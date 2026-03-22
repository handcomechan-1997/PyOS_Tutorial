"""
内核级线程 (Kernel-Level Threads)

==========================================
      内核级线程深入学习教程
==========================================

🎯 什么是内核级线程？
--------------------
内核级线程是由操作系统内核直接管理的线程。
内核知道每个线程的存在，并负责线程的调度和同步。

📚 特点
-------
1. 内核维护线程控制块 (TCB)
2. 线程切换需要内核参与
3. 一个线程阻塞不影响其他线程
4. 可以利用多核处理器

💡 优点
-------
1. 真正的并行执行
2. 一个线程阻塞不会影响其他线程
3. 可以利用多核
4. 内核可以优化调度

⚠️ 缺点
-------
1. 线程切换开销大（需要内核态切换）
2. 创建线程需要系统调用
3. 调度开销较大

🔧 Python中的线程
-----------------
Python的 threading 模块创建的是内核级线程，
但由于GIL（全局解释器锁），同一时刻只有一个线程执行Python字节码。
"""

import threading
import time
from typing import Callable, Optional, Dict, List, Any
from enum import Enum
from utils.logger import Logger


class KernelThreadState(Enum):
    """内核线程状态"""
    NEW = "new"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    TERMINATED = "terminated"


class KernelThread:
    """
    内核级线程

    封装Python的threading.Thread，模拟内核线程管理。
    """

    _next_tid = 1

    def __init__(self, target: Callable = None, name: str = "",
                 args: tuple = (), kwargs: dict = None):
        """
        初始化内核线程

        Args:
            target: 执行函数
            name: 线程名称
            args: 位置参数
            kwargs: 关键字参数
        """
        self._tid = KernelThread._next_tid
        KernelThread._next_tid += 1
        self._name = name or f"KernelThread-{self._tid}"
        self._target = target
        self._args = args
        self._kwargs = kwargs or {}

        # 状态
        self._state = KernelThreadState.NEW
        self._result = None
        self._exception = None

        # 内部线程
        self._thread: Optional[threading.Thread] = None

        # 同步
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)

        # 统计
        self._cpu_time = 0.0
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

        # 优先级（模拟）
        self._priority = 0

        self._logger = Logger()

    @property
    def tid(self) -> int:
        return self._tid

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> KernelThreadState:
        return self._state

    @property
    def result(self) -> Any:
        return self._result

    @property
    def priority(self) -> int:
        return self._priority

    @priority.setter
    def priority(self, value: int) -> None:
        self._priority = value

    def start(self) -> None:
        """启动线程"""
        if self._state != KernelThreadState.NEW:
            raise RuntimeError(f"线程 {self._name} 已经启动")

        self._state = KernelThreadState.READY

        # 创建并启动内部线程
        self._thread = threading.Thread(
            target=self._run_wrapper,
            name=self._name,
            daemon=False
        )
        self._thread.start()
        self._logger.debug(f"内核线程 {self._name} 启动")

    def _run_wrapper(self) -> None:
        """线程执行包装器"""
        self._state = KernelThreadState.RUNNING
        self._start_time = time.time()

        try:
            if self._target:
                self._result = self._target(*self._args, **self._kwargs)
        except Exception as e:
            self._exception = e
            self._logger.error(f"线程 {self._name} 异常: {e}")
        finally:
            self._state = KernelThreadState.TERMINATED
            self._end_time = time.time()

            with self._condition:
                self._condition.notify_all()

    def join(self, timeout: Optional[float] = None) -> bool:
        """
        等待线程结束

        Args:
            timeout: 超时时间

        Returns:
            bool: 是否正常结束
        """
        if self._thread is None:
            return True

        self._thread.join(timeout=timeout)
        return not self._thread.is_alive()

    def is_alive(self) -> bool:
        """检查线程是否存活"""
        return self._thread is not None and self._thread.is_alive()

    def get_cpu_time(self) -> float:
        """获取CPU时间"""
        if self._start_time is None:
            return 0.0
        end = self._end_time or time.time()
        return end - self._start_time

    def get_info(self) -> dict:
        """获取线程信息"""
        return {
            'tid': self._tid,
            'name': self._name,
            'state': self._state.value,
            'priority': self._priority,
            'cpu_time': self.get_cpu_time(),
            'alive': self.is_alive(),
            'result': self._result,
            'exception': str(self._exception) if self._exception else None
        }

    def __str__(self) -> str:
        return f"KernelThread(tid={self._tid}, name='{self._name}', state={self._state.value})"


