"""
信号量 (Semaphore) - 经典的同步原语

==========================================
         信号量深入学习教程
==========================================

🎯 什么是信号量？
----------------
信号量是由荷兰计算机科学家 Edsger Dijkstra 在 1965 年提出的同步机制。
它是一个整数变量，只能通过两个原子操作来访问：
- P操作 (Proberen/Wait): 申请资源
- V操作 (Verhogen/Signal): 释放资源

📚 信号量的类型
---------------
1. 二进制信号量 (Binary Semaphore)
   - 值只能是 0 或 1
   - 类似于互斥锁，用于互斥访问

2. 计数信号量 (Counting Semaphore)
   - 值可以是任意非负整数
   - 用于资源计数，控制并发访问数量

🔧 核心操作
-----------
P操作 (wait/down):
    while S <= 0:
        block()  # 阻塞等待
    S = S - 1   # 原子操作

V操作 (signal/up):
    S = S + 1   # 原子操作
    wakeup()    # 唤醒等待进程

💡 应用场景
-----------
1. 互斥访问临界区
2. 控制并发数量
3. 进程同步（事件通知）
4. 生产者-消费者问题

⚠️ 注意事项
-----------
- 必须成对使用 P/V 操作
- 不能颠倒 P/V 操作顺序
- 避免死锁和饥饿
"""

import threading
import time
from typing import Optional, List
from collections import deque
from utils.logger import Logger


