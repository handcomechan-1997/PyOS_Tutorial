"""
死锁检测 - 资源分配图与死锁检测算法

==========================================
        死锁深入学习教程
==========================================

🎯 什么是死锁？
--------------
死锁是指两个或多个进程互相等待对方释放资源，导致所有进程都无法继续执行的状态。

📚 死锁的四个必要条件 (Coffman条件)
----------------------------------
1. 互斥条件 (Mutual Exclusion)
   - 资源不能共享，一次只能被一个进程使用

2. 持有并等待 (Hold and Wait)
   - 进程持有至少一个资源，同时等待获取其他进程持有的资源

3. 不可抢占 (No Preemption)
   - 资源不能被强制抢占，只能由持有者主动释放

4. 循环等待 (Circular Wait)
   - 存在一个进程等待环路，P1等P2，P2等P3，...，Pn等P1

💡 死锁检测方法
---------------
1. 资源分配图法
   - 画出资源分配图
   - 检测是否存在环路

2. 银行家算法
   - 预先检查分配是否安全
   - 只进行安全分配

🔧 处理死锁的策略
-----------------
1. 预防 (Prevention): 破坏四个必要条件之一
2. 避免 (Avoidance): 动态检查，避免不安全状态
3. 检测和恢复 (Detection & Recovery): 允许死锁发生，然后检测并恢复
4. 鸵鸟策略 (Ostrich): 忽略死锁（适用于极少发生的情况）
"""

import threading
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
from enum import Enum
from utils.logger import Logger


class ResourceType(Enum):
    """资源类型"""
    MEMORY = "memory"
    FILE = "file"
    DEVICE = "device"
    SEMAPHORE = "semaphore"
    MUTEX = "mutex"
    CUSTOM = "custom"


class Resource:
    """资源类"""

    _next_id = 1

    def __init__(self, name: str, resource_type: ResourceType,
                 total_instances: int = 1):
        """
        初始化资源

        Args:
            name: 资源名称
            resource_type: 资源类型
            total_instances: 资源实例总数
        """
        self.id = Resource._next_id
        Resource._next_id += 1
        self.name = name
        self.type = resource_type
        self.total_instances = total_instances
        self.available_instances = total_instances

    def __str__(self) -> str:
        return f"Resource({self.name}, type={self.type.value}, available={self.available_instances}/{self.total_instances})"


class Process:
    """进程类（用于死锁检测）"""

    _next_pid = 1

    def __init__(self, name: str):
        self.pid = Process._next_pid
        Process._next_pid += 1
        self.name = name
        self.held_resources: Dict[int, int] = defaultdict(int)  # resource_id -> count
        self.requested_resources: Dict[int, int] = defaultdict(int)

    def __str__(self) -> str:
        return f"Process({self.pid}, name='{self.name}')"


