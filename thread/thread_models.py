"""
多线程模型 (Threading Models)

==========================================
      多线程模型深入学习教程
==========================================

🎯 什么是多线程模型？
--------------------
多线程模型描述了用户级线程与内核级线程之间的对应关系。
主要有三种模型：多对一、一对一、多对多。

📚 三种模型对比
---------------

1. 多对一模型 (Many-to-One)
   - 多个用户线程映射到一个内核线程
   - 优点：高效，线程管理在用户空间
   - 缺点：一个线程阻塞，整个进程阻塞
   - 示例：Green threads (早期Java)

2. 一对一模型 (One-to-One)
   - 每个用户线程对应一个内核线程
   - 优点：真正并行，一个线程阻塞不影响其他
   - 缺点：创建开销大
   - 示例：Linux pthreads, Windows threads

3. 多对多模型 (Many-to-Many)
   - 多个用户线程映射到多个内核线程
   - 优点：结合两者优点
   - 缺点：实现复杂
   - 示例：Solaris, IRIX

💡 两级模型
-----------
多对多模型的变体，允许用户线程绑定到特定的内核线程。
"""

import threading
import time
from typing import Callable, Optional, List, Dict, Any
from abc import ABC, abstractmethod
from collections import deque
from enum import Enum
from utils.logger import Logger


class ThreadModelType(Enum):
    """线程模型类型"""
    MANY_TO_ONE = "many_to_one"
    ONE_TO_ONE = "one_to_one"
    MANY_TO_MANY = "many_to_many"


class ThreadModelBase(ABC):
    """线程模型基类"""

    def __init__(self, name: str = ""):
        self._name = name or f"ThreadModel-{id(self)}"
        self._logger = Logger()
        self._user_threads: Dict[int, dict] = {}
        self._next_user_tid = 1

    @abstractmethod
    def create_user_thread(self, target: Callable, args: tuple = ()) -> int:
        """创建用户线程"""
        pass

    @abstractmethod
    def start(self) -> None:
        """启动模型"""
        pass

    @abstractmethod
    def join(self, tid: int, timeout: float = None) -> bool:
        """等待线程完成"""
        pass

    def get_thread_count(self) -> int:
        """获取线程数量"""
        return len(self._user_threads)


class ManyToOneModel(ThreadModelBase):
    """
    多对一模型

    多个用户线程映射到一个内核线程。
    用户线程在用户空间调度，内核只看到一个线程。
    """

    def __init__(self, name: str = ""):
        super().__init__(name or "ManyToOneModel")
        self._ready_queue: deque = deque()
        self._current_thread: Optional[dict] = None
        self._running = False
        self._kernel_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        self._logger.info("多对一线程模型创建")

    def create_user_thread(self, target: Callable, args: tuple = ()) -> int:
        """创建用户线程"""
        with self._lock:
            tid = self._next_user_tid
            self._next_user_tid += 1

            thread_info = {
                'tid': tid,
                'target': target,
                'args': args,
                'state': 'ready',
                'result': None
            }
            self._user_threads[tid] = thread_info
            self._ready_queue.append(thread_info)

            self._logger.debug(f"创建用户线程 {tid}")
            return tid

    def start(self) -> None:
        """启动模型（创建唯一的内核线程）"""
        if self._running:
            return

        self._running = True
        self._kernel_thread = threading.Thread(target=self._run, daemon=True)
        self._kernel_thread.start()
        self._logger.info("多对一模型启动")

    def _run(self) -> None:
        """内核线程执行函数"""
        while self._running:
            thread_info = self._get_next_thread()
            if thread_info is None:
                time.sleep(0.01)
                continue

            self._current_thread = thread_info
            thread_info['state'] = 'running'

            try:
                target = thread_info['target']
                args = thread_info['args']
                thread_info['result'] = target(*args)
                thread_info['state'] = 'terminated'
            except Exception as e:
                self._logger.error(f"线程 {thread_info['tid']} 错误: {e}")
                thread_info['state'] = 'terminated'

            self._current_thread = None

    def _get_next_thread(self) -> Optional[dict]:
        """获取下一个就绪线程"""
        with self._lock:
            while self._ready_queue:
                thread_info = self._ready_queue.popleft()
                if thread_info['state'] == 'ready':
                    return thread_info
            return None

    def join(self, tid: int, timeout: float = None) -> bool:
        """等待线程完成"""
        start = time.time()
        while True:
            with self._lock:
                thread_info = self._user_threads.get(tid)
                if thread_info and thread_info['state'] == 'terminated':
                    return True

            if timeout and (time.time() - start) >= timeout:
                return False
            time.sleep(0.01)

    def stop(self) -> None:
        """停止模型"""
        self._running = False
        if self._kernel_thread:
            self._kernel_thread.join(timeout=1.0)
        self._logger.info("多对一模型停止")

    def get_result(self, tid: int) -> Any:
        """获取线程结果"""
        thread_info = self._user_threads.get(tid)
        return thread_info['result'] if thread_info else None


