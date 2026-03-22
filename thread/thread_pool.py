"""
线程池 (Thread Pool)

==========================================
        线程池深入学习教程
==========================================

🎯 什么是线程池？
----------------
线程池是一种线程管理模式，预先创建一组线程，重复利用它们执行任务。
避免频繁创建和销毁线程的开销。

📚 为什么需要线程池？
--------------------
1. 线程创建/销毁开销大
2. 控制并发线程数量
3. 提供任务队列管理
4. 统一管理线程生命周期

💡 核心组件
-----------
1. 工作线程 (Worker Thread): 执行任务的线程
2. 任务队列 (Task Queue): 存储待执行任务
3. 线程池管理器 (Pool Manager): 管理线程和任务

🔧 工作流程
-----------
1. 初始化时创建固定数量的工作线程
2. 任务提交到任务队列
3. 空闲工作线程从队列获取任务执行
4. 执行完成后线程回到池中等待新任务

⚠️ 注意事项
-----------
1. 合理设置线程数量（CPU密集型：核心数，IO密集型：可更多）
2. 任务队列要有界，防止内存溢出
3. 处理好拒绝策略
4. 优雅关闭线程池
"""

import threading
import time
import queue
from typing import Callable, Optional, Any, List
from concurrent.futures import Future
from enum import Enum
from utils.logger import Logger


class PoolState(Enum):
    """线程池状态"""
    RUNNING = "running"
    SHUTDOWN = "shutdown"
    TERMINATED = "terminated"


class ThreadPool:
    """
    线程池实现

    提供可重用的线程池，用于并发执行任务。
    """

    def __init__(self, max_workers: int = 4, name: str = ""):
        """
        初始化线程池

        Args:
            max_workers: 最大工作线程数
            name: 线程池名称
        """
        self._max_workers = max_workers
        self._name = name or f"ThreadPool-{id(self)}"
        self._logger = Logger()

        # 状态
        self._state = PoolState.RUNNING
        self._lock = threading.Lock()

        # 任务队列
        self._task_queue: queue.Queue = queue.Queue()

        # 工作线程
        self._workers: List[threading.Thread] = []
        self._idle_count = 0

        # 统计
        self._submitted_tasks = 0
        self._completed_tasks = 0
        self._rejected_tasks = 0

        # 创建工作线程
        self._create_workers()

        self._logger.info(f"线程池 '{self._name}' 创建，工作线程数: {max_workers}")

    def _create_workers(self) -> None:
        """创建工作线程"""
        for i in range(self._max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"{self._name}-Worker-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)

    def _worker_loop(self) -> None:
        """工作线程主循环"""
        while True:
            with self._lock:
                if self._state == PoolState.TERMINATED:
                    break

            try:
                # 从队列获取任务
                task = self._task_queue.get(timeout=0.5)

                if task is None:  # 停止信号
                    break

                future, func, args, kwargs = task

                with self._lock:
                    self._idle_count -= 1

                try:
                    # 执行任务
                    result = func(*args, **kwargs)
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)
                finally:
                    self._task_queue.task_done()
                    with self._lock:
                        self._completed_tasks += 1
                        self._idle_count += 1

            except queue.Empty:
                continue

    def submit(self, func: Callable, *args, **kwargs) -> Future:
        """
        提交任务

        Args:
            func: 执行函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Future: 任务未来对象
        """
        with self._lock:
            if self._state != PoolState.RUNNING:
                self._rejected_tasks += 1
                raise RuntimeError("线程池已关闭")

            future = Future()
            self._task_queue.put((future, func, args, kwargs))
            self._submitted_tasks += 1

        return future

    def map(self, func: Callable, iterable: List) -> List[Any]:
        """
        批量执行任务

        Args:
            func: 执行函数
            iterable: 参数列表

        Returns:
            List: 结果列表
        """
        futures = [self.submit(func, item) for item in iterable]
        return [f.result() for f in futures]

    def shutdown(self, wait: bool = True) -> None:
        """
        关闭线程池

        Args:
            wait: 是否等待任务完成
        """
        with self._lock:
            if self._state == PoolState.TERMINATED:
                return

            self._state = PoolState.SHUTDOWN

        if wait:
            self._task_queue.join()

        # 发送停止信号
        for _ in self._workers:
            self._task_queue.put(None)

        # 等待工作线程结束
        for worker in self._workers:
            worker.join(timeout=1.0)

        self._state = PoolState.TERMINATED
        self._logger.info(f"线程池 '{self._name}' 已关闭")

    def get_active_count(self) -> int:
        """获取活动线程数"""
        with self._lock:
            return self._max_workers - self._idle_count

    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self._task_queue.qsize()

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            return {
                'name': self._name,
                'state': self._state.value,
                'max_workers': self._max_workers,
                'active_workers': self._max_workers - self._idle_count,
                'idle_workers': self._idle_count,
                'queue_size': self._task_queue.qsize(),
                'submitted_tasks': self._submitted_tasks,
                'completed_tasks': self._completed_tasks,
                'rejected_tasks': self._rejected_tasks
            }


