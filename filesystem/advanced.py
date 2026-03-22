"""
文件系统高级特性 - 软硬链接、文件锁

本模块实现：
1. 硬链接 (Hard Link)
2. 软链接 (Symbolic/Soft Link)
3. 文件锁 (Advisory Lock)
"""

import time
from typing import Optional, Dict, List, Set
from enum import Enum
from collections import defaultdict
import threading
from utils.logger import Logger


class LinkType(Enum):
    """链接类型"""
    HARD = "hard"
    SYMBOLIC = "symbolic"


class LockType(Enum):
    """锁类型"""
    SHARED = "shared"     # 共享锁（读锁）
    EXCLUSIVE = "exclusive"  # 排他锁（写锁")


class Inode:
    """
    索引节点

    存储文件的元数据。
    """

    _next_ino = 1

    def __init__(self, file_type: str = "regular"):
        """
        初始化Inode

        Args:
            file_type: 文件类型 (regular, directory, symlink)
        """
        self.ino = Inode._next_ino
        Inode._next_ino += 1
        self.file_type = file_type
        self.mode = 0o644
        self.uid = 0
        self.gid = 0
        self.size = 0
        self.blocks = 0
        self.link_count = 1  # 硬链接计数
        self.atime = time.time()
        self.mtime = time.time()
        self.ctime = time.time()
        self.data = ""

    def inc_link(self) -> None:
        """增加链接计数"""
        self.link_count += 1
        self.ctime = time.time()

    def dec_link(self) -> int:
        """减少链接计数"""
        self.link_count -= 1
        self.ctime = time.time()
        return self.link_count


class Link:
    """
    链接基类
    """

    def __init__(self, source_path: str, target_ino: int, link_type: LinkType):
        """
        初始化链接

        Args:
            source_path: 链接文件路径
            target_ino: 目标Inode号
            link_type: 链接类型
        """
        self.source_path = source_path
        self.target_ino = target_ino
        self.link_type = link_type
        self.created_time = time.time()


class HardLink(Link):
    """
    硬链接

    硬链接是文件的另一个名称，指向同一个Inode。
    删除原文件不会影响硬链接。
    """

    def __init__(self, source_path: str, target_ino: int):
        super().__init__(source_path, target_ino, LinkType.HARD)


class SymbolicLink(Link):
    """
    软链接（符号链接）

    软链接是一个特殊文件，包含目标文件的路径。
    目标文件被删除后，软链接变成悬空链接。
    """

    def __init__(self, source_path: str, target_path: str, target_ino: int = None):
        super().__init__(source_path, target_ino, LinkType.SYMBOLIC)
        self.target_path = target_path
        self.is_dangling = target_ino is None


class FileLock:
    """
    文件锁

    实现建议性锁（Advisory Lock）。
    """

    def __init__(self, ino: int):
        """
        初始化文件锁

        Args:
            ino: Inode号
        """
        self._ino = ino
        self._lock = threading.Lock()
        self._shared_count = 0
        self._exclusive_holder: Optional[int] = None
        self._shared_holders: Set[int] = set()
        self._waiting: List[tuple] = []  # (pid, lock_type, event)
        self._logger = Logger()

    def acquire(self, pid: int, lock_type: LockType, timeout: float = None) -> bool:
        """
        获取锁

        Args:
            pid: 进程ID
            lock_type: 锁类型
            timeout: 超时时间

        Returns:
            bool: 是否成功
        """
        import time
        start = time.time()

        while True:
            with self._lock:
                if lock_type == LockType.SHARED:
                    # 共享锁：没有排他锁时可以获取
                    if self._exclusive_holder is None:
                        self._shared_count += 1
                        self._shared_holders.add(pid)
                        self._logger.debug(f"进程 {pid} 获取共享锁，Inode {self._ino}")
                        return True
                else:
                    # 排他锁：没有任何锁时可以获取
                    if self._exclusive_holder is None and self._shared_count == 0:
                        self._exclusive_holder = pid
                        self._logger.debug(f"进程 {pid} 获取排他锁，Inode {self._ino}")
                        return True

            # 需要等待
            if timeout is not None:
                elapsed = time.time() - start
                if elapsed >= timeout:
                    return False
            time.sleep(0.01)

    def release(self, pid: int) -> None:
        """
        释放锁

        Args:
            pid: 进程ID
        """
        with self._lock:
            if self._exclusive_holder == pid:
                self._exclusive_holder = None
                self._logger.debug(f"进程 {pid} 释放排他锁，Inode {self._ino}")
            elif pid in self._shared_holders:
                self._shared_holders.remove(pid)
                self._shared_count -= 1
                self._logger.debug(f"进程 {pid} 释放共享锁，Inode {self._ino}")

    def is_locked(self) -> bool:
        """检查是否被锁"""
        with self._lock:
            return self._exclusive_holder is not None or self._shared_count > 0

    def get_lock_info(self) -> dict:
        """获取锁信息"""
        with self._lock:
            return {
                'ino': self._ino,
                'exclusive_holder': self._exclusive_holder,
                'shared_count': self._shared_count,
                'shared_holders': list(self._shared_holders)
            }


