"""
银行家算法 - 死锁避免的经典算法

==========================================
       银行家算法深入学习教程
==========================================

🎯 什么是银行家算法？
--------------------
银行家算法是一种死锁避免算法，由 Edsger Dijkstra 提出。
名字来源于银行系统的借贷策略：银行不会借出超过其储备的资金，
确保在任何时候都能满足所有客户的最大需求。

📚 核心概念
-----------
1. 可用资源 (Available): 当前可用的各类资源数量
2. 最大需求 (Max): 每个进程对各类资源的最大需求
3. 已分配 (Allocation): 已分配给每个进程的各类资源数量
4. 需求矩阵 (Need): 每个进程还需要多少资源
   Need[i][j] = Max[i][j] - Allocation[i][j]

💡 安全状态
-----------
系统处于安全状态，当且仅当存在一个安全序列 <P1, P2, ..., Pn>，
使得对于每个 Pi，它仍然需要的资源可以被当前可用资源加上
所有 Pj (j < i) 持有的资源所满足。

🔧 算法步骤
-----------
1. 初始化：设置 Available, Max, Allocation, Need

2. 资源请求算法：
   a) 如果 Request[i] > Need[i]，出错
   b) 如果 Request[i] > Available，等待
   c) 试探性分配
   d) 执行安全性算法
   e) 如果安全，正式分配；否则回滚

3. 安全性算法：
   a) Work = Available, Finish[i] = false
   b) 找到满足 Finish[i]=false 且 Need[i] <= Work 的进程
   c) Work += Allocation[i], Finish[i] = true
   d) 重复直到所有 Finish 为 true 或无法继续
"""

import threading
from typing import Dict, List, Optional, Tuple
from copy import deepcopy
from utils.logger import Logger


