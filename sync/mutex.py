"""
互斥锁 (Mutex) - 互斥访问的同步机制

==========================================
         互斥锁深入学习教程
==========================================

🎯 什么是互斥锁？
----------------
互斥锁 (Mutual Exclusion) 是一种用于保护临界区的同步原语。
同一时刻只允许一个线程/进程持有锁，从而保证临界区的互斥访问。

📚 互斥锁 vs 二进制信号量
-------------------------
虽然两者都能实现互斥，但有重要区别：

| 特性           | 互斥锁         | 二进制信号量    |
|----------------|----------------|-----------------|
| 所有权         | 有             | 无              |
| 谁能释放       | 只有持有者     | 任何线程        |
| 递归锁定       | 可支持         | 不支持          |
| 优先级继承     | 可支持         | 一般不支持      |
| 语义           | 保护资源       | 信号通知        |

🔧 互斥锁的状态
---------------
- 未锁定 (unlocked): 可以被获取
- 已锁定 (locked): 被某个线程持有

💡 使用原则
-----------
1. 进入临界区前必须获取锁
2. 离开临界区后必须释放锁
3. 锁的持有时间应尽可能短
4. 避免在持有锁时调用可能阻塞的函数

⚠️ 常见问题
-----------
- 忘记释放锁 -> 死锁
- 重复获取锁 -> 死锁（除非使用递归锁）
- 锁的粒度过大 -> 性能下降
- 锁的粒度过小 -> 保护不足
"""

import threading
import time
from typing import Optional
from utils.logger import Logger


class Mutex:
    """
    互斥锁实现

    提供基本的互斥访问控制，确保同一时刻只有一个线程能进入临界区。
    支持超时获取、所有权检查等特性。
    """

    def __init__(self, name: str = ""):
        """
        初始化互斥锁

        Args:
            name: 锁的名称，用于调试和日志
        """
        self._name = name or f"mutex_{id(self)}"
        self._lock = threading.Lock()
        self._owner: Optional[int] = None  # 持有者线程ID
        self._lock_count = 0  # 锁定次数（用于递归锁）
        self._logger = Logger()

        # 统计信息
        self._acquire_count = 0
        self._release_count = 0
        self._contention_count = 0  # 竞争次数
        self._total_wait_time = 0.0

        self._logger.info(f"互斥锁 '{self._name}' 创建")

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        获取锁

        如果锁未被持有，立即获取并返回True
        如果锁已被持有，阻塞等待直到获取或超时

        Args:
            timeout: 超时时间（秒），None表示无限等待

        Returns:
            bool: 是否成功获取锁
        """
        current_thread = threading.current_thread()
        thread_id = current_thread.ident

        # 检查是否已经持有锁（非递归锁不允许）
        if self._owner == thread_id:
            self._logger.warning(f"线程 {thread_id} 尝试重复获取非递归锁 '{self._name}'")
            raise RuntimeError(f"检测到死锁：线程 {thread_id} 尝试重复获取非递归锁")

        start_time = time.time()
        self._acquire_count += 1

        # 检查是否有竞争
        if self._owner is not None:
            self._contention_count += 1
            self._logger.debug(f"锁 '{self._name}' 存在竞争，线程 {thread_id} 等待")

        # 尝试获取锁
        acquired = self._lock.acquire(timeout=timeout)

        if acquired:
            self._owner = thread_id
            wait_time = time.time() - start_time
            self._total_wait_time += wait_time
            self._logger.debug(f"线程 {thread_id} 获取锁 '{self._name}'，等待时间: {wait_time:.3f}s")
        else:
            self._logger.debug(f"线程 {thread_id} 获取锁 '{self._name}' 超时")

        return acquired

    def release(self) -> None:
        """
        释放锁

        只有锁的持有者才能释放锁
        """
        current_thread = threading.current_thread()
        thread_id = current_thread.ident

        if self._owner != thread_id:
            self._logger.error(f"线程 {thread_id} 尝试释放不属于自己的锁 '{self._name}'")
            raise RuntimeError(f"线程 {thread_id} 不是锁 '{self._name}' 的持有者")

        self._owner = None
        self._release_count += 1
        self._lock.release()
        self._logger.debug(f"线程 {thread_id} 释放锁 '{self._name}'")

    def locked(self) -> bool:
        """检查锁是否被持有"""
        return self._owner is not None

    @property
    def owner(self) -> Optional[int]:
        """获取当前持有者的线程ID"""
        return self._owner

    def get_stats(self) -> dict:
        """获取统计信息"""
        avg_wait = self._total_wait_time / self._acquire_count if self._acquire_count > 0 else 0
        return {
            'name': self._name,
            'locked': self.locked(),
            'owner': self._owner,
            'acquire_count': self._acquire_count,
            'release_count': self._release_count,
            'contention_count': self._contention_count,
            'average_wait_time': avg_wait
        }

    def __enter__(self):
        """支持 with 语句"""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持 with 语句"""
        self.release()
        return False

    def __str__(self) -> str:
        status = "locked" if self.locked() else "unlocked"
        owner = f", owner={self._owner}" if self._owner else ""
        return f"Mutex(name='{self._name}', status={status}{owner})"


