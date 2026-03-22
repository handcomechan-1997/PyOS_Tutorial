"""
死锁预防 - 破坏死锁的必要条件

==========================================
       死锁预防策略深入学习
==========================================

🎯 死锁预防的核心思想
--------------------
通过破坏死锁的四个必要条件之一，从根本上防止死锁发生。

📚 四种预防策略
---------------

1. 破坏互斥条件
   - 让资源可以共享（不总是可行）
   - 例如：只读文件可以共享

2. 破坏持有并等待条件
   - 方案A：进程开始时一次性申请所有资源
   - 方案B：进程在请求新资源前释放所有已持有资源
   - 缺点：资源利用率低，可能饥饿

3. 破坏不可抢占条件
   - 允许抢占资源
   - 保存状态，稍后恢复
   - 适用于可以保存/恢复状态的资源

4. 破坏循环等待条件
   - 资源有序分配：给资源编号，按顺序申请
   - 例如：必须先申请小编号资源，再申请大编号资源
   - 最常用的预防策略

💡 实际应用
-----------
- 数据库系统：事务锁
- 操作系统：资源编号
- 嵌入式系统：静态资源分配
"""

import threading
from typing import Dict, List, Optional, Set
from enum import Enum
from collections import defaultdict
from utils.logger import Logger


class PreventionStrategy(Enum):
    """预防策略"""
    HOLD_AND_WAIT = "hold_and_wait"    # 破坏持有并等待
    NO_PREEMPTION = "no_preemption"    # 破坏不可抢占
    CIRCULAR_WAIT = "circular_wait"    # 破坏循环等待（资源有序）


class ManagedResource:
    """被管理的资源"""

    def __init__(self, resource_id: int, name: str, total: int = 1,
                 order: int = 0, preemptable: bool = False):
        """
        初始化资源

        Args:
            resource_id: 资源ID
            name: 资源名称
            total: 总实例数
            order: 资源序号（用于有序分配）
            preemptable: 是否可抢占
        """
        self.id = resource_id
        self.name = name
        self.total = total
        self.available = total
        self.order = order
        self.preemptable = preemptable

        # 持有者
        self._holders: Dict[int, int] = {}  # pid -> count

    def allocate(self, pid: int, count: int = 1) -> bool:
        """分配资源"""
        if self.available < count:
            return False
        self.available -= count
        self._holders[pid] = self._holders.get(pid, 0) + count
        return True

    def release(self, pid: int, count: int = 1) -> bool:
        """释放资源"""
        if self._holders.get(pid, 0) < count:
            return False
        self._holders[pid] -= count
        if self._holders[pid] == 0:
            del self._holders[pid]
        self.available += count
        return True

    def preempt(self, pid: int, count: int = 1) -> bool:
        """抢占资源"""
        if not self.preemptable:
            return False
        return self.release(pid, count)