class KernelThreadManager:
    """
    内核线程管理器

    管理所有内核线程，提供创建、调度、同步等功能。
    """

    def __init__(self):
        """初始化线程管理器"""
        self._threads: Dict[int, KernelThread] = {}
        self._lock = threading.Lock()
        self._logger = Logger()

        # 统计
        self._total_created = 0
        self._total_terminated = 0

        self._logger.info("内核线程管理器初始化")

    def create_thread(self, target: Callable, name: str = "",
                     args: tuple = (), kwargs: dict = None,
                     priority: int = 0) -> KernelThread:
        """
        创建内核线程

        Args:
            target: 执行函数
            name: 线程名称
            args: 位置参数
            kwargs: 关键字参数
            priority: 优先级

        Returns:
            KernelThread: 创建的线程
        """
        thread = KernelThread(target, name, args, kwargs)
        thread.priority = priority

        with self._lock:
            self._threads[thread.tid] = thread
            self._total_created += 1

        self._logger.debug(f"创建内核线程: {thread}")
        return thread

    def start_thread(self, tid: int) -> bool:
        """启动线程"""
        with self._lock:
            thread = self._threads.get(tid)
            if thread:
                thread.start()
                return True
        return False

    def terminate_thread(self, tid: int) -> bool:
        """终止线程（标记为终止）"""
        with self._lock:
            thread = self._threads.get(tid)
            if thread and thread.is_alive():
                # Python线程不能被强制终止，只能标记
                thread._state = KernelThreadState.TERMINATED
                self._total_terminated += 1
                return True
        return False

    def join_thread(self, tid: int, timeout: Optional[float] = None) -> bool:
        """等待线程结束"""
        thread = self._threads.get(tid)
        if thread:
            return thread.join(timeout)
        return False

    def get_thread(self, tid: int) -> Optional[KernelThread]:
        """获取线程"""
        return self._threads.get(tid)

    def get_all_threads(self) -> List[KernelThread]:
        """获取所有线程"""
        return list(self._threads.values())

    def get_active_threads(self) -> List[KernelThread]:
        """获取活动线程"""
        return [t for t in self._threads.values() if t.is_alive()]

    def cleanup_terminated(self) -> int:
        """清理已终止的线程"""
        count = 0
        with self._lock:
            to_remove = [
                tid for tid, thread in self._threads.items()
                if thread.state == KernelThreadState.TERMINATED
            ]
            for tid in to_remove:
                del self._threads[tid]
                count += 1

        self._logger.debug(f"清理了 {count} 个已终止线程")
        return count

    def get_thread_count(self) -> int:
        """获取线程数量"""
        return len(self._threads)

    def get_active_count(self) -> int:
        """获取活动线程数量"""
        return len(self.get_active_threads())

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'total_created': self._total_created,
            'total_terminated': self._total_terminated,
            'active_threads': self.get_active_count(),
            'total_threads': len(self._threads)
        }

    def print_thread_status(self) -> None:
        """打印线程状态"""
        print("\n内核线程状态:")
        print("-" * 60)
        print(f"{'TID':<6} {'名称':<20} {'状态':<12} {'存活':<6} {'优先级':<6}")
        print("-" * 60)

        for thread in self._threads.values():
            info = thread.get_info()
            print(f"{info['tid']:<6} {info['name']:<20} {info['state']:<12} "
                  f"{'是' if info['alive'] else '否':<6} {info['priority']:<6}")

        print("-" * 60)


# 使用示例
if __name__ == "__main__":
    print("=== 内核级线程演示 ===\n")

    manager = KernelThreadManager()

    def worker(name, duration):
        print(f"  {name}: 开始工作")
        time.sleep(duration)
        print(f"  {name}: 工作完成")
        return f"{name}_result"

    # 创建多个线程
    t1 = manager.create_thread(worker, "Worker-A", args=("Worker-A", 0.3), priority=1)
    t2 = manager.create_thread(worker, "Worker-B", args=("Worker-B", 0.2), priority=2)
    t3 = manager.create_thread(worker, "Worker-C", args=("Worker-C", 0.1), priority=0)

    # 启动线程
    print("启动线程:")
    manager.start_thread(t1.tid)
    manager.start_thread(t2.tid)
    manager.start_thread(t3.tid)

    # 打印状态
    manager.print_thread_status()

    # 等待所有线程完成
    print("\n等待线程完成...")
    for tid in [t1.tid, t2.tid, t3.tid]:
        manager.join_thread(tid)

    # 打印最终状态
    print("\n最终状态:")
    manager.print_thread_status()

    # 打印结果
    print("\n执行结果:")
    for thread in manager.get_all_threads():
        print(f"  {thread.name}: {thread.result}")

    print(f"\n统计: {manager.get_stats()}")