class RecursiveMutex:
    """
    递归互斥锁 (可重入锁)

    允许同一个线程多次获取同一个锁，但必须释放相同次数。
    适用于递归调用或嵌套临界区的场景。

    示例：
        lock = RecursiveMutex()

        def outer():
            with lock:
                print("外层临界区")
                inner()  # 内部也需要锁

        def inner():
            with lock:  # 同一线程可以再次获取
                print("内层临界区")
    """

    def __init__(self, name: str = ""):
        """
        初始化递归互斥锁

        Args:
            name: 锁的名称
        """
        self._name = name or f"recursive_mutex_{id(self)}"
        self._lock = threading.RLock()
        self._owner: Optional[int] = None
        self._lock_count = 0  # 递归计数
        self._logger = Logger()

        # 统计信息
        self._acquire_count = 0
        self._release_count = 0
        self._total_wait_time = 0.0

        self._logger.info(f"递归互斥锁 '{self._name}' 创建")

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        获取锁

        如果当前线程已持有锁，增加递归计数
        否则等待获取锁
        """
        current_thread = threading.current_thread()
        thread_id = current_thread.ident
        start_time = time.time()

        acquired = self._lock.acquire(timeout=timeout)

        if acquired:
            if self._owner is None:
                self._owner = thread_id
            self._lock_count += 1
            self._acquire_count += 1
            wait_time = time.time() - start_time
            self._total_wait_time += wait_time
            self._logger.debug(f"线程 {thread_id} 获取递归锁 '{self._name}'，"
                               f"递归深度: {self._lock_count}")

        return acquired

    def release(self) -> None:
        """
        释放锁

        减少递归计数，当计数为0时真正释放锁
        """
        current_thread = threading.current_thread()
        thread_id = current_thread.ident

        if self._owner != thread_id:
            self._logger.error(f"线程 {thread_id} 尝试释放不属于自己的递归锁 '{self._name}'")
            raise RuntimeError(f"线程 {thread_id} 不是锁 '{self._name}' 的持有者")

        self._lock_count -= 1
        self._release_count += 1

        if self._lock_count == 0:
            self._owner = None

        self._lock.release()
        self._logger.debug(f"线程 {thread_id} 释放递归锁 '{self._name}'，"
                           f"剩余深度: {self._lock_count}")

    def locked(self) -> bool:
        """检查锁是否被持有"""
        return self._lock_count > 0

    @property
    def recursion_depth(self) -> int:
        """获取当前递归深度"""
        return self._lock_count

    @property
    def owner(self) -> Optional[int]:
        """获取当前持有者"""
        return self._owner

    def get_stats(self) -> dict:
        """获取统计信息"""
        avg_wait = self._total_wait_time / self._acquire_count if self._acquire_count > 0 else 0
        return {
            'name': self._name,
            'locked': self.locked(),
            'owner': self._owner,
            'recursion_depth': self._lock_count,
            'acquire_count': self._acquire_count,
            'release_count': self._release_count,
            'average_wait_time': avg_wait
        }

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False

    def __str__(self) -> str:
        status = f"locked(depth={self._lock_count})" if self.locked() else "unlocked"
        owner = f", owner={self._owner}" if self._owner else ""
        return f"RecursiveMutex(name='{self._name}', status={status}{owner})"


# 使用示例
if __name__ == "__main__":
    print("=== 互斥锁使用示例 ===\n")

    # 示例1: 基本互斥锁
    print("1. 基本互斥锁")
    mutex = Mutex(name="resource_lock")
    shared_counter = [0]  # 使用列表以便在闭包中修改

    def increment(task_id):
        for _ in range(1000):
            with mutex:
                old = shared_counter[0]
                shared_counter[0] = old + 1

    threads = [threading.Thread(target=increment, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"  计数器最终值: {shared_counter[0]} (期望: 5000)")
    print(f"  统计: {mutex.get_stats()}")

    # 示例2: 递归互斥锁
    print("\n2. 递归互斥锁")
    rec_mutex = RecursiveMutex(name="recursive_lock")

    def recursive_function(depth):
        if depth <= 0:
            return
        with rec_mutex:
            print(f"  递归深度: {depth}, 锁深度: {rec_mutex.recursion_depth}")
            recursive_function(depth - 1)

    recursive_function(3)
    print(f"  统计: {rec_mutex.get_stats()}")

    # 示例3: 演示所有权检查
    print("\n3. 所有权检查")
    mutex2 = Mutex(name="test_mutex")

    def try_release_other():
        try:
            mutex2.release()
        except RuntimeError as e:
            print(f"  正确捕获错误: {e}")

    with mutex2:
        print(f"  主线程持有锁: {mutex2.locked()}")
        t = threading.Thread(target=try_release_other)
        t.start()
        t.join()