class ResourceAllocationGraph:
    """
    资源分配图 (Resource Allocation Graph, RAG)

    用于可视化资源分配和请求状态，检测死锁。

    图的组成：
    - 进程节点 (圆形)
    - 资源节点 (方形)
    - 分配边 (资源 -> 进程)
    - 请求边 (进程 -> 资源)
    """

    def __init__(self):
        """初始化资源分配图"""
        self._logger = Logger()

        # 节点
        self._processes: Dict[int, Process] = {}
        self._resources: Dict[int, Resource] = {}

        # 边
        # allocation[resource_id][process_id] = count
        self._allocations: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        # requests[process_id][resource_id] = count
        self._requests: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))

        self._lock = threading.Lock()

    def add_process(self, process: Process) -> None:
        """添加进程"""
        with self._lock:
            self._processes[process.pid] = process
            self._logger.debug(f"添加进程: {process}")

    def add_resource(self, resource: Resource) -> None:
        """添加资源"""
        with self._lock:
            self._resources[resource.id] = resource
            self._logger.debug(f"添加资源: {resource}")

    def request_resource(self, process_id: int, resource_id: int,
                        count: int = 1) -> bool:
        """
        进程请求资源

        Args:
            process_id: 进程ID
            resource_id: 资源ID
            count: 请求数量

        Returns:
            bool: 是否成功记录请求
        """
        with self._lock:
            if process_id not in self._processes:
                self._logger.error(f"进程 {process_id} 不存在")
                return False
            if resource_id not in self._resources:
                self._logger.error(f"资源 {resource_id} 不存在")
                return False

            self._requests[process_id][resource_id] += count
            self._logger.debug(f"进程 {process_id} 请求资源 {resource_id} x{count}")
            return True

    def allocate_resource(self, process_id: int, resource_id: int,
                         count: int = 1) -> bool:
        """
        分配资源给进程

        Args:
            process_id: 进程ID
            resource_id: 资源ID
            count: 分配数量

        Returns:
            bool: 是否成功分配
        """
        with self._lock:
            resource = self._resources.get(resource_id)
            if not resource:
                return False

            if resource.available_instances < count:
                self._logger.warning(f"资源 {resource.name} 不足")
                return False

            # 更新资源
            resource.available_instances -= count

            # 更新分配记录
            self._allocations[resource_id][process_id] += count

            # 移除请求
            if self._requests[process_id][resource_id] >= count:
                self._requests[process_id][resource_id] -= count
                if self._requests[process_id][resource_id] == 0:
                    del self._requests[process_id][resource_id]

            # 更新进程持有记录
            process = self._processes[process_id]
            process.held_resources[resource_id] += count

            self._logger.debug(f"分配资源 {resource.name} x{count} 给进程 {process.name}")
            return True

    def release_resource(self, process_id: int, resource_id: int,
                        count: int = 1) -> bool:
        """
        释放资源

        Args:
            process_id: 进程ID
            resource_id: 资源ID
            count: 释放数量

        Returns:
            bool: 是否成功释放
        """
        with self._lock:
            process = self._processes.get(process_id)
            resource = self._resources.get(resource_id)

            if not process or not resource:
                return False

            if self._allocations[resource_id][process_id] < count:
                self._logger.warning(f"进程 {process.name} 未持有足够资源")
                return False

            # 更新分配记录
            self._allocations[resource_id][process_id] -= count
            if self._allocations[resource_id][process_id] == 0:
                del self._allocations[resource_id][process_id]

            # 更新资源
            resource.available_instances += count

            # 更新进程持有记录
            process.held_resources[resource_id] -= count
            if process.held_resources[resource_id] == 0:
                del process.held_resources[resource_id]

            self._logger.debug(f"进程 {process.name} 释放资源 {resource.name} x{count}")
            return True

    def detect_deadlock(self) -> Tuple[bool, List[int]]:
        """
        检测死锁

        使用资源分配图检测是否存在死锁

        Returns:
            Tuple[bool, List[int]]: (是否存在死锁, 死锁进程ID列表)
        """
        with self._lock:
            return self._detect_deadlock_internal()

    def _detect_deadlock_internal(self) -> Tuple[bool, List[int]]:
        """内部死锁检测实现"""
        # 使用银行家算法的变体进行检测
        # Work = Available, Finish = False for all
        work: Dict[int, int] = {}  # resource_id -> available
        finish: Dict[int, bool] = {}  # process_id -> finished

        # 初始化
        for rid, resource in self._resources.items():
            work[rid] = resource.available_instances

        for pid in self._processes:
            # 如果进程没有持有任何资源且没有请求，则认为完成
            if not self._allocations_get_for_process(pid) and not self._requests_get_for_process(pid):
                finish[pid] = True
            else:
                finish[pid] = False

        # 尝试找到可以完成的进程
        changed = True
        while changed:
            changed = False
            for pid in self._processes:
                if finish[pid]:
                    continue

                # 检查进程的请求是否可以被满足
                requests = self._requests_get_for_process(pid)
                can_satisfy = True
                for rid, count in requests.items():
                    if work.get(rid, 0) < count:
                        can_satisfy = False
                        break

                if can_satisfy:
                    # 进程可以完成，释放其持有的资源
                    finish[pid] = True
                    changed = True

                    # 释放资源
                    allocations = self._allocations_get_for_process(pid)
                    for rid, count in allocations.items():
                        work[rid] = work.get(rid, 0) + count

        # 检查是否有未完成的进程
        deadlocked = [pid for pid, f in finish.items() if not f]

        if deadlocked:
            self._logger.warning(f"检测到死锁！涉及进程: {deadlocked}")
        else:
            self._logger.debug("未检测到死锁")

        return len(deadlocked) > 0, deadlocked

    def _allocations_get_for_process(self, pid: int) -> Dict[int, int]:
        """获取进程持有的资源"""
        result = {}
        for rid, allocations in self._allocations.items():
            if pid in allocations and allocations[pid] > 0:
                result[rid] = allocations[pid]
        return result

    def _requests_get_for_process(self, pid: int) -> Dict[int, int]:
        """获取进程请求的资源"""
        return dict(self._requests.get(pid, {}))

    def get_graph_description(self) -> str:
        """获取图的文本描述"""
        lines = ["资源分配图:"]
        lines.append("=" * 50)

        lines.append("\n进程:")
        for pid, process in self._processes.items():
            lines.append(f"  P{pid} ({process.name})")

        lines.append("\n资源:")
        for rid, resource in self._resources.items():
            lines.append(f"  R{rid} ({resource.name}): {resource.available_instances}/{resource.total_instances} 可用")

        lines.append("\n分配边 (资源 -> 进程):")
        for rid, allocations in self._allocations.items():
            resource = self._resources.get(rid)
            for pid, count in allocations.items():
                process = self._processes.get(pid)
                lines.append(f"  R{rid}({resource.name if resource else '?'}) --{count}--> P{pid}({process.name if process else '?'})")

        lines.append("\n请求边 (进程 -> 资源):")
        for pid, requests in self._requests.items():
            process = self._processes.get(pid)
            for rid, count in requests.items():
                resource = self._resources.get(rid)
                lines.append(f"  P{pid}({process.name if process else '?'}) --{count}--> R{rid}({resource.name if resource else '?'})")

        return "\n".join(lines)