class OneToOneModel(ThreadModelBase):
    """
    一对一模型

    每个用户线程对应一个内核线程。
    这是最直接的实现方式。
    """

    def __init__(self, name: str = ""):
        super().__init__(name or "OneToOneModel")
        self._kernel_threads: Dict[int, threading.Thread] = {}
        self._lock = threading.Lock()

        self._logger.info("一对一线程模型创建")

    def create_user_thread(self, target: Callable, args: tuple = ()) -> int:
        """创建用户线程（同时创建内核线程）"""
        with self._lock:
            tid = self._next_user_tid
            self._next_user_tid += 1

            thread_info = {
                'tid': tid,
                'target': target,
                'args': args,
                'state': 'new',
                'result': None,
                'exception': None
            }
            self._user_threads[tid] = thread_info

            # 创建对应的内核线程
            def wrapper():
                thread_info['state'] = 'running'
                try:
                    thread_info['result'] = target(*args)
                    thread_info['state'] = 'terminated'
                except Exception as e:
                    thread_info['exception'] = e
                    thread_info['state'] = 'terminated'

            kernel_thread = threading.Thread(target=wrapper)
            self._kernel_threads[tid] = kernel_thread

            self._logger.debug(f"创建用户线程 {tid} 及对应内核线程")
            return tid

    def start(self) -> None:
        """启动所有线程"""
        with self._lock:
            for tid, thread_info in self._user_threads.items():
                kernel_thread = self._kernel_threads.get(tid)
                if kernel_thread and thread_info['state'] == 'new':
                    kernel_thread.start()
                    thread_info['state'] = 'ready'

        self._logger.info("一对一模型启动")

    def start_thread(self, tid: int) -> bool:
        """启动单个线程"""
        with self._lock:
            kernel_thread = self._kernel_threads.get(tid)
            thread_info = self._user_threads.get(tid)

            if kernel_thread and thread_info['state'] == 'new':
                kernel_thread.start()
                thread_info['state'] = 'ready'
                return True
        return False

    def join(self, tid: int, timeout: float = None) -> bool:
        """等待线程完成"""
        kernel_thread = self._kernel_threads.get(tid)
        if kernel_thread:
            kernel_thread.join(timeout=timeout)
            return not kernel_thread.is_alive()
        return False

    def join_all(self, timeout: float = None) -> None:
        """等待所有线程完成"""
        for tid in self._kernel_threads:
            self.join(tid, timeout)

    def get_result(self, tid: int) -> Any:
        """获取线程结果"""
        thread_info = self._user_threads.get(tid)
        return thread_info['result'] if thread_info else None

    def get_active_count(self) -> int:
        """获取活动线程数"""
        count = 0
        for kernel_thread in self._kernel_threads.values():
            if kernel_thread.is_alive():
                count += 1
        return count