class AdvancedFileSystem:
    """
    高级文件系统

    支持软硬链接和文件锁。
    """

    def __init__(self):
        """初始化高级文件系统"""
        self._inodes: Dict[int, Inode] = {}
        self._path_to_ino: Dict[str, int] = {}
        self._links: Dict[str, Link] = {}  # source_path -> Link
        self._locks: Dict[int, FileLock] = {}  # ino -> FileLock
        self._lock = threading.Lock()
        self._logger = Logger()

    def create_file(self, path: str, content: str = "") -> int:
        """
        创建文件

        Args:
            path: 文件路径
            content: 文件内容

        Returns:
            int: Inode号
        """
        with self._lock:
            inode = Inode()
            inode.data = content
            inode.size = len(content)

            self._inodes[inode.ino] = inode
            self._path_to_ino[path] = inode.ino

            self._logger.debug(f"创建文件: {path}, Inode: {inode.ino}")
            return inode.ino

    def create_hard_link(self, source_path: str, target_path: str) -> bool:
        """
        创建硬链接

        Args:
            source_path: 链接文件路径
            target_path: 目标文件路径

        Returns:
            bool: 是否成功
        """
        with self._lock:
            target_ino = self._path_to_ino.get(target_path)
            if target_ino is None:
                self._logger.error(f"目标文件不存在: {target_path}")
                return False

            inode = self._inodes.get(target_ino)
            if inode.file_type != "regular":
                self._logger.error("只能对普通文件创建硬链接")
                return False

            # 创建硬链接
            link = HardLink(source_path, target_ino)
            self._links[source_path] = link
            self._path_to_ino[source_path] = target_ino
            inode.inc_link()

            self._logger.info(f"创建硬链接: {source_path} -> {target_path}")
            return True

    def create_symbolic_link(self, source_path: str, target_path: str) -> bool:
        """
        创建软链接

        Args:
            source_path: 链接文件路径
            target_path: 目标路径（可以是相对或绝对路径）

        Returns:
            bool: 是否成功
        """
        with self._lock:
            target_ino = self._path_to_ino.get(target_path)

            # 创建软链接Inode
            inode = Inode(file_type="symlink")
            inode.data = target_path
            inode.size = len(target_path)
            inode.link_count = 1

            self._inodes[inode.ino] = inode
            self._path_to_ino[source_path] = inode.ino

            # 创建软链接
            link = SymbolicLink(source_path, target_path, target_ino)
            self._links[source_path] = link

            self._logger.info(f"创建软链接: {source_path} -> {target_path}")
            return True

    def read_file(self, path: str) -> Optional[str]:
        """
        读取文件

        自动解析软链接。

        Args:
            path: 文件路径

        Returns:
            Optional[str]: 文件内容
        """
        with self._lock:
            ino = self._path_to_ino.get(path)
            if ino is None:
                # 检查是否是软链接
                link = self._links.get(path)
                if link and link.link_type == LinkType.SYMBOLIC:
                    slink: SymbolicLink = link
                    if slink.is_dangling:
                        self._logger.error(f"悬空软链接: {path}")
                        return None
                    ino = slink.target_ino
                else:
                    return None

            inode = self._inodes.get(ino)
            if inode:
                inode.atime = time.time()
                return inode.data
            return None

    def write_file(self, path: str, content: str) -> bool:
        """
        写入文件

        Args:
            path: 文件路径
            content: 内容

        Returns:
            bool: 是否成功
        """
        with self._lock:
            ino = self._path_to_ino.get(path)
            if ino is None:
                return False

            inode = self._inodes.get(ino)
            if inode:
                inode.data = content
                inode.size = len(content)
                inode.mtime = time.time()
                return True
            return False

    def delete_file(self, path: str) -> bool:
        """
        删除文件

        Args:
            path: 文件路径

        Returns:
            bool: 是否成功
        """
        with self._lock:
            ino = self._path_to_ino.get(path)
            if ino is None:
                return False

            inode = self._inodes.get(ino)
            if inode is None:
                return False

            # 减少链接计数
            remaining = inode.dec_link()

            # 如果是软链接，直接删除
            if path in self._links:
                del self._links[path]

            # 从路径映射中移除
            del self._path_to_ino[path]

            # 如果链接计数为0，删除Inode
            if remaining == 0:
                del self._inodes[ino]
                if ino in self._locks:
                    del self._locks[ino]

            self._logger.debug(f"删除文件: {path}")
            return True

    def lock_file(self, path: str, pid: int, lock_type: LockType,
                  timeout: float = None) -> bool:
        """
        锁定文件

        Args:
            path: 文件路径
            pid: 进程ID
            lock_type: 锁类型
            timeout: 超时时间

        Returns:
            bool: 是否成功
        """
        ino = self._path_to_ino.get(path)
        if ino is None:
            return False

        if ino not in self._locks:
            self._locks[ino] = FileLock(ino)

        return self._locks[ino].acquire(pid, lock_type, timeout)

    def unlock_file(self, path: str, pid: int) -> None:
        """
        解锁文件

        Args:
            path: 文件路径
            pid: 进程ID
        """
        ino = self._path_to_ino.get(path)
        if ino and ino in self._locks:
            self._locks[ino].release(pid)

    def get_file_info(self, path: str) -> Optional[dict]:
        """获取文件信息"""
        with self._lock:
            ino = self._path_to_ino.get(path)
            if ino is None:
                return None

            inode = self._inodes.get(ino)
            if inode is None:
                return None

            info = {
                'path': path,
                'ino': inode.ino,
                'type': inode.file_type,
                'size': inode.size,
                'link_count': inode.link_count,
                'mode': oct(inode.mode),
                'mtime': inode.mtime
            }

            # 检查链接
            if path in self._links:
                link = self._links[path]
                info['link_type'] = link.link_type.value
                if link.link_type == LinkType.SYMBOLIC:
                    info['target_path'] = link.target_path

            # 检查锁
            if inode.ino in self._locks:
                info['lock_info'] = self._locks[inode.ino].get_lock_info()

            return info

    def list_links(self) -> List[dict]:
        """列出所有链接"""
        with self._lock:
            result = []
            for path, link in self._links.items():
                info = {
                    'source': path,
                    'type': link.link_type.value,
                    'target_ino': link.target_ino
                }
                if link.link_type == LinkType.SYMBOLIC:
                    info['target_path'] = link.target_path
                result.append(info)
            return result


