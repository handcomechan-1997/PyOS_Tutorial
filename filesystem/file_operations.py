"""
文件操作模块 - 实现基本的文件操作
"""

import threading
import time
from typing import Dict, List, Optional, Tuple, BinaryIO
from enum import Enum

from .inode import Inode, FileType
from utils.logger import Logger

class OpenMode(Enum):
    """文件打开模式"""
    READ = "r"
    WRITE = "w"
    APPEND = "a"
    READ_WRITE = "r+"
    WRITE_READ = "w+"
    APPEND_READ = "a+"

class FileDescriptor:
    """文件描述符"""
    
    def __init__(self, fd: int, file_path: str, mode: OpenMode):
        self.fd = fd
        self.file_path = file_path
        self.mode = mode
        self.position = 0  # 文件指针位置
        self.inode = None
        self.opened_time = time.time()
        self.last_access_time = time.time()
        self.is_open = True

class FileOperations:
    """文件操作类"""
    
    def __init__(self):
        """初始化文件操作"""
        self.logger = Logger()
        self.open_files: Dict[int, FileDescriptor] = {}
        self.next_fd = 1
        self.lock = threading.Lock()
        
        # 文件系统引用
        self.file_system = None
        self.inode_table = None
    
    def initialize(self, file_system, inode_table):
        """初始化文件操作"""
        self.file_system = file_system
        self.inode_table = inode_table
        self.logger.info("文件操作初始化完成")
    
    def open_file(self, path: str, mode: str = "r") -> int:
        """打开文件"""
        with self.lock:
            try:
                # 解析模式
                open_mode = self._parse_mode(mode)
                if not open_mode:
                    self.logger.error(f"无效的文件打开模式: {mode}")
                    return -1
                
                # 检查文件是否存在
                if open_mode in [OpenMode.READ, OpenMode.READ_WRITE, OpenMode.APPEND_READ]:
                    if not self._file_exists(path):
                        self.logger.error(f"文件不存在: {path}")
                        return -1
                
                # 创建文件描述符
                fd = self.next_fd
                self.next_fd += 1
                
                file_descriptor = FileDescriptor(fd, path, open_mode)
                self.open_files[fd] = file_descriptor
                
                # 获取或创建inode
                inode = self._get_or_create_inode(path, open_mode)
                if inode:
                    file_descriptor.inode = inode
                
                self.logger.log_file_event(f"打开文件: {path}, 模式: {mode}, 描述符: {fd}")
                return fd
                
            except Exception as e:
                self.logger.error(f"打开文件失败: {path} - {e}")
                return -1
    
    def close_file(self, fd: int) -> bool:
        """关闭文件"""
        with self.lock:
            if fd not in self.open_files:
                self.logger.warning(f"文件描述符不存在: {fd}")
                return False
            
            file_descriptor = self.open_files[fd]
            file_descriptor.is_open = False
            
            # 更新inode访问时间
            if file_descriptor.inode:
                file_descriptor.inode.update_access_time()
            
            del self.open_files[fd]
            
            self.logger.log_file_event(f"关闭文件: 描述符 {fd}")
            return True
    
    def read_file(self, fd: int, size: int) -> str:
        """读取文件"""
        with self.lock:
            if fd not in self.open_files:
                self.logger.error(f"文件描述符不存在: {fd}")
                return ""
            
            file_descriptor = self.open_files[fd]
            if not file_descriptor.is_open:
                self.logger.error(f"文件描述符已关闭: {fd}")
                return ""
            
            if file_descriptor.mode not in [OpenMode.READ, OpenMode.READ_WRITE, OpenMode.APPEND_READ]:
                self.logger.error(f"文件未以读模式打开: {fd}")
                return ""
            
            # TODO: 实现文件读取
            # 1. 检查文件指针位置
            # 2. 从inode获取数据块
            # 3. 读取数据
            # 4. 更新文件指针
            
            content = self._read_from_inode(file_descriptor.inode, file_descriptor.position, size)
            if content:
                file_descriptor.position += len(content)
                file_descriptor.last_access_time = time.time()
                file_descriptor.inode.update_access_time()
            
            self.logger.log_file_event(f"读取文件: 描述符 {fd}, 大小 {size}, 实际读取 {len(content)}")
            return content
    
    def write_file(self, fd: int, data: str) -> int:
        """写入文件"""
        with self.lock:
            if fd not in self.open_files:
                self.logger.error(f"文件描述符不存在: {fd}")
                return -1
            
            file_descriptor = self.open_files[fd]
            if not file_descriptor.is_open:
                self.logger.error(f"文件描述符已关闭: {fd}")
                return -1
            
            if file_descriptor.mode not in [OpenMode.WRITE, OpenMode.APPEND, OpenMode.READ_WRITE, OpenMode.WRITE_READ, OpenMode.APPEND_READ]:
                self.logger.error(f"文件未以写模式打开: {fd}")
                return -1
            
            # TODO: 实现文件写入
            # 1. 检查文件指针位置
            # 2. 分配数据块
            # 3. 写入数据
            # 4. 更新inode
            # 5. 更新文件指针
            
            written_size = self._write_to_inode(file_descriptor.inode, file_descriptor.position, data)
            if written_size > 0:
                file_descriptor.position += written_size
                file_descriptor.last_access_time = time.time()
                file_descriptor.inode.update_modification_time()
            
            self.logger.log_file_event(f"写入文件: 描述符 {fd}, 数据长度 {len(data)}, 实际写入 {written_size}")
            return written_size
    
    def seek_file(self, fd: int, offset: int, whence: int = 0) -> int:
        """文件指针定位"""
        with self.lock:
            if fd not in self.open_files:
                self.logger.error(f"文件描述符不存在: {fd}")
                return -1
            
            file_descriptor = self.open_files[fd]
            if not file_descriptor.is_open:
                self.logger.error(f"文件描述符已关闭: {fd}")
                return -1
            
            # 计算新的位置
            if whence == 0:  # SEEK_SET
                new_position = offset
            elif whence == 1:  # SEEK_CUR
                new_position = file_descriptor.position + offset
            elif whence == 2:  # SEEK_END
                new_position = file_descriptor.inode.get_size() + offset if file_descriptor.inode else offset
            else:
                self.logger.error(f"无效的whence值: {whence}")
                return -1
            
            # 检查边界
            if new_position < 0:
                new_position = 0
            
            file_descriptor.position = new_position
            self.logger.log_file_event(f"文件指针定位: 描述符 {fd}, 位置 {new_position}")
            return new_position
    
    def truncate_file(self, fd: int, size: int) -> bool:
        """截断文件"""
        with self.lock:
            if fd not in self.open_files:
                self.logger.error(f"文件描述符不存在: {fd}")
                return False
            
            file_descriptor = self.open_files[fd]
            if not file_descriptor.is_open:
                self.logger.error(f"文件描述符已关闭: {fd}")
                return False
            
            if not file_descriptor.inode:
                self.logger.error(f"文件inode不存在: {fd}")
                return False
            
            # TODO: 实现文件截断
            # 1. 调整文件大小
            # 2. 释放多余的数据块
            # 3. 更新inode
            
            old_size = file_descriptor.inode.get_size()
            file_descriptor.inode.set_size(size)
            file_descriptor.inode.update_modification_time()
            
            self.logger.log_file_event(f"截断文件: 描述符 {fd}, 大小 {old_size} -> {size}")
            return True
    
    def _parse_mode(self, mode: str) -> Optional[OpenMode]:
        """解析文件打开模式"""
        mode_map = {
            'r': OpenMode.READ,
            'w': OpenMode.WRITE,
            'a': OpenMode.APPEND,
            'r+': OpenMode.READ_WRITE,
            'w+': OpenMode.WRITE_READ,
            'a+': OpenMode.APPEND_READ
        }
        return mode_map.get(mode)
    
    def _file_exists(self, path: str) -> bool:
        """检查文件是否存在"""
        # TODO: 实现文件存在检查
        # 1. 解析路径
        # 2. 查找inode
        # 3. 返回是否存在
        return True  # 临时实现
    
    def _get_or_create_inode(self, path: str, mode: OpenMode) -> Optional[Inode]:
        """获取或创建inode"""
        # TODO: 实现inode获取或创建
        # 1. 查找现有inode
        # 2. 如果不存在且为写模式，创建新inode
        # 3. 返回inode
        return None  # 临时实现
    
    def _read_from_inode(self, inode: Inode, position: int, size: int) -> str:
        """从inode读取数据"""
        # TODO: 实现从inode读取数据
        # 1. 计算数据块位置
        # 2. 读取数据块
        # 3. 返回数据
        return ""  # 临时实现
    
    def _write_to_inode(self, inode: Inode, position: int, data: str) -> int:
        """向inode写入数据"""
        # TODO: 实现向inode写入数据
        # 1. 计算数据块位置
        # 2. 分配数据块
        # 3. 写入数据
        # 4. 更新inode
        return len(data)  # 临时实现
    
    def get_open_files(self) -> List[FileDescriptor]:
        """获取所有打开的文件"""
        with self.lock:
            return list(self.open_files.values())
    
    def get_file_descriptor(self, fd: int) -> Optional[FileDescriptor]:
        """获取文件描述符"""
        with self.lock:
            return self.open_files.get(fd)
    
    def print_open_files(self):
        """打印打开的文件"""
        with self.lock:
            print(f"\n打开的文件 (共 {len(self.open_files)} 个):")
            print("-" * 80)
            print(f"{'描述符':<8} {'路径':<30} {'模式':<8} {'位置':<8} {'大小':<8}")
            print("-" * 80)
            
            for fd, file_desc in self.open_files.items():
                size = file_desc.inode.get_size() if file_desc.inode else 0
                print(f"{fd:<8} {file_desc.file_path:<30} {file_desc.mode.value:<8} "
                      f"{file_desc.position:<8} {size:<8}")
            
            print("-" * 80)
    
    def cleanup(self):
        """清理文件操作"""
        with self.lock:
            # 关闭所有打开的文件
            for fd in list(self.open_files.keys()):
                self.close_file(fd)
            self.logger.info("文件操作清理完成") 