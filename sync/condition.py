"""
条件变量 (Condition Variable) - 线程同步的高级机制

==========================================
       条件变量深入学习教程
==========================================

🎯 什么是条件变量？
------------------
条件变量是一种同步原语，允许线程等待某个条件成立后再继续执行。
它总是与一个互斥锁配合使用，用于避免忙等待。

📚 核心概念
-----------
1. 等待 (wait): 线程释放锁并进入等待状态
2. 通知 (signal/notify): 唤醒一个等待的线程
3. 广播 (broadcast/notify_all): 唤醒所有等待的线程

🔧 工作原理
-----------
典型的使用模式：

    # 等待线程
    with mutex:
        while not condition:      # 条件不满足
            cond.wait(mutex)      # 释放锁并等待
        # 条件满足，继续执行

    # 通知线程
    with mutex:
        change_condition()        # 改变条件
        cond.signal()             # 唤醒等待线程

💡 为什么需要 while 循环？
-------------------------
1. 虚假唤醒 (Spurious Wakeup): 系统可能无故唤醒等待线程
2. 抢占: 被唤醒后，其他线程可能先获取锁并改变条件
3. 广播: 多个线程被唤醒，但资源可能不足

⚠️ 注意事项
-----------
- 必须在持有锁的情况下调用 wait
- wait 会自动释放锁，被唤醒时重新获取锁
- signal/broadcast 应该在持有锁时调用
- 使用 while 而不是 if 检查条件
"""

import threading
import time
from typing import Optional, Callable
from collections import deque
from utils.logger import Logger


class ConditionVariable:
    """
    条件变量实现

    允许线程等待特定条件成立，支持单个唤醒和广播唤醒。
    必须与互斥锁配合使用。
    """

    def __init__(self, name: str = ""):
        """
        初始化条件变量

        Args:
            name: 条件变量名称
        """
        self._name = name or f"condition_{id(self)}"
        self._lock = threading.Lock()
        self._wait_queue: deque = deque()  # 等待队列
        self._logger = Logger()

        # 统计信息
        self._wait_count = 0
        self._signal_count = 0
        self._broadcast_count = 0
        self._total_wait_time = 0.0

        self._logger.info(f"条件变量 '{self._name}' 创建")

    def wait(self, mutex: threading.Lock, timeout: Optional[float] = None) -> bool:
        """
        等待条件成立

        原子地释放 mutex 并进入等待状态，被唤醒时重新获取 mutex

        Args:
            mutex: 与条件变量关联的互斥锁
            timeout: 超时时间（秒）

        Returns:
            bool: 是否被正常唤醒（False表示超时）
        """
        if mutex is None:
            raise ValueError("必须提供互斥锁")

        start_time = time.time()

        # 创建等待事件
        event = threading.Event()

        with self._lock:
            self._wait_queue.append(event)
            self._wait_count += 1

        # 释放互斥锁（必须在锁外等待）
        mutex.release()

        self._logger.debug(f"线程 {threading.current_thread().ident} "
                           f"在条件变量 '{self._name}' 上等待")

        # 等待被唤醒或超时
        success = event.wait(timeout=timeout)

        # 重新获取互斥锁
        mutex.acquire()

        with self._lock:
            if not success:
                # 超时，从队列中移除
                if event in self._wait_queue:
                    self._wait_queue.remove(event)
            else:
                wait_time = time.time() - start_time
                self._total_wait_time += wait_time

        return success

    def signal(self) -> None:
        """
        唤醒一个等待线程

        如果有线程在等待，唤醒其中一个（FIFO顺序）
        """
        with self._lock:
            self._signal_count += 1

            if self._wait_queue:
                event = self._wait_queue.popleft()
                event.set()
                self._logger.debug(f"条件变量 '{self._name}' 唤醒一个线程")

    def broadcast(self) -> None:
        """
        唤醒所有等待线程

        当条件改变可能影响多个等待线程时使用
        """
        with self._lock:
            self._broadcast_count += 1

            if self._wait_queue:
                # 唤醒所有等待的线程
                while self._wait_queue:
                    event = self._wait_queue.popleft()
                    event.set()
                self._logger.debug(f"条件变量 '{self._name}' 广播唤醒所有线程")

    # 别名
    notify = signal
    notify_all = broadcast

    @property
    def waiting_count(self) -> int:
        """获取等待线程数量"""
        with self._lock:
            return len(self._wait_queue)

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            avg_wait = self._total_wait_time / self._wait_count if self._wait_count > 0 else 0
            return {
                'name': self._name,
                'waiting_count': len(self._wait_queue),
                'total_waits': self._wait_count,
                'signal_count': self._signal_count,
                'broadcast_count': self._broadcast_count,
                'average_wait_time': avg_wait
            }

    def __str__(self) -> str:
        return f"ConditionVariable(name='{self._name}', waiting={self.waiting_count})"