class BankersAlgorithm:
    """
    银行家算法实现

    用于避免死锁，确保系统始终处于安全状态。
    """

    def __init__(self, resource_types: List[str], total_resources: List[int]):
        """
        初始化银行家算法

        Args:
            resource_types: 资源类型列表，如 ['A', 'B', 'C']
            total_resources: 各类资源的总数，如 [10, 5, 7]
        """
        if len(resource_types) != len(total_resources):
            raise ValueError("资源类型数量与资源总数不匹配")

        self._resource_types = resource_types
        self._num_resources = len(resource_types)
        self._total = total_resources[:]

        # 可用资源
        self._available = total_resources[:]

        # 进程管理
        self._processes: Dict[str, dict] = {}  # pid -> {max, allocation, need}

        self._lock = threading.Lock()
        self._logger = Logger()

        # 统计
        self._request_count = 0
        self._success_count = 0
        self._rejection_count = 0

        self._logger.info(f"银行家算法初始化: 资源类型={resource_types}, 总数={total_resources}")

    def add_process(self, pid: str, max_demand: List[int]) -> bool:
        """
        添加进程

        Args:
            pid: 进程ID
            max_demand: 最大需求矩阵行

        Returns:
            bool: 是否成功添加
        """
        if len(max_demand) != self._num_resources:
            self._logger.error(f"进程 {pid} 的最大需求维度不正确")
            return False

        with self._lock:
            if pid in self._processes:
                self._logger.error(f"进程 {pid} 已存在")
                return False

            # 检查最大需求是否超过总资源
            for i, demand in enumerate(max_demand):
                if demand > self._total[i]:
                    self._logger.error(f"进程 {pid} 对资源 {self._resource_types[i]} 的最大需求超过总数")
                    return False

            self._processes[pid] = {
                'max': max_demand[:],
                'allocation': [0] * self._num_resources,
                'need': max_demand[:]
            }

            self._logger.info(f"添加进程 {pid}, 最大需求: {max_demand}")
            return True

    def remove_process(self, pid: str) -> bool:
        """
        移除进程（释放所有资源）

        Args:
            pid: 进程ID

        Returns:
            bool: 是否成功移除
        """
        with self._lock:
            if pid not in self._processes:
                return False

            # 释放资源
            allocation = self._processes[pid]['allocation']
            for i in range(self._num_resources):
                self._available[i] += allocation[i]

            del self._processes[pid]
            self._logger.info(f"移除进程 {pid}")
            return True

    def request_resources(self, pid: str, request: List[int]) -> Tuple[bool, str]:
        """
        请求资源

        Args:
            pid: 进程ID
            request: 请求的资源数量列表

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        self._request_count += 1

        if len(request) != self._num_resources:
            return False, "请求维度不正确"

        with self._lock:
            if pid not in self._processes:
                return False, f"进程 {pid} 不存在"

            process = self._processes[pid]

            # 步骤1: 检查请求是否超过最大需求
            for i in range(self._num_resources):
                if request[i] > process['need'][i]:
                    self._rejection_count += 1
                    return False, f"请求超过声明的最大需求 (资源 {self._resource_types[i]})"

            # 步骤2: 检查是否有足够可用资源
            for i in range(self._num_resources):
                if request[i] > self._available[i]:
                    # 进程需要等待
                    self._logger.debug(f"进程 {pid} 等待资源 {self._resource_types[i]}")
                    return False, "资源不足，进程需要等待"

            # 步骤3: 试探性分配
            # 保存状态用于回滚
            saved_available = self._available[:]
            saved_allocation = process['allocation'][:]
            saved_need = process['need'][:]

            # 执行试探性分配
            for i in range(self._num_resources):
                self._available[i] -= request[i]
                process['allocation'][i] += request[i]
                process['need'][i] -= request[i]

            # 步骤4: 安全性检查
            is_safe, safe_sequence = self._safety_check()

            if is_safe:
                # 安全，正式分配
                self._success_count += 1
                self._logger.info(f"进程 {pid} 获取资源 {request}, 安全序列: {safe_sequence}")
                return True, f"分配成功，安全序列: {safe_sequence}"
            else:
                # 不安全，回滚
                self._available = saved_available
                process['allocation'] = saved_allocation
                process['need'] = saved_need

                self._rejection_count += 1
                self._logger.warning(f"进程 {pid} 请求 {request} 会导致不安全状态，拒绝")
                return False, "分配会导致不安全状态，请求被拒绝"

    def release_resources(self, pid: str, release: List[int]) -> Tuple[bool, str]:
        """
        释放资源

        Args:
            pid: 进程ID
            release: 释放的资源数量列表

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        if len(release) != self._num_resources:
            return False, "释放维度不正确"

        with self._lock:
            if pid not in self._processes:
                return False, f"进程 {pid} 不存在"

            process = self._processes[pid]

            # 检查释放量是否超过持有量
            for i in range(self._num_resources):
                if release[i] > process['allocation'][i]:
                    return False, f"释放量超过持有量 (资源 {self._resource_types[i]})"

            # 执行释放
            for i in range(self._num_resources):
                process['allocation'][i] -= release[i]
                process['need'][i] += release[i]
                self._available[i] += release[i]

            self._logger.info(f"进程 {pid} 释放资源 {release}")
            return True, "释放成功"

    def _safety_check(self) -> Tuple[bool, List[str]]:
        """
        安全性算法

        Returns:
            Tuple[bool, List[str]]: (是否安全, 安全序列)
        """
        # 初始化
        work = self._available[:]
        finish = {pid: False for pid in self._processes}
        safe_sequence = []

        # 尝试找到安全序列
        while True:
            found = False
            for pid, process in self._processes.items():
                if not finish[pid]:
                    # 检查 Need <= Work
                    can_allocate = True
                    for i in range(self._num_resources):
                        if process['need'][i] > work[i]:
                            can_allocate = False
                            break

                    if can_allocate:
                        # 可以满足这个进程
                        for i in range(self._num_resources):
                            work[i] += process['allocation'][i]
                        finish[pid] = True
                        safe_sequence.append(pid)
                        found = True

            if not found:
                break

        # 检查是否所有进程都完成
        all_finished = all(finish.values())
        return all_finished, safe_sequence

    def get_state(self) -> dict:
        """
        获取当前系统状态

        Returns:
            dict: 系统状态信息
        """
        with self._lock:
            is_safe, safe_sequence = self._safety_check()

            return {
                'resource_types': self._resource_types,
                'total': self._total,
                'available': self._available,
                'processes': deepcopy(self._processes),
                'is_safe': is_safe,
                'safe_sequence': safe_sequence if is_safe else []
            }

    def print_state(self) -> None:
        """打印当前系统状态"""
        state = self.get_state()

        print("\n" + "=" * 70)
        print("银行家算法状态")
        print("=" * 70)

        print(f"\n资源类型: {state['resource_types']}")
        print(f"总资源:   {state['total']}")
        print(f"可用资源: {state['available']}")

        print("\n进程状态:")
        print("-" * 70)
        print(f"{'进程':<10} {'最大需求':<20} {'已分配':<20} {'需求':<20}")
        print("-" * 70)

        for pid, proc in state['processes'].items():
            print(f"{pid:<10} {str(proc['max']):<20} {str(proc['allocation']):<20} {str(proc['need']):<20}")

        print("-" * 70)
        print(f"系统状态: {'安全' if state['is_safe'] else '不安全'}")
        if state['is_safe']:
            print(f"安全序列: {' -> '.join(state['safe_sequence'])}")
        print("=" * 70)

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'request_count': self._request_count,
            'success_count': self._success_count,
            'rejection_count': self._rejection_count,
            'process_count': len(self._processes)
        }