class DeadlockPrevention:
    """
    死锁预防管理器

    实现多种死锁预防策略。
    """

    def __init__(self, strategy: PreventionStrategy = PreventionStrategy.CIRCULAR_WAIT):
        """
        初始化死锁预防管理器

        Args:
            strategy: 预防策略
        """
        self._strategy = strategy
        self._logger = Logger()
        self._lock = threading.Lock()

        # 资源管理
        self._resources: Dict[int, ManagedResource] = {}
        self._next_resource_id = 1

        # 进程状态
        # 每个进程持有的资源
        self._process_resources: Dict[int, Set[int]] = defaultdict(set)
        # 进程正在等待的资源
        self._process_waiting: Dict[int, int] = {}  # pid -> resource_id

        # 统计
        self._allocation_count = 0
        self._rejection_count = 0
        self._preemption_count = 0

        self._logger.info(f"死锁预防管理器创建，策略: {strategy.value}")

    def register_resource(self, name: str, total: int = 1,
                         order: int = 0, preemptable: bool = False) -> int:
        """
        注册资源

        Args:
            name: 资源名称
            total: 总实例数
            order: 资源序号（用于有序分配策略）
            preemptable: 是否可抢占

        Returns:
            int: 资源ID
        """
        with self._lock:
            rid = self._next_resource_id
            self._next_resource_id += 1
            self._resources[rid] = ManagedResource(
                rid, name, total, order, preemptable
            )
            self._logger.info(f"注册资源: {name}, ID: {rid}, 序号: {order}, 可抢占: {preemptable}")
            return rid

    def request_resource(self, pid: int, resource_id: int,
                        count: int = 1) -> bool:
        """
        请求资源

        根据预防策略决定是否允许请求

        Args:
            pid: 进程ID
            resource_id: 资源ID
            count: 请求数量

        Returns:
            bool: 是否成功获取
        """
        with self._lock:
            resource = self._resources.get(resource_id)
            if not resource:
                self._logger.error(f"资源 {resource_id} 不存在")
                return False

            # 检查是否违反策略
            if not self._check_strategy(pid, resource_id):
                self._rejection_count += 1
                return False

            # 尝试分配
            if resource.available >= count:
                resource.allocate(pid, count)
                self._process_resources[pid].add(resource_id)
                self._allocation_count += 1
                self._logger.debug(f"进程 {pid} 获取资源 {resource.name}")
                return True
            else:
                # 资源不足
                if self._strategy == PreventionStrategy.NO_PREEMPTION and resource.preemptable:
                    # 尝试抢占
                    return self._try_preempt(pid, resource, count)

                self._rejection_count += 1
                self._logger.debug(f"进程 {pid} 请求资源 {resource.name} 失败（资源不足）")
                return False

    def _check_strategy(self, pid: int, resource_id: int) -> bool:
        """检查是否违反预防策略"""
        if self._strategy == PreventionStrategy.HOLD_AND_WAIT:
            return self._check_hold_and_wait(pid)

        elif self._strategy == PreventionStrategy.CIRCULAR_WAIT:
            return self._check_circular_wait(pid, resource_id)

        return True

    def _check_hold_and_wait(self, pid: int) -> bool:
        """
        检查持有并等待条件

        策略：如果进程已持有资源，不允许再请求新资源
        必须先释放所有资源，再重新申请
        """
        if pid in self._process_resources and self._process_resources[pid]:
            self._logger.warning(f"进程 {pid} 已持有资源，违反持有并等待策略")
            return False
        return True

    def _check_circular_wait(self, pid: int, resource_id: int) -> bool:
        """
        检查循环等待条件

        策略：资源有序分配
        进程只能按资源序号递增的顺序请求资源
        """
        resource = self._resources[resource_id]
        new_order = resource.order

        # 检查已持有资源的序号
        for held_rid in self._process_resources.get(pid, set()):
            held_resource = self._resources.get(held_rid)
            if held_resource and held_resource.order >= new_order:
                self._logger.warning(
                    f"进程 {pid} 违反有序分配策略: "
                    f"已持有序号 {held_resource.order}，请求序号 {new_order}"
                )
                return False

        return True

    def _try_preempt(self, pid: int, resource: ManagedResource,
                    count: int) -> bool:
        """尝试抢占资源"""
        # 找到持有该资源的进程
        for holder_pid in list(resource._holders.keys()):
            if resource.preempt(holder_pid, count):
                self._preemption_count += 1
                self._logger.info(f"抢占进程 {holder_pid} 的资源 {resource.name}")

                # 分配给请求者
                resource.allocate(pid, count)
                self._process_resources[pid].add(resource.id)
                self._allocation_count += 1
                return True

        return False

    def release_resource(self, pid: int, resource_id: int,
                        count: int = 1) -> bool:
        """
        释放资源

        Args:
            pid: 进程ID
            resource_id: 资源ID
            count: 释放数量

        Returns:
            bool: 是否成功释放
        """
        with self._lock:
            resource = self._resources.get(resource_id)
            if not resource:
                return False

            if resource.release(pid, count):
                if resource_id in self._process_resources.get(pid, set()):
                    self._process_resources[pid].discard(resource_id)
                self._logger.debug(f"进程 {pid} 释放资源 {resource.name}")
                return True

            return False

    def release_all_resources(self, pid: int) -> None:
        """释放进程持有的所有资源"""
        with self._lock:
            for rid in list(self._process_resources.get(pid, set())):
                resource = self._resources.get(rid)
                if resource:
                    resource.release(pid, resource._holders.get(pid, 0))
            self._process_resources[pid].clear()
            self._logger.debug(f"进程 {pid} 释放所有资源")

    def get_process_resources(self, pid: int) -> List[str]:
        """获取进程持有的资源"""
        with self._lock:
            result = []
            for rid in self._process_resources.get(pid, set()):
                resource = self._resources.get(rid)
                if resource:
                    result.append(resource.name)
            return result

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            return {
                'strategy': self._strategy.value,
                'resource_count': len(self._resources),
                'allocation_count': self._allocation_count,
                'rejection_count': self._rejection_count,
                'preemption_count': self._preemption_count
            }


