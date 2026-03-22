"""
用户级线程 (User-Level Threads)

==========================================
      用户级线程深入学习教程
==========================================

🎯 什么是用户级线程？
--------------------
用户级线程是由用户空间的线程库实现的线程，内核不知道这些线程的存在。
线程的创建、调度、同步都在用户空间完成。

📚 用户级线程 vs 内核级线程
---------------------------
| 特性           | 用户级线程         | 内核级线程         |
|----------------|-------------------|-------------------|
| 实现位置       | 用户空间           | 内核空间           |
| 内核感知       | 不知道             | 知道               |
| 切换开销       | 低                 | 高                 |
| 阻塞影响       | 整个进程阻塞       | 只阻塞该线程       |
| 多核并行       | 不能               | 能                 |
| 调度控制       | 用户程序           | 内核               |

💡 优点
-------
1. 线程切换快（不需要内核参与）
2. 调度算法可定制
3. 可在任何操作系统运行
4. 不需要内核支持

⚠️ 缺点
-------
1. 一个线程阻塞，整个进程阻塞
2. 不能利用多核
3. 时钟中断无法打断线程

🔧 协程 vs 用户级线程
---------------------
Python的协程类似于用户级线程，但更轻量：
- 协程是协作式调度
- 用户级线程可以是抢占式
"""

import time
import threading
from typing import Callable, Optional, List, Any
from enum import Enum
from collections import deque
from utils.logger import Logger


class ThreadState(Enum):
    """线程状态"""
    NEW = "new"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    TERMINATED = "terminated"


class UserThread:
    """
    用户级线程

    模拟用户空间的线程实现，使用协程式调度。
    """

    _next_tid = 1

    def __init__(self, target: Callable, name: str = "", args: tuple = ()):
        """
        初始化用户级线程

        Args:
            target: 线程执行函数
            name: 线程名称
            args: 函数参数
        """
        self._tid = UserThread._next_tid
        UserThread._next_tid += 1
        self._name = name or f"UserThread-{self._tid}"
        self._target = target
        self._args = args
        self._state = ThreadState.NEW
        self._result = None
        self._logger = Logger()

        # 用于协程式调度
        self._yield_requested = False

        # 统计
        self._cpu_time = 0.0
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

    @property
    def tid(self) -> int:
        """线程ID"""
        return self._tid

    @property
    def name(self) -> str:
        """线程名称"""
        return self._name

    @property
    def state(self) -> ThreadState:
        """线程状态"""
        return self._state

    @property
    def result(self) -> Any:
        """执行结果"""
        return self._result

    def start(self) -> None:
        """启动线程"""
        if self._state != ThreadState.NEW:
            raise RuntimeError(f"线程 {self._name} 已经启动")

        self._state = ThreadState.READY
        self._logger.debug(f"用户线程 {self._name} 准备就绪")

    def run(self, time_slice: float = 0.1) -> bool:
        """
        执行线程（由调度器调用）

        Args:
            time_slice: 时间片

        Returns:
            bool: 是否执行完成
        """
        if self._state == ThreadState.TERMINATED:
            return True

        if self._state == ThreadState.BLOCKED:
            return False

        self._state = ThreadState.RUNNING
        if self._start_time is None:
            self._start_time = time.time()

        start = time.time()
        self._yield_requested = False

        try:
            # 执行目标函数
            # 在实际的用户级线程中，这里需要更复杂的上下文切换
            self._result = self._target(*self._args)
            self._state = ThreadState.TERMINATED
            self._end_time = time.time()

        except Exception as e:
            self._logger.error(f"线程 {self._name} 执行错误: {e}")
            self._state = ThreadState.TERMINATED
            self._end_time = time.time()

        elapsed = time.time() - start
        self._cpu_time += elapsed

        return self._state == ThreadState.TERMINATED

    def yield_thread(self) -> None:
        """主动让出CPU"""
        self._yield_requested = True

    def block(self) -> None:
        """阻塞线程"""
        self._state = ThreadState.BLOCKED

    def unblock(self) -> None:
        """解除阻塞"""
        if self._state == ThreadState.BLOCKED:
            self._state = ThreadState.READY

    def terminate(self) -> None:
        """终止线程"""
        self._state = ThreadState.TERMINATED
        self._end_time = time.time()

    def get_info(self) -> dict:
        """获取线程信息"""
        return {
            'tid': self._tid,
            'name': self._name,
            'state': self._state.value,
            'cpu_time': self._cpu_time,
            'result': self._result
        }

    def __str__(self) -> str:
        return f"UserThread(tid={self._tid}, name='{self._name}', state={self._state.value})"