class Semaphore:
    """
    通用信号量实现

    支持计数信号量和二进制信号量的基础类。
    使用队列管理等待的进程/线程，确保公平性 (FIFO)。
    """

    def __init__(self, value: int = 1, name: str = ""):
        """
        初始化信号量

        Args:
            value: 信号量初始值，必须 >= 0
            name: 信号量名称，用于调试
        """
        if value < 0:
            raise ValueError("信号量初始值不能为负数")

        self._value = value
        self._name = name or f"semaphore_{id(self)}"
        self._lock = threading.Lock()
        self._wait_queue: deque = deque()  # 等待队列
        self._logger = Logger()

        # 统计信息
        self._wait_count = 0
        self._signal_count = 0
        self._total_wait_time = 0.0

        self._logger.info(f"信号量 '{self._name}' 创建，初始值: {value}")

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        P操作 - 申请资源

        如果信号量值 > 0，减1并返回True
        否则阻塞等待，直到有资源可用或超时

        Args:
            timeout: 超时时间（秒），None表示无限等待

        Returns:
            bool: 是否成功获取资源
        """
        start_time = time.time()

        with self._lock:
            if self._value > 0:
                # 有资源可用，直接获取
                self._value -= 1
                self._logger.debug(f"P操作成功: {self._name}, 剩余: {self._value}")
                return True

            # 没有资源，需要等待
            # 创建一个事件用于等待通知
            event = threading.Event()
            self._wait_queue.append(event)
            self._wait_count += 1

        # 在锁外等待，避免死锁
        self._logger.debug(f"P操作等待: {self._name}, 队列长度: {len(self._wait_queue)}")

        # 等待被唤醒或超时
        success = event.wait(timeout=timeout)

        with self._lock:
            if not success:
                # 超时，从队列中移除
                if event in self._wait_queue:
                    self._wait_queue.remove(event)
                self._logger.debug(f"P操作超时: {self._name}")
                return False

            # 被唤醒，资源已经在 signal 中分配
            wait_time = time.time() - start_time
            self._total_wait_time += wait_time
            self._logger.debug(f"P操作完成: {self._name}, 等待时间: {wait_time:.3f}s")
            return True

    def release(self) -> None:
        """
        V操作 - 释放资源

        增加信号量值，如果有等待的进程则唤醒一个
        """
        with self._lock:
            self._signal_count += 1

            if self._wait_queue:
                # 有等待的进程，唤醒一个
                event = self._wait_queue.popleft()
                event.set()
                self._logger.debug(f"V操作唤醒: {self._name}")
            else:
                # 没有等待的进程，增加信号量值
                self._value += 1
                self._logger.debug(f"V操作增加: {self._name}, 当前值: {self._value}")

    # 别名，便于理解
    def wait(self, timeout: Optional[float] = None) -> bool:
        """P操作的别名"""
        return self.acquire(timeout)

    def signal(self) -> None:
        """V操作的别名"""
        self.release()

    def P(self) -> bool:
        """Dijkstra原始记号 P操作"""
        return self.acquire()

    def V(self) -> None:
        """Dijkstra原始记号 V操作"""
        self.release()

    @property
    def value(self) -> int:
        """获取当前信号量值（仅用于调试）"""
        with self._lock:
            return self._value

    @property
    def waiting_count(self) -> int:
        """获取等待进程数量"""
        with self._lock:
            return len(self._wait_queue)

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            avg_wait = self._total_wait_time / self._wait_count if self._wait_count > 0 else 0
            return {
                'name': self._name,
                'value': self._value,
                'waiting_count': len(self._wait_queue),
                'total_waits': self._wait_count,
                'total_signals': self._signal_count,
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
        return f"Semaphore(name='{self._name}', value={self._value}, waiting={self.waiting_count})"


class BinarySemaphore(Semaphore):
    """
    二进制信号量

    值只能是 0 或 1，主要用于互斥访问。
    与互斥锁的区别：
    - 信号量可以被任何进程释放
    - 互斥锁只能由持有者释放
    """

    def __init__(self, name: str = "", initial_value: int = 1):
        if initial_value not in (0, 1):
            raise ValueError("二进制信号量初始值必须是 0 或 1")
        super().__init__(value=initial_value, name=name)

    def release(self) -> None:
        """重写释放方法，确保值不超过1"""
        with self._lock:
            self._signal_count += 1

            if self._wait_queue:
                # 有等待的进程，唤醒一个
                event = self._wait_queue.popleft()
                event.set()
            elif self._value == 0:
                # 只有当前值为0时才增加
                self._value = 1

    def __str__(self) -> str:
        return f"BinarySemaphore(name='{self._name}', value={self._value})"


class CountingSemaphore(Semaphore):
    """
    计数信号量

    用于控制对有限数量资源的并发访问。
    例如：数据库连接池、线程池等。
    """

    def __init__(self, max_count: int, name: str = ""):
        """
        初始化计数信号量

        Args:
            max_count: 最大资源数量
            name: 信号量名称
        """
        if max_count <= 0:
            raise ValueError("最大资源数量必须大于0")

        super().__init__(value=max_count, name=name)
        self._max_count = max_count

    @property
    def available(self) -> int:
        """获取可用资源数量"""
        return self._value

    @property
    def used(self) -> int:
        """获取已使用资源数量"""
        return self._max_count - self._value

    @property
    def utilization(self) -> float:
        """获取资源利用率"""
        return (self.used / self._max_count) * 100

    def get_stats(self) -> dict:
        stats = super().get_stats()
        stats.update({
            'max_count': self._max_count,
            'available': self.available,
            'used': self.used,
            'utilization': self.utilization
        })
        return stats

    def __str__(self) -> str:
        return (f"CountingSemaphore(name='{self._name}', "
                f"available={self.available}/{self._max_count})")


# 使用示例
if __name__ == "__main__":
    print("=== 信号量使用示例 ===\n")

    # 示例1: 二进制信号量用于互斥
    print("1. 二进制信号量 - 互斥访问")
    mutex = BinarySemaphore(name="mutex")

    def critical_section(task_id):
        print(f"  任务 {task_id} 尝试进入临界区...")
        mutex.acquire()
        print(f"  任务 {task_id} 进入临界区")
        time.sleep(0.5)  # 模拟临界区操作
        print(f"  任务 {task_id} 离开临界区")
        mutex.release()

    threads = [threading.Thread(target=critical_section, args=(i,)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"\n  统计: {mutex.get_stats()}")

    # 示例2: 计数信号量控制并发
    print("\n2. 计数信号量 - 限制并发数")
    pool_sem = CountingSemaphore(max_count=2, name="connection_pool")

    def use_resource(task_id):
        print(f"  任务 {task_id} 请求资源...")
        pool_sem.acquire()
        print(f"  任务 {task_id} 获得资源 (使用: {pool_sem.used}/{pool_sem._max_count})")
        time.sleep(1)
        print(f"  任务 {task_id} 释放资源")
        pool_sem.release()

    threads = [threading.Thread(target=use_resource, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"\n  统计: {pool_sem.get_stats()}")