class OrderedResourceAllocator:
    """
    有序资源分配器

    实现资源有序分配策略，破坏循环等待条件。
    这是最实用的死锁预防方法。
    """

    def __init__(self):
        """初始化有序资源分配器"""
        self._logger = Logger()
        self._lock = threading.Lock()

        # 资源按序号排序
        self._resources_by_order: Dict[int, ManagedResource] = {}
        self._resources_by_id: Dict[int, ManagedResource] = {}

        self._next_id = 1

    def register_resource(self, name: str, order: int, total: int = 1) -> int:
        """
        注册资源

        Args:
            name: 资源名称
            order: 资源序号（必须唯一）
            total: 总实例数

        Returns:
            int: 资源ID
        """
        with self._lock:
            if order in self._resources_by_order:
                raise ValueError(f"序号 {order} 已被使用")

            rid = self._next_id
            self._next_id += 1

            resource = ManagedResource(rid, name, total, order)
            self._resources_by_order[order] = resource
            self._resources_by_id[rid] = resource

            self._logger.info(f"注册资源: {name}, 序号: {order}")
            return rid

    def request_multiple(self, pid: int, resource_ids: List[int],
                        counts: Optional[List[int]] = None) -> bool:
        """
        请求多个资源

        自动按序号排序后依次请求，避免死锁

        Args:
            pid: 进程ID
            resource_ids: 资源ID列表
            counts: 对应的请求数量

        Returns:
            bool: 是否全部成功
        """
        if counts is None:
            counts = [1] * len(resource_ids)

        with self._lock:
            # 获取资源并按序号排序
            resources = []
            for rid, count in zip(resource_ids, counts):
                resource = self._resources_by_id.get(rid)
                if resource:
                    resources.append((resource.order, resource, count))

            resources.sort(key=lambda x: x[0])

            # 按顺序请求
            acquired = []
            for _, resource, count in resources:
                if resource.available >= count:
                    resource.allocate(pid, count)
                    acquired.append(resource)
                else:
                    # 失败，回滚
                    for r in acquired:
                        r.release(pid)
                    self._logger.warning(f"进程 {pid} 请求资源失败，已回滚")
                    return False

            self._logger.debug(f"进程 {pid} 成功获取 {len(acquired)} 个资源")
            return True

    def release_multiple(self, pid: int, resource_ids: List[int],
                        counts: Optional[List[int]] = None) -> None:
        """释放多个资源"""
        if counts is None:
            counts = [1] * len(resource_ids)

        with self._lock:
            for rid, count in zip(resource_ids, counts):
                resource = self._resources_by_id.get(rid)
                if resource:
                    resource.release(pid, count)


# 使用示例
if __name__ == "__main__":
    print("=== 死锁预防演示 ===\n")

    # 示例1: 有序分配策略
    print("1. 有序分配策略（破坏循环等待）")
    dp = DeadlockPrevention(strategy=PreventionStrategy.CIRCULAR_WAIT)

    # 注册资源（按序号）
    r1 = dp.register_resource("打印机", order=1)
    r2 = dp.register_resource("扫描仪", order=2)
    r3 = dp.register_resource("绘图仪", order=3)

    # 进程1按顺序请求
    print("  进程1按顺序请求资源...")
    print(f"    请求打印机: {dp.request_resource(1, r1)}")
    print(f"    请求扫描仪: {dp.request_resource(1, r2)}")

    # 进程2违反顺序请求
    print("  进程2违反顺序请求...")
    print(f"    先请求扫描仪: {dp.request_resource(2, r2)}")  # 应该失败

    print(f"\n  统计: {dp.get_stats()}")

    # 示例2: 持有并等待策略
    print("\n2. 持有并等待策略")
    dp2 = DeadlockPrevention(strategy=PreventionStrategy.HOLD_AND_WAIT)

    r1 = dp2.register_resource("资源A")
    r2 = dp2.register_resource("资源B")

    print(f"  进程1请求资源A: {dp2.request_resource(1, r1)}")
    print(f"  进程1再请求资源B: {dp2.request_resource(1, r2)}")  # 应该失败

    print(f"\n  统计: {dp2.get_stats()}")

    # 示例3: 有序资源分配器
    print("\n3. 有序资源分配器（批量请求）")
    allocator = OrderedResourceAllocator()

    r1 = allocator.register_resource("磁盘", order=1)
    r2 = allocator.register_resource("磁带", order=2)
    r3 = allocator.register_resource("打印机", order=3)

    # 无论传入什么顺序，都会按序号排序后请求
    print(f"  进程1请求 [打印机, 磁盘, 磁带]: {allocator.request_multiple(1, [r3, r1, r2])}")

    print("\n  所有演示完成！")
