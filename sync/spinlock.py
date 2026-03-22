"""
自旋锁 (Spin Lock) - 忙等待的同步机制

==========================================
        自旋锁深入学习教程
==========================================

🎯 什么是自旋锁？
----------------
自旋锁是一种忙等待锁，当锁被占用时，请求线程不会阻塞，
而是在一个循环中不断尝试获取锁（自旋）。

📚 自旋锁 vs 互斥锁
-------------------
| 特性         | 自旋锁           | 互斥锁           |
|--------------|------------------|------------------|
| 等待方式     | 忙等待（占用CPU）| 阻塞（释放CPU）  |
| 上下文切换   | 无               | 有               |
| 适用场景     | 短临界区         | 长临界区         |
| 实现复杂度   | 简单             | 较复杂           |
| 多核效率     | 高               | 较低             |

🔧 工作原理
-----------
while (lock_is_held):
    ;  // 自旋等待
acquire_lock();

💡 适用场景
-----------
1. 临界区非常短（几条指令）
2. 多核系统
3. 中断上下文（不能阻塞）
4. 实时系统（避免调度延迟）

⚠️ 注意事项
-----------
1. 不适合长临界区（浪费CPU）
2. 单核系统上可能导致死锁
3. 可能导致优先级反转
4. 需要配合内存屏障使用
"""

import threading
import time
from typing import Optional
from utils.logger import Logger