# 使用示例
if __name__ == "__main__":
    print("=== 文件系统高级特性演示 ===\n")

    fs = AdvancedFileSystem()

    # 1. 创建文件
    print("1. 创建文件")
    fs.create_file("/original.txt", "Hello, World!")
    print(f"  创建: /original.txt")

    # 2. 创建硬链接
    print("\n2. 创建硬链接")
    fs.create_hard_link("/hardlink.txt", "/original.txt")
    print(f"  创建硬链接: /hardlink.txt -> /original.txt")

    # 3. 创建软链接
    print("\n3. 创建软链接")
    fs.create_symbolic_link("/symlink.txt", "/original.txt")
    print(f"  创建软链接: /symlink.txt -> /original.txt")

    # 4. 读取文件（通过不同路径）
    print("\n4. 通过不同路径读取")
    print(f"  原文件: {fs.read_file('/original.txt')}")
    print(f"  硬链接: {fs.read_file('/hardlink.txt')}")
    print(f"  软链接: {fs.read_file('/symlink.txt')}")

    # 5. 查看链接信息
    print("\n5. 链接信息")
    for link in fs.list_links():
        print(f"  {link}")

    # 6. 文件锁
    print("\n6. 文件锁")
    fs.lock_file("/original.txt", pid=1, lock_type=LockType.EXCLUSIVE)
    print(f"  进程1获取排他锁")

    # 尝试获取共享锁（应该失败）
    success = fs.lock_file("/original.txt", pid=2, lock_type=LockType.SHARED, timeout=0.5)
    print(f"  进程2尝试获取共享锁: {'成功' if success else '失败（被阻塞）'}")

    # 释放锁
    fs.unlock_file("/original.txt", pid=1)
    print(f"  进程1释放锁")

    # 再次尝试
    success = fs.lock_file("/original.txt", pid=2, lock_type=LockType.SHARED, timeout=0.5)
    print(f"  进程2再次尝试获取共享锁: {'成功' if success else '失败'}")

    # 7. 删除原文件
    print("\n7. 删除原文件")
    fs.delete_file("/original.txt")
    print(f"  硬链接读取: {fs.read_file('/hardlink.txt')}")  # 仍然可以读取
    print(f"  软链接读取: {fs.read_file('/symlink.txt')}")  # 悬空链接

    print("\n演示完成！")