class UserThreadScheduler:
    """
    用户级线程调度器

    实现用户空间的线程调度，支持多种调度算法。
    """

    def __init__(self, algorithm: str = "round_robin", time_slice: float = 0.1):
        """
        初始化调度器

        Args:
            algorithm: 调度算法 (round_robin, priority, fifo)
            time_slice: 时间片
        """
        self._algorithm = algorithm
        self._time_slice = time_slice
        self._logger = Logger()

        # 线程队列
        self._ready_queue: deque = deque()
        self._threads: dict = {}  # tid -> thread
        self._current_thread: Optional[UserThread] = None

        # 调度状态
        self._running = False
        self._lock = threading.Lock()

        # 统计
        self._context_switches = 0
        self._total_threads = 0

    def create_thread(self, target: Callable, name: str = "",
                     args: tuple = (), priority: int = 0) -> UserThread:
        """
        创建新线程

        Args:
            target: 执行函数
            name: 线程名称
            args: 函数参数
            priority: 优先级

        Returns:
            UserThread: 创建的线程
        """
        thread = UserThread(target, name, args)
        thread._priority = priority  # 添加优先级属性

        with self._lock:
            self._threads[thread.tid] = thread
            self._ready_queue.append(thread)
            self._total_threads += 1

        thread.start()
        self._logger.debug(f"创建用户线程: {thread}")
        return thread

    def schedule(self) -> None:
        """
        执行调度

        根据调度算法选择下一个执行的线程
        """
        while self._ready_queue:
            thread = self._select_next_thread()
            if thread is None:
                break

            self._current_thread = thread
            self._context_switches += 1

            # 执行线程
            completed = thread.run(self._time_slice)

            if not completed and thread.state != ThreadState.BLOCKED:
                # 放回就绪队列
                self._ready_queue.append(thread)

    def _select_next_thread(self) -> Optional[UserThread]:
        """选择下一个执行的线程"""
        if not self._ready_queue:
            return None

        if self._algorithm == "priority":
            # 优先级调度
            threads = list(self._ready_queue)
            threads.sort(key=lambda t: getattr(t, '_priority', 0), reverse=True)
            self._ready_queue = deque(threads)
            return self._ready_queue.popleft()

        elif self._algorithm == "fifo":
            # FIFO调度
            return self._ready_queue.popleft()

        else:
            # 默认轮转调度
            return self._ready_queue.popleft()

    def block_thread(self, tid: int) -> None:
        """阻塞线程"""
        with self._lock:
            thread = self._threads.get(tid)
            if thread:
                thread.block()

    def unblock_thread(self, tid: int) -> None:
        """解除阻塞线程"""
        with self._lock:
            thread = self._threads.get(tid)
            if thread:
                thread.unblock()
                if thread.state == ThreadState.READY:
                    self._ready_queue.append(thread)

    def terminate_thread(self, tid: int) -> None:
        """终止线程"""
        with self._lock:
            thread = self._threads.get(tid)
            if thread:
                thread.terminate()

    def get_thread_count(self) -> int:
        """获取线程数量"""
        return len(self._threads)

    def get_ready_count(self) -> int:
        """获取就绪线程数量"""
        return len(self._ready_queue)

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'algorithm': self._algorithm,
            'time_slice': self._time_slice,
            'total_threads': self._total_threads,
            'active_threads': len(self._threads),
            'ready_threads': len(self._ready_queue),
            'context_switches': self._context_switches
        }

    def print_thread_states(self) -> None:
        """打印所有线程状态"""
        print("\n用户级线程状态:")
        print("-" * 50)
        for tid, thread in self._threads.items():
            print(f"  {thread}")
        print("-" * 50)


# 使用示例
if __name__ == "__main__":
    print("=== 用户级线程演示 ===\n")

    # 创建调度器
    scheduler = UserThreadScheduler(algorithm="round_robin", time_slice=0.1)

    # 创建线程
    def task1():
        print("  任务1: 开始执行")
        time.sleep(0.05)
        print("  任务1: 执行完成")
        return "task1_result"

    def task2():
        print("  任务2: 开始执行")
        time.sleep(0.05)
        print("  任务2: 执行完成")
        return "task2_result"

    def task3():
        print("  任务3: 开始执行")
        time.sleep(0.05)
        print("  任务3: 执行完成")
        return "task3_result"

    t1 = scheduler.create_thread(task1, "Worker-1")
    t2 = scheduler.create_thread(task2, "Worker-2")
    t3 = scheduler.create_thread(task3, "Worker-3")

    print("开始调度执行:")
    scheduler.schedule()

    print(f"\n执行结果:")
    print(f"  {t1.name}: {t1.result}")
    print(f"  {t2.name}: {t2.result}")
    print(f"  {t3.name}: {t3.result}")

    print(f"\n统计: {scheduler.get_stats()}")