class ResourceManager:
    """
    资源管理器

    提供更高层次的资源管理接口，集成银行家算法。
    """

    def __init__(self, resource_types: List[str], total_resources: List[int]):
        """
        初始化资源管理器

        Args:
            resource_types: 资源类型列表
            total_resources: 各类资源总数
        """
        self._banker = BankersAlgorithm(resource_types, total_resources)
        self._logger = Logger()
        self._process_counter = 0

    def create_process(self, max_demand: List[int]) -> str:
        """
        创建新进程

        Args:
            max_demand: 最大资源需求

        Returns:
            str: 进程ID
        """
        self._process_counter += 1
        pid = f"P{self._process_counter}"
        self._banker.add_process(pid, max_demand)
        return pid

    def destroy_process(self, pid: str) -> bool:
        """销毁进程"""
        return self._banker.remove_process(pid)

    def allocate(self, pid: str, request: List[int]) -> Tuple[bool, str]:
        """分配资源"""
        return self._banker.request_resources(pid, request)

    def deallocate(self, pid: str, release: List[int]) -> Tuple[bool, str]:
        """释放资源"""
        return self._banker.release_resources(pid, release)

    def get_banker(self) -> BankersAlgorithm:
        """获取银行家算法实例"""
        return self._banker


# 使用示例
if __name__ == "__main__":
    print("=== 银行家算法演示 ===\n")

    # 经典教材示例
    # 5个进程，3类资源
    banker = BankersAlgorithm(
        resource_types=['A', 'B', 'C'],
        total_resources=[10, 5, 7]
    )

    # 添加进程及其最大需求
    processes = {
        'P0': [7, 5, 3],
        'P1': [3, 2, 2],
        'P2': [9, 0, 2],
        'P3': [2, 2, 2],
        'P4': [4, 3, 3]
    }

    for pid, max_demand in processes.items():
        banker.add_process(pid, max_demand)

    # 初始分配（模拟已分配状态）
    initial_allocations = {
        'P0': [0, 1, 0],
        'P1': [2, 0, 0],
        'P2': [3, 0, 2],
        'P3': [2, 1, 1],
        'P4': [0, 0, 2]
    }

    # 手动设置初始分配（绕过请求检查）
    for pid, alloc in initial_allocations.items():
        process = banker._processes[pid]
        for i in range(len(alloc)):
            banker._available[i] -= alloc[i]
            process['allocation'][i] = alloc[i]
            process['need'][i] -= alloc[i]

    print("初始状态:")
    banker.print_state()

    # 测试安全请求
    print("\n测试1: P1 请求 [1, 0, 2]")
    success, msg = banker.request_resources('P1', [1, 0, 2])
    print(f"  结果: {success}, {msg}")
    banker.print_state()

    # 测试不安全请求
    print("\n测试2: P4 请求 [3, 3, 0]")
    success, msg = banker.request_resources('P4', [3, 3, 0])
    print(f"  结果: {success}, {msg}")

    # 测试超过需求的请求
    print("\n测试3: P0 请求 [0, 2, 0]（超过需求）")
    success, msg = banker.request_resources('P0', [0, 2, 0])
    print(f"  结果: {success}, {msg}")

    # 测试资源不足
    print("\n测试4: P0 请求 [0, 2, 0]（等待）")
    success, msg = banker.request_resources('P0', [0, 2, 0])
    print(f"  结果: {success}, {msg}")

    print(f"\n统计: {banker.get_stats()}")