class BoundedBuffer:
    """
    有界缓冲区 - 条件变量经典应用

    实现一个线程安全的有界缓冲区，展示条件变量的典型用法。
    这是生产者-消费者问题的核心组件。
    """

    def __init__(self, capacity: int):
        """
        初始化有界缓冲区

        Args:
            capacity: 缓冲区容量
        """
        self._capacity = capacity
        self._buffer: deque = deque()
        self._mutex = threading.Lock()
        self._not_full = ConditionVariable(name="not_full")
        self._not_empty = ConditionVariable(name="not_empty")
        self._logger = Logger()

        # 统计
        self._put_count = 0
        self._get_count = 0

    def put(self, item, timeout: Optional[float] = None) -> bool:
        """
        放入元素

        如果缓冲区已满，等待直到有空间或超时

        Args:
            item: 要放入的元素
            timeout: 超时时间

        Returns:
            bool: 是否成功放入
        """
        with self._mutex:
            # 等待缓冲区不满
            while len(self._buffer) >= self._capacity:
                if not self._not_full.wait(self._mutex, timeout):
                    return False

            # 放入元素
            self._buffer.append(item)
            self._put_count += 1
            self._logger.debug(f"放入元素: {item}, 缓冲区大小: {len(self._buffer)}")

            # 通知消费者
            self._not_empty.signal()
            return True

    def get(self, timeout: Optional[float] = None):
        """
        获取元素

        如果缓冲区为空，等待直到有元素或超时

        Args:
            timeout: 超时时间

        Returns:
            元素，如果超时返回 None
        """
        with self._mutex:
            # 等待缓冲区不空
            while len(self._buffer) == 0:
                if not self._not_empty.wait(self._mutex, timeout):
                    return None

            # 获取元素
            item = self._buffer.popleft()
            self._get_count += 1
            self._logger.debug(f"获取元素: {item}, 缓冲区大小: {len(self._buffer)}")

            # 通知生产者
            self._not_full.signal()
            return item

    @property
    def size(self) -> int:
        """获取当前大小"""
        with self._mutex:
            return len(self._buffer)

    @property
    def is_empty(self) -> bool:
        """是否为空"""
        return self.size == 0

    @property
    def is_full(self) -> bool:
        """是否已满"""
        return self.size >= self._capacity

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._mutex:
            return {
                'capacity': self._capacity,
                'size': len(self._buffer),
                'put_count': self._put_count,
                'get_count': self._get_count,
                'not_full_stats': self._not_full.get_stats(),
                'not_empty_stats': self._not_empty.get_stats()
            }


# 使用示例
if __name__ == "__main__":
    print("=== 条件变量使用示例 ===\n")

    # 示例1: 基本条件变量
    print("1. 基本条件变量 - 线程间同步")
    mutex = threading.Lock()
    cond = ConditionVariable(name="test_cond")
    ready = [False]
    data = [None]

    def waiter():
        with mutex:
            while not ready[0]:
                print("  等待线程: 等待条件...")
                cond.wait(mutex)
            print(f"  等待线程: 收到数据 {data[0]}")

    def notifier():
        time.sleep(1)
        with mutex:
            data[0] = "Hello from notifier!"
            ready[0] = True
            print("  通知线程: 设置条件并通知")
            cond.signal()

    t1 = threading.Thread(target=waiter)
    t2 = threading.Thread(target=notifier)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    print(f"\n  统计: {cond.get_stats()}")

    # 示例2: 有界缓冲区
    print("\n2. 有界缓冲区 - 生产者消费者")
    buffer = BoundedBuffer(capacity=3)

    def producer(pid):
        for i in range(5):
            item = f"P{pid}-item{i}"
            buffer.put(item)
            print(f"  生产者{pid}: 生产 {item}")
            time.sleep(0.1)

    def consumer(cid):
        for _ in range(5):
            item = buffer.get(timeout=2)
            if item:
                print(f"  消费者{cid}: 消费 {item}")
            time.sleep(0.2)

    producers = [threading.Thread(target=producer, args=(i,)) for i in range(2)]
    consumers = [threading.Thread(target=consumer, args=(i,)) for i in range(2)]

    for t in producers + consumers:
        t.start()
    for t in producers + consumers:
        t.join()

    print(f"\n  统计: {buffer.get_stats()}")
