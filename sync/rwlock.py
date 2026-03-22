"""
读写锁 (Read-Write Lock) - 优化读多写少场景的同步机制

==========================================
        读写锁深入学习教程
==========================================

🎯 什么是读写锁？
----------------
读写锁是一种特殊的锁机制，区分读操作和写操作：
- 读锁（共享锁）：允许多个读者同时访问
- 写锁（排他锁）：只允许一个写者访问，且排斥所有读者

📚 读写锁的状态
---------------
1. 空闲：没有任何读者或写者
2. 读锁定：有一个或多个读者持有锁
3. 写锁定：有一个写者持有锁

🔧 锁的兼容性
-------------
         | 读请求 | 写请求
---------|--------|-------
读锁定   |   ✅   |   ❌
写锁定   |   ❌   |   ❌

💡 应用场景
-----------
- 读多写少的数据结构（缓存、配置）
- 数据库读操作远多于写操作
- 文件系统的读操作

⚠️ 读写锁的策略
---------------
1. 读者优先 (Reader Preference)
   - 只要有读者，新读者可以直接进入
   - 可能导致写者饥饿

2. 写者优先 (Writer Preference)
   - 有写者等待时，新读者必须等待
   - 可能导致读者饥饿

3. 公平策略 (Fair)
   - 按请求顺序分配锁
   - 避免饥饿，但可能降低吞吐量
"""

import threading
import time
from typing import Optional
from enum import Enum
from collections import deque
from utils.logger import Logger


class RWLockPolicy(Enum):
    """读写锁策略"""
    READER_PREFERENCE = "reader_preference"  # 读者优先
    WRITER_PREFERENCE = "writer_preference"  # 写者优先
    FAIR = "fair"                            # 公平策略