class ManyToManyModel(ThreadModelBase):
    """
    多对多模型

    多个用户线程映射到多个内核线程。
    提供更好的灵活性和性能平衡。
    """

    def __init__(self, num_kernel_threads: int = 2, name: str = ""):
        super().__init__(name or "ManyToManyModel")
        self._num_kernel_threads = num_kernel_threads
        self._ready_queue: deque = deque()
        self._kernel_threads: List[threading.Thread] = []
        self._running = False
        self._lock = threading.Lock()
        self._queue_lock = threading.Lock()
        self._queue_condition = threading.Condition(self._queue_lock)

        self._logger.info(f"多对多模型创建，内核线程数: {num_kernel_threads}")

    def create_user_thread(self, target: Callable, args: tuple = (),
                          priority: int = 0) -> int:
        """创建用户线程"""
        with self._lock:
            tid = self._next_user_tid
            self._next_user_tid += 1

            thread_info = {
                'tid': tid,
                'target': target,
                'args': args,
                'priority': priority,
                'state': 'ready',
                'result': None,
                'exception': None
            }
            self._user_threads[tid] = thread_info

            with self._queue_lock:
                self._ready_queue.append(thread_info)
                self._queue_condition.notify()

            self._logger.debug(f"创建用户线程 {tid}")
            return tid

    def start(self) -> None:
        """启动模型"""
        if self._running:
            return

        self._running = True

        # 创建内核线程
        for i in range(self._num_kernel_threads):
            kernel_thread = threading.Thread(
                target=self._kernel_thread_run,
                args=(i,),
                daemon=True
            )
            kernel_thread.start()
            self._kernel_threads.append(kernel_thread)

        self._logger.info("多对多模型启动")

    def _kernel_thread_run(self, kid: int) -> None:
        """内核线程执行函数"""
        self._logger.debug(f"内核线程 {kid} 启动")

        while self._running:
            thread_info = self._get_next_user_thread()

            if thread_info is None:
                time.sleep(0.01)
                continue

            thread_info['state'] = 'running'

            try:
                target = thread_info['target']
                args = thread_info['args']
                thread_info['result'] = target(*args)
                thread_info['state'] = 'terminated'
            except Exception as e:
                thread_info['exception'] = e
                thread_info['state'] = 'terminated'

    def _get_next_user_thread(self) -> Optional[dict]:
        """获取下一个用户线程"""
        with self._queue_condition:
            while self._running and not self._ready_queue:
                self._queue_condition.wait(timeout=0.5)

            if not self._ready_queue:
                return None

            # 按优先级选择
            best = None
            best_idx = -1
            for i, info in enumerate(self._ready_queue):
                if info['state'] == 'ready':
                    if best is None or info['priority'] > best['priority']:
                        best = info
                        best_idx = i

            if best is not None:
                del list(self._ready_queue)[best_idx]
            return best

    def join(self, tid: int, timeout: float = None) -> bool:
        """等待线程完成"""
        start = time.time()
        while True:
            with self._lock:
                thread_info = self._user_threads.get(tid)
                if thread_info and thread_info['state'] == 'terminated':
                    return True

            if timeout and (time.time() - start) >= timeout:
                return False
            time.sleep(0.01)

    def stop(self) -> None:
        """停止模型"""
        self._running = False

        with self._queue_condition:
            self._queue_condition.notify_all()

        for kernel_thread in self._kernel_threads:
            kernel_thread.join(timeout=1.0)

        self._logger.info("多对多模型停止")

    def get_result(self, tid: int) -> Any:
        """获取线程结果"""
        thread_info = self._user_threads.get(tid)
        return thread_info['result'] if thread_info else None

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            states = {'ready': 0, 'running': 0, 'terminated': 0}
            for info in self._user_threads.values():
                states[info['state']] = states.get(info['state'], 0) + 1

            return {
                'model_type': 'many_to_many',
                'kernel_threads': self._num_kernel_threads,
                'user_threads': len(self._user_threads),
                'ready_queue_size': len(self._ready_queue),
                'thread_states': states
            }


# 使用示例
if __name__ == "__main__":
    print("=== 多线程模型演示 ===\n")

    def task(name, duration=0.5):
        print(f"  [{name}] 开始执行")
        time.sleep(duration)
        print(f"  [{name}] 执行完成")
        return f"{name}_result"

    # 示例1: 多对一模型
    print("1. 多对一模型")
    mto = ManyToOneModel()

    t1 = mto.create_user_thread(task, ("Task-1", 0.3))
    t2 = mto.create_user_thread(task, ("Task-2", 0.3))
    t3 = mto.create_user_thread(task, ("Task-3", 0.3))

    mto.start()
    time.sleep(2)  # 等待执行完成

    print(f"  结果: {mto.get_result(t1)}, {mto.get_result(t2)}, {mto.get_result(t3)}")
    mto.stop()

    # 示例2: 一对一模型
    print("\n2. 一对一模型")
    oto = OneToOneModel()

    t1 = oto.create_user_thread(task, ("Task-A", 0.2))
    t2 = oto.create_user_thread(task, ("Task-B", 0.2))
    t3 = oto.create_user_thread(task, ("Task-C", 0.2))

    oto.start()
    oto.join_all()

    print(f"  结果: {oto.get_result(t1)}, {oto.get_result(t2)}, {oto.get_result(t3)}")

    # 示例3: 多对多模型
    print("\n3. 多对多模型")
    mtm = ManyToManyModel(num_kernel_threads=2)

    t1 = mtm.create_user_thread(task, ("Task-X", 0.3), priority=1)
    t2 = mtm.create_user_thread(task, ("Task-Y", 0.3), priority=2)
    t3 = mtm.create_user_thread(task, ("Task-Z", 0.3), priority=0)
    t4 = mtm.create_user_thread(task, ("Task-W", 0.3), priority=3)

    mtm.start()
    time.sleep(2)

    print(f"  统计: {mtm.get_stats()}")
    mtm.stop()

    print("\n所有演示完成！")