class ThreadPoolExecutor:
    """
    线程池执行器

    提供更高级的线程池功能，支持上下文管理。
    """

    def __init__(self, max_workers: int = None):
        """
        初始化执行器

        Args:
            max_workers: 最大工作线程数，默认为CPU核心数*2
        """
        if max_workers is None:
            max_workers = (threading.cpu_count() or 1) * 2

        self._pool = ThreadPool(max_workers)
        self._logger = Logger()

    def submit(self, func: Callable, *args, **kwargs) -> Future:
        """提交任务"""
        return self._pool.submit(func, *args, **kwargs)

    def map(self, func: Callable, iterable: List, timeout: float = None) -> List:
        """批量执行"""
        return self._pool.map(func, iterable)

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """执行并返回结果"""
        future = self.submit(func, *args, **kwargs)
        return future.result()

    def shutdown(self, wait: bool = True) -> None:
        """关闭执行器"""
        self._pool.shutdown(wait)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown(wait=True)
        return False

    @property
    def pool(self) -> ThreadPool:
        return self._pool


class PriorityThreadPool:
    """
    优先级线程池

    任务按优先级执行。
    """

    def __init__(self, max_workers: int = 4):
        """初始化优先级线程池"""
        self._max_workers = max_workers
        self._lock = threading.Lock()
        self._state = PoolState.RUNNING

        # 优先级队列（使用堆实现）
        import heapq
        self._priority_queue: List = []  # (priority, counter, task)
        self._counter = 0  # 用于相同优先级的FIFO排序
        self._queue_lock = threading.Lock()
        self._queue_not_empty = threading.Condition(self._queue_lock)

        # 工作线程
        self._workers: List[threading.Thread] = []
        self._create_workers()

        self._logger = Logger()
        self._logger.info(f"优先级线程池创建，工作线程数: {max_workers}")

    def _create_workers(self) -> None:
        """创建工作线程"""
        for i in range(self._max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"PriorityWorker-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)

    def _worker_loop(self) -> None:
        """工作线程主循环"""
        while self._state == PoolState.RUNNING:
            try:
                with self._queue_not_empty:
                    while not self._priority_queue and self._state == PoolState.RUNNING:
                        self._queue_not_empty.wait(timeout=0.5)

                    if not self._priority_queue:
                        continue

                    _, _, task = self._priority_queue.pop(0)

                future, func, args, kwargs = task
                try:
                    result = func(*args, **kwargs)
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)

            except Exception as e:
                self._logger.error(f"工作线程错误: {e}")

    def submit(self, func: Callable, priority: int = 0,
               *args, **kwargs) -> Future:
        """
        提交优先级任务

        Args:
            func: 执行函数
            priority: 优先级（越大越优先）
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Future: 任务未来对象
        """
        if self._state != PoolState.RUNNING:
            raise RuntimeError("线程池已关闭")

        future = Future()

        with self._queue_lock:
            import heapq
            heapq.heappush(
                self._priority_queue,
                (-priority, self._counter, (future, func, args, kwargs))
            )
            self._counter += 1
            self._queue_not_empty.notify()

        return future

    def shutdown(self, wait: bool = True) -> None:
        """关闭线程池"""
        self._state = PoolState.SHUTDOWN

        with self._queue_not_empty:
            self._queue_not_empty.notify_all()

        if wait:
            for worker in self._workers:
                worker.join(timeout=1.0)

        self._state = PoolState.TERMINATED


# 使用示例
if __name__ == "__main__":
    print("=== 线程池演示 ===\n")

    # 示例1: 基本线程池
    print("1. 基本线程池")
    pool = ThreadPool(max_workers=3, name="DemoPool")

    def task(n):
        print(f"  执行任务 {n}...")
        time.sleep(0.5)
        return n * n

    # 提交任务
    futures = [pool.submit(task, i) for i in range(6)]

    # 获取结果
    print("  等待结果...")
    results = [f.result() for f in futures]
    print(f"  结果: {results}")

    print(f"\n  统计: {pool.get_stats()}")

    pool.shutdown()

    # 示例2: 使用上下文管理器
    print("\n2. 使用上下文管理器")
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = executor.map(lambda x: x ** 2, [1, 2, 3, 4, 5])
        print(f"  结果: {results}")

    # 示例3: 优先级线程池
    print("\n3. 优先级线程池")
    priority_pool = PriorityThreadPool(max_workers=2)

    def priority_task(name):
        print(f"  执行 {name}")
        time.sleep(0.3)
        return name

    # 提交不同优先级的任务
    futures = [
        priority_pool.submit(priority_task, priority=1, args=("低优先级",)),
        priority_pool.submit(priority_task, priority=3, args=("高优先级",)),
        priority_pool.submit(priority_task, priority=2, args=("中优先级",)),
    ]

    results = [f.result() for f in futures]
    print(f"  结果: {results}")

    priority_pool.shutdown()

    print("\n所有演示完成！")