class DeadlockDetector:
    """
    死锁检测器

    定期检测系统中的死锁，并提供恢复机制。
    """

    def __init__(self, rag: ResourceAllocationGraph):
        """
        初始化死锁检测器

        Args:
            rag: 资源分配图
        """
        self._rag = rag
        self._logger = Logger()
        self._detection_interval = 5.0  # 检测间隔（秒）
        self._running = False
        self._detection_thread: Optional[threading.Thread] = None

        # 统计
        self._detection_count = 0
        self._deadlock_count = 0
        self._recovery_count = 0

        # 回调
        self._on_deadlock_detected = None
        self._on_recovery = None

    def start_detection(self, interval: float = 5.0) -> None:
        """
        启动定期检测

        Args:
            interval: 检测间隔（秒）
        """
        self._detection_interval = interval
        self._running = True
        self._detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self._detection_thread.start()
        self._logger.info("死锁检测器启动")

    def stop_detection(self) -> None:
        """停止检测"""
        self._running = False
        if self._detection_thread:
            self._detection_thread.join(timeout=2)
        self._logger.info("死锁检测器停止")

    def _detection_loop(self) -> None:
        """检测循环"""
        import time
        while self._running:
            self._detection_count += 1
            has_deadlock, deadlocked = self._rag.detect_deadlock()

            if has_deadlock:
                self._deadlock_count += 1
                if self._on_deadlock_detected:
                    self._on_deadlock_detected(deadlocked)

            time.sleep(self._detection_interval)

    def set_deadlock_callback(self, callback) -> None:
        """设置死锁检测回调"""
        self._on_deadlock_detected = callback

    def set_recovery_callback(self, callback) -> None:
        """设置恢复回调"""
        self._on_recovery = callback

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'detection_count': self._detection_count,
            'deadlock_count': self._deadlock_count,
            'recovery_count': self._recovery_count,
            'running': self._running
        }


# 使用示例
if __name__ == "__main__":
    print("=== 死锁检测演示 ===\n")

    # 创建资源分配图
    rag = ResourceAllocationGraph()

    # 创建进程
    p1 = Process("Process-1")
    p2 = Process("Process-2")
    rag.add_process(p1)
    rag.add_process(p2)

    # 创建资源
    r1 = Resource("Resource-A", ResourceType.MUTEX, 1)
    r2 = Resource("Resource-B", ResourceType.MUTEX, 1)
    rag.add_resource(r1)
    rag.add_resource(r2)

    print("场景1: 正常资源分配")
    rag.request_resource(p1.pid, r1.id)
    rag.allocate_resource(p1.pid, r1.id)
    rag.request_resource(p2.pid, r2.id)
    rag.allocate_resource(p2.pid, r2.id)

    has_deadlock, deadlocked = rag.detect_deadlock()
    print(f"  死锁检测: {'是' if has_deadlock else '否'}")
    print(f"  {rag.get_graph_description()}")

    print("\n场景2: 模拟死锁")
    # P1 持有 R1，请求 R2
    rag.request_resource(p1.pid, r2.id)
    # P2 持有 R2，请求 R1
    rag.request_resource(p2.pid, r1.id)

    has_deadlock, deadlocked = rag.detect_deadlock()
    print(f"  死锁检测: {'是' if has_deadlock else '否'}")
    if has_deadlock:
        print(f"  死锁进程: {deadlocked}")

    print(f"\n  {rag.get_graph_description()}")