class SpinLock:
    """
    自旋锁实现

    使用原子操作实现忙等待锁，适用于短临界区。
    """

    def __init__(self, name: str = ""):
        """
        初始化自旋锁

        Args:
            name: 锁的名称
        """
        self._name = name or f"spinlock_{id(self)}"
        self._locked = False
        self._owner: Optional[int] = None
        self._logger = Logger()

        # 统计
        self._acquire_count = 0
        self._spin_count = 0  # 自旋次数
        self._total_spin_time = 0.0

        self._logger.info(f"自旋锁 '{self._name}' 创建")

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        获取锁

        忙等待直到获取锁或超时

        Args:
            timeout: 超时时间（秒）

        Returns:
            bool: 是否成功获取
        """
        current_thread = threading.current_thread()
        thread_id = current_thread.ident
        start_time = time.time()
        spin_count = 0

        while True:
            # 尝试原子地获取锁
            if not self._locked:
                # 这里使用简单的检查-设置，实际应使用CAS指令
                # Python的GIL保证了简单的原子性，但不是真正的CAS
                self._locked = True
                self._owner = thread_id
                self._acquire_count += 1
                self._spin_count += spin_count
                self._total_spin_time += time.time() - start_time
                self._logger.debug(f"自旋锁 '{self._name}' 被线程 {thread_id} 获取，"
                                   f"自旋次数: {spin_count}")
                return True

            spin_count += 1

            # 检查超时
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    self._logger.debug(f"自旋锁 '{self._name}' 获取超时")
                    return False

            # 让出CPU（模拟真实的自旋锁行为）
            # 实际的自旋锁会使用pause指令减少功耗
            time.sleep(0)

    def release(self) -> None:
        """释放锁"""
        current_thread = threading.current_thread()
        thread_id = current_thread.ident

        if not self._locked:
            raise RuntimeError("锁未被持有")

        if self._owner != thread_id:
            raise RuntimeError(f"线程 {thread_id} 不是锁的持有者")

        self._locked = False
        self._owner = None
        self._logger.debug(f"自旋锁 '{self._name}' 被释放")

    def locked(self) -> bool:
        """检查锁是否被持有"""
        return self._locked

    @property
    def owner(self) -> Optional[int]:
        """获取持有者"""
        return self._owner

    def get_stats(self) -> dict:
        """获取统计信息"""
        avg_spin = self._spin_count / self._acquire_count if self._acquire_count > 0 else 0
        return {
            'name': self._name,
            'locked': self._locked,
            'owner': self._owner,
            'acquire_count': self._acquire_count,
            'total_spin_count': self._spin_count,
            'average_spin_count': avg_spin
        }

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False

    def __str__(self) -> str:
        status = "locked" if self._locked else "unlocked"
        return f"SpinLock(name='{self._name}', status={status})"


class TicketLock:
    """
    排号自旋锁 (Ticket Lock)

    一种公平的自旋锁变体，按照请求顺序分配锁。
    避免了普通自旋锁的不公平性。

    工作原理：
    1. 获取锁时，获取一个票号
    2. 等待自己的票号被叫到
    3. 释放锁时，叫下一个票号
    """

    def __init__(self, name: str = ""):
        """初始化排号锁"""
        self._name = name or f"ticketlock_{id(self)}"
        self._ticket = 0        # 当前票号
        self._turn = 0          # 当前叫号
        self._lock = threading.Lock()
        self._logger = Logger()

        self._acquire_count = 0

    def acquire(self) -> int:
        """
        获取锁，返回票号

        Returns:
            int: 票号
        """
        with self._lock:
            my_ticket = self._ticket
            self._ticket += 1

        self._logger.debug(f"排号锁 '{self._name}' 分配票号: {my_ticket}")

        # 等待自己的票号
        while True:
            with self._lock:
                if self._turn == my_ticket:
                    self._acquire_count += 1
                    return my_ticket
            time.sleep(0)

    def release(self) -> None:
        """释放锁，叫下一个号"""
        with self._lock:
            self._turn += 1
            self._logger.debug(f"排号锁 '{self._name}' 叫号: {self._turn}")

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *args):
        self.release()
        return False


class MCSLock:
    """
    MCS锁 (Mellor-Crummey and Scott Lock)

    一种基于链表的可扩展自旋锁，每个等待者在自己的本地变量上自旋，
    减少了缓存一致性流量。

    特点：
    - 公平性：FIFO顺序
    - 可扩展：多核系统性能好
    - 低开销：每个等待者在本地变量上自旋
    """

    class Node:
        """MCS锁节点"""
        def __init__(self):
            self.locked = True  # 是否需要等待
            self.next = None    # 下一个节点

    def __init__(self, name: str = ""):
        """初始化MCS锁"""
        self._name = name or f"mcslock_{id(self)}"
        self._tail = None
        self._lock = threading.Lock()
        self._logger = Logger()

    def acquire(self):
        """
        获取锁

        Returns:
            Node: 当前线程的节点，释放时需要
        """
        node = self.Node()

        with self._lock:
            prev = self._tail
            self._tail = node

        if prev is not None:
            # 有前驱，需要等待
            prev.next = node
            while node.locked:
                time.sleep(0)

        return node

    def release(self, node) -> None:
        """
        释放锁

        Args:
            node: acquire返回的节点
        """
        with self._lock:
            if node.next is None:
                # 没有后继，尝试释放锁
                if self._tail == node:
                    self._tail = None
                    return
                # 等待后继节点链接上来
                while node.next is None:
                    self._lock.release()
                    time.sleep(0)
                    self._lock.acquire()

        # 唤醒后继
        node.next.locked = False


# 使用示例
if __name__ == "__main__":
    print("=== 自旋锁使用示例 ===\n")

    # 示例1: 基本自旋锁
    print("1. 基本自旋锁")
    spinlock = SpinLock(name="test_spinlock")
    counter = [0]

    def increment(tid):
        for _ in range(1000):
            with spinlock:
                old = counter[0]
                counter[0] = old + 1

    threads = [threading.Thread(target=increment, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"  计数器值: {counter[0]} (期望: 4000)")
    print(f"  统计: {spinlock.get_stats()}")

    # 示例2: 排号锁
    print("\n2. 排号自旋锁")
    ticket_lock = TicketLock(name="test_ticket")

    def with_ticket(tid):
        ticket = ticket_lock.acquire()
        print(f"  线程{tid} 获取锁，票号: {ticket}")
        time.sleep(0.1)
        ticket_lock.release()
        print(f"  线程{tid} 释放锁")

    threads = [threading.Thread(target=with_ticket, args=(i,)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