class ReadWriteLock:
    """
    读写锁实现

    支持三种策略：读者优先、写者优先、公平策略
    """

    def __init__(self, name: str = "", policy: RWLockPolicy = RWLockPolicy.FAIR):
        """
        初始化读写锁

        Args:
            name: 锁的名称
            policy: 锁的策略
        """
        self._name = name or f"rwlock_{id(self)}"
        self._policy = policy
        self._lock = threading.Lock()

        # 状态
        self._readers = 0          # 当前读者数量
        self._writers = 0          # 当前写者数量（最多为1）
        self._writer_waiting = 0   # 等待的写者数量

        # 等待队列（用于公平策略）
        self._wait_queue: deque = deque()
        self._next_id = 0

        self._logger = Logger()

        # 统计
        self._read_acquire_count = 0
        self._read_release_count = 0
        self._write_acquire_count = 0
        self._write_release_count = 0

        self._logger.info(f"读写锁 '{self._name}' 创建，策略: {policy.value}")

    def acquire_read(self, timeout: Optional[float] = None) -> bool:
        """
        获取读锁

        根据策略决定是否可以立即获取或需要等待

        Args:
            timeout: 超时时间

        Returns:
            bool: 是否成功获取
        """
        start_time = time.time()

        with self._lock:
            can_acquire = self._can_acquire_read()

            if can_acquire:
                self._readers += 1
                self._read_acquire_count += 1
                self._logger.debug(f"获取读锁 '{self._name}'，读者数: {self._readers}")
                return True

            # 需要等待
            if self._policy == RWLockPolicy.FAIR:
                # 公平策略：加入等待队列
                event = threading.Event()
                request_id = self._next_id
                self._next_id += 1
                self._wait_queue.append(('read', event, request_id))

                # 在锁外等待
                self._lock.release()
                success = event.wait(timeout=timeout)
                self._lock.acquire()

                if not success:
                    # 超时，从队列移除
                    self._wait_queue = deque(
                        item for item in self._wait_queue
                        if item[2] != request_id
                    )
                return success
            else:
                # 读者优先或写者优先：创建等待事件
                event = threading.Event()

        # 在锁外等待（非公平策略）
        while True:
            with self._lock:
                if self._can_acquire_read():
                    self._readers += 1
                    self._read_acquire_count += 1
                    return True

                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        return False
                    remaining = timeout - elapsed
                else:
                    remaining = 0.1

            time.sleep(min(0.01, remaining if timeout else 0.01))

    def release_read(self) -> None:
        """释放读锁"""
        with self._lock:
            if self._readers <= 0:
                raise RuntimeError("没有读锁可以释放")

            self._readers -= 1
            self._read_release_count += 1
            self._logger.debug(f"释放读锁 '{self._name}'，读者数: {self._readers}")

            # 如果没有读者了，唤醒等待的写者
            if self._readers == 0:
                self._wake_waiters()

    def acquire_write(self, timeout: Optional[float] = None) -> bool:
        """
        获取写锁

        只有在没有读者和写者时才能获取

        Args:
            timeout: 超时时间

        Returns:
            bool: 是否成功获取
        """
        start_time = time.time()

        with self._lock:
            can_acquire = self._can_acquire_write()

            if can_acquire:
                self._writers += 1
                self._write_acquire_count += 1
                self._logger.debug(f"获取写锁 '{self._name}'")
                return True

            # 需要等待
            self._writer_waiting += 1

            if self._policy == RWLockPolicy.FAIR:
                event = threading.Event()
                request_id = self._next_id
                self._next_id += 1
                self._wait_queue.append(('write', event, request_id))

                self._lock.release()
                success = event.wait(timeout=timeout)
                self._lock.acquire()

                if not success:
                    self._writer_waiting -= 1
                    self._wait_queue = deque(
                        item for item in self._wait_queue
                        if item[2] != request_id
                    )
                return success

        # 非公平策略的等待循环
        while True:
            with self._lock:
                if self._can_acquire_write():
                    self._writers += 1
                    self._writer_waiting -= 1
                    self._write_acquire_count += 1
                    return True

                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        with self._lock:
                            self._writer_waiting -= 1
                        return False

            time.sleep(0.01)

    def release_write(self) -> None:
        """释放写锁"""
        with self._lock:
            if self._writers <= 0:
                raise RuntimeError("没有写锁可以释放")

            self._writers -= 1
            self._write_release_count += 1
            self._logger.debug(f"释放写锁 '{self._name}'")

            # 唤醒等待者
            self._wake_waiters()

    def _can_acquire_read(self) -> bool:
        """检查是否可以获取读锁"""
        if self._writers > 0:
            return False

        if self._policy == RWLockPolicy.WRITER_PREFERENCE and self._writer_waiting > 0:
            return False

        return True

    def _can_acquire_write(self) -> bool:
        """检查是否可以获取写锁"""
        return self._readers == 0 and self._writers == 0

    def _wake_waiters(self) -> None:
        """唤醒等待者"""
        if self._policy != RWLockPolicy.FAIR:
            return

        if not self._wait_queue:
            return

        # 唤醒队列头部的请求
        if self._wait_queue:
            req_type, event, _ = self._wait_queue[0]

            if req_type == 'write' and self._can_acquire_write():
                self._wait_queue.popleft()
                self._writers += 1
                self._writer_waiting -= 1
                event.set()
            elif req_type == 'read':
                # 唤醒所有连续的读请求
                while self._wait_queue and self._wait_queue[0][0] == 'read':
                    _, event, _ = self._wait_queue.popleft()
                    self._readers += 1
                    event.set()

    @property
    def reader_count(self) -> int:
        """获取当前读者数量"""
        with self._lock:
            return self._readers

    @property
    def writer_count(self) -> int:
        """获取当前写者数量"""
        with self._lock:
            return self._writers

    @property
    def is_write_locked(self) -> bool:
        """是否有写者持有锁"""
        return self.writer_count > 0

    @property
    def is_read_locked(self) -> bool:
        """是否有读者持有锁"""
        return self.reader_count > 0

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            return {
                'name': self._name,
                'policy': self._policy.value,
                'readers': self._readers,
                'writers': self._writers,
                'writer_waiting': self._writer_waiting,
                'read_acquire_count': self._read_acquire_count,
                'write_acquire_count': self._write_acquire_count
            }

    # 上下文管理器支持
    class ReadGuard:
        """读锁守卫"""
        def __init__(self, rwlock):
            self._rwlock = rwlock

        def __enter__(self):
            self._rwlock.acquire_read()
            return self

        def __exit__(self, *args):
            self._rwlock.release_read()
            return False

    class WriteGuard:
        """写锁守卫"""
        def __init__(self, rwlock):
            self._rwlock = rwlock

        def __enter__(self):
            self._rwlock.acquire_write()
            return self

        def __exit__(self, *args):
            self._rwlock.release_write()
            return False

    def read_lock(self):
        """返回读锁上下文管理器"""
        return self.ReadGuard(self)

    def write_lock(self):
        """返回写锁上下文管理器"""
        return self.WriteGuard(self)

    def __str__(self) -> str:
        return (f"ReadWriteLock(name='{self._name}', "
                f"readers={self.reader_count}, writers={self.writer_count})")


# 使用示例
if __name__ == "__main__":
    print("=== 读写锁使用示例 ===\n")

    rwlock = ReadWriteLock(name="cache_lock", policy=RWLockPolicy.FAIR)
    shared_data = {"value": 0}

    def reader(rid):
        for _ in range(3):
            with rwlock.read_lock():
                print(f"  读者{rid}: 读取值 = {shared_data['value']}")
                time.sleep(0.1)

    def writer(wid):
        for i in range(2):
            with rwlock.write_lock():
                shared_data['value'] += 1
                print(f"  写者{wid}: 写入值 = {shared_data['value']}")
                time.sleep(0.2)

    # 创建多个读者和写者
    readers = [threading.Thread(target=reader, args=(i,)) for i in range(3)]
    writers = [threading.Thread(target=writer, args=(i,)) for i in range(2)]

    for t in readers + writers:
        t.start()
    for t in readers + writers:
        t.join()

    print(f"\n统计: {rwlock.get_stats()}")
