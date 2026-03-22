"""
I/O调度器 - I/O请求调度算法

==========================================
       I/O调度深入学习教程
==========================================

🎯 什么是I/O调度？
-----------------
I/O调度器负责决定I/O请求的执行顺序，优化磁盘访问性能。

📚 为什么需要I/O调度？
---------------------
1. 磁盘寻道是机械操作，耗时较长
2. 优化请求顺序可以减少寻道时间
3. 避免某些请求饥饿
4. 提高整体I/O吞吐量

💡 常见I/O调度算法
------------------
1. FCFS (先来先服务)
   - 最简单，按请求顺序执行
   - 公平但效率低

2. SSTF (最短寻道时间优先)
   - 选择离当前位置最近的请求
   - 效率高但可能导致饥饿

3. SCAN (电梯算法)
   - 磁头来回扫描，处理沿途请求
   - 公平，不会饥饿

4. C-SCAN (循环扫描)
   - 单向扫描，到头后返回起点
   - 更均匀的等待时间

5. LOOK / C-LOOK
   - SCAN/C-SCAN的优化版本
   - 只扫描到最远的请求，不到磁盘边界
"""

import time
from typing import List, Optional, Callable
from enum import Enum
from collections import deque
from dataclasses import dataclass, field
from utils.logger import Logger


class IOType(Enum):
    """I/O类型"""
    READ = "read"
    WRITE = "write"


class IOSchedulerType(Enum):
    """I/O调度算法类型"""
    FCFS = "fcfs"
    SSTF = "sstf"
    SCAN = "scan"
    C_SCAN = "c_scan"
    LOOK = "look"
    C_LOOK = "c_look"


@dataclass
class IORequest:
    """I/O请求"""
    request_id: int
    block_number: int      # 目标块号
    io_type: IOType        # 读写类型
    data_size: int         # 数据大小
    process_id: int        # 请求进程ID
    arrival_time: float    # 到达时间
    callback: Optional[Callable] = None  # 完成回调

    # 执行信息
    start_time: Optional[float] = None
    finish_time: Optional[float] = None
    seek_distance: int = 0  # 寻道距离

    @property
    def waiting_time(self) -> float:
        """等待时间"""
        if self.start_time:
            return self.start_time - self.arrival_time
        return time.time() - self.arrival_time

    @property
    def service_time(self) -> float:
        """服务时间"""
        if self.start_time and self.finish_time:
            return self.finish_time - self.start_time
        return 0.0


class IOScheduler:
    """
    I/O调度器

    实现多种I/O调度算法。
    """

    _next_request_id = 1

    def __init__(self, scheduler_type: IOSchedulerType = IOSchedulerType.LOOK,
                 total_blocks: int = 1000, initial_position: int = 0):
        """
        初始化I/O调度器

        Args:
            scheduler_type: 调度算法类型
            total_blocks: 总块数
            initial_position: 初始磁头位置
        """
        self._type = scheduler_type
        self._total_blocks = total_blocks
        self._current_position = initial_position
        self._direction = 1  # 1: 向上, -1: 向下
        self._logger = Logger()

        # 请求队列
        self._pending_requests: List[IORequest] = []
        self._completed_requests: List[IORequest] = []

        # 统计
        self._total_seek = 0
        self._total_requests = 0
        self._total_wait_time = 0.0

        self._logger.info(f"I/O调度器创建，算法: {scheduler_type.value}")

    def submit_request(self, block_number: int, io_type: IOType,
                      data_size: int, process_id: int,
                      callback: Callable = None) -> int:
        """
        提交I/O请求

        Args:
            block_number: 目标块号
            io_type: 读写类型
            data_size: 数据大小
            process_id: 进程ID
            callback: 完成回调

        Returns:
            int: 请求ID
        """
        request = IORequest(
            request_id=IOScheduler._next_request_id,
            block_number=block_number,
            io_type=io_type,
            data_size=data_size,
            process_id=process_id,
            arrival_time=time.time(),
            callback=callback
        )
        IOScheduler._next_request_id += 1

        self._pending_requests.append(request)
        self._total_requests += 1

        self._logger.debug(f"接收I/O请求 {request.request_id}: 块 {block_number}")
        return request.request_id

    def get_next_request(self) -> Optional[IORequest]:
        """
        获取下一个要执行的请求

        Returns:
            Optional[IORequest]: 下一个请求，如果队列为空返回None
        """
        if not self._pending_requests:
            return None

        if self._type == IOSchedulerType.FCFS:
            return self._fcfs()
        elif self._type == IOSchedulerType.SSTF:
            return self._sstf()
        elif self._type == IOSchedulerType.SCAN:
            return self._scan()
        elif self._type == IOSchedulerType.C_SCAN:
            return self._c_scan()
        elif self._type == IOSchedulerType.LOOK:
            return self._look()
        elif self._type == IOSchedulerType.C_LOOK:
            return self._c_look()
        else:
            return self._fcfs()

    def _fcfs(self) -> Optional[IORequest]:
        """FCFS: 先来先服务"""
        return self._pending_requests.pop(0)

    def _sstf(self) -> Optional[IORequest]:
        """SSTF: 最短寻道时间优先"""
        if not self._pending_requests:
            return None

        # 找到距离当前位置最近的请求
        min_distance = float('inf')
        min_index = 0

        for i, req in enumerate(self._pending_requests):
            distance = abs(req.block_number - self._current_position)
            if distance < min_distance:
                min_distance = distance
                min_index = i

        return self._pending_requests.pop(min_index)

    def _scan(self) -> Optional[IORequest]:
        """SCAN: 电梯算法"""
        # 按块号排序
        sorted_requests = sorted(self._pending_requests,
                                key=lambda r: r.block_number)

        # 在当前方向上找第一个大于等于当前位置的请求
        for i, req in enumerate(sorted_requests):
            if self._direction == 1 and req.block_number >= self._current_position:
                # 移除并返回
                self._pending_requests.remove(req)
                return req
            elif self._direction == -1 and req.block_number <= self._current_position:
                # 移除并返回
                self._pending_requests.remove(req)
                return req

        # 当前方向没有请求，改变方向
        self._direction *= -1

        # 重新查找
        if self._direction == 1:
            # 向上，找最小的
            min_req = min(self._pending_requests, key=lambda r: r.block_number)
        else:
            # 向下，找最大的
            min_req = max(self._pending_requests, key=lambda r: r.block_number)

        self._pending_requests.remove(min_req)
        return min_req

    def _c_scan(self) -> Optional[IORequest]:
        """C-SCAN: 循环扫描"""
        # 按块号排序
        sorted_requests = sorted(self._pending_requests,
                                key=lambda r: r.block_number)

        # 找第一个大于等于当前位置的请求
        for req in sorted_requests:
            if req.block_number >= self._current_position:
                self._pending_requests.remove(req)
                return req

        # 到了最大位置，返回最小位置
        if self._pending_requests:
            min_req = min(self._pending_requests, key=lambda r: r.block_number)
            self._pending_requests.remove(min_req)
            return min_req

        return None

    def _look(self) -> Optional[IORequest]:
        """LOOK: SCAN优化版"""
        # 按块号排序
        sorted_requests = sorted(self._pending_requests,
                                key=lambda r: r.block_number)

        # 在当前方向上找请求
        if self._direction == 1:
            for req in sorted_requests:
                if req.block_number >= self._current_position:
                    self._pending_requests.remove(req)
                    return req
            # 没有向上的请求，改变方向
            self._direction = -1
            if sorted_requests:
                max_req = max(self._pending_requests, key=lambda r: r.block_number)
                self._pending_requests.remove(max_req)
                return max_req
        else:
            for req in reversed(sorted_requests):
                if req.block_number <= self._current_position:
                    self._pending_requests.remove(req)
                    return req
            # 没有向下的请求，改变方向
            self._direction = 1
            if sorted_requests:
                min_req = min(self._pending_requests, key=lambda r: r.block_number)
                self._pending_requests.remove(min_req)
                return min_req

        return None

    def _c_look(self) -> Optional[IORequest]:
        """C-LOOK: C-SCAN优化版"""
        # 按块号排序
        sorted_requests = sorted(self._pending_requests,
                                key=lambda r: r.block_number)

        # 找第一个大于等于当前位置的请求
        for req in sorted_requests:
            if req.block_number >= self._current_position:
                self._pending_requests.remove(req)
                return req

        # 到了最高请求位置，跳到最低请求位置
        if self._pending_requests:
            min_req = min(self._pending_requests, key=lambda r: r.block_number)
            self._pending_requests.remove(min_req)
            return min_req

        return None

    def execute_request(self, request: IORequest, seek_time_per_block: float = 0.001) -> None:
        """
        执行I/O请求

        Args:
            request: I/O请求
            seek_time_per_block: 每块寻道时间
        """
        # 计算寻道距离和时间
        request.seek_distance = abs(request.block_number - self._current_position)
        seek_time = request.seek_distance * seek_time_per_block

        request.start_time = time.time()
        time.sleep(seek_time)  # 模拟寻道
        request.finish_time = time.time()

        # 更新状态
        self._current_position = request.block_number
        self._total_seek += request.seek_distance
        self._total_wait_time += request.waiting_time

        self._completed_requests.append(request)

        # 调用回调
        if request.callback:
            request.callback(request)

        self._logger.debug(f"完成I/O请求 {request.request_id}: "
                          f"块 {request.block_number}, 寻道 {request.seek_distance}")

    def run_all(self) -> None:
        """执行所有待处理请求"""
        while self._pending_requests:
            request = self.get_next_request()
            if request:
                self.execute_request(request)

    def get_pending_count(self) -> int:
        """获取待处理请求数"""
        return len(self._pending_requests)

    def get_completed_count(self) -> int:
        """获取已完成请求数"""
        return len(self._completed_requests)

    def get_stats(self) -> dict:
        """获取统计信息"""
        avg_wait = self._total_wait_time / self._total_requests if self._total_requests > 0 else 0
        avg_seek = self._total_seek / self._total_requests if self._total_requests > 0 else 0

        return {
            'scheduler_type': self._type.value,
            'current_position': self._current_position,
            'direction': 'up' if self._direction == 1 else 'down',
            'pending_requests': len(self._pending_requests),
            'completed_requests': len(self._completed_requests),
            'total_seek_distance': self._total_seek,
            'average_seek_distance': avg_seek,
            'average_wait_time': avg_wait
        }

    def print_schedule_sequence(self) -> None:
        """打印调度序列"""
        print(f"\n{self._type.value.upper()} 调度序列:")
        print("-" * 60)
        print(f"{'请求ID':<8} {'块号':<8} {'寻道距离':<10} {'等待时间':<12}")
        print("-" * 60)

        for req in self._completed_requests:
            print(f"{req.request_id:<8} {req.block_number:<8} "
                  f"{req.seek_distance:<10} {req.waiting_time:<12.4f}")

        print("-" * 60)
        stats = self.get_stats()
        print(f"总寻道距离: {stats['total_seek_distance']}")
        print(f"平均寻道距离: {stats['average_seek_distance']:.2f}")
        print(f"平均等待时间: {stats['average_wait_time']:.4f}s")


# 使用示例
if __name__ == "__main__":
    print("=== I/O调度算法演示 ===\n")

    # 创建不同调度器的工厂函数
    def create_test_requests(scheduler):
        """创建测试请求"""
        blocks = [98, 183, 37, 122, 14, 124, 65, 67]
        for i, block in enumerate(blocks):
            scheduler.submit_request(
                block_number=block,
                io_type=IOType.READ,
                data_size=1024,
                process_id=i
            )

    # 测试各种算法
    algorithms = [
        IOSchedulerType.FCFS,
        IOSchedulerType.SSTF,
        IOSchedulerType.SCAN,
        IOSchedulerType.LOOK,
        IOSchedulerType.C_LOOK
    ]

    initial_pos = 53

    for algo in algorithms:
        print(f"\n测试 {algo.value.upper()} 算法:")
        scheduler = IOScheduler(
            scheduler_type=algo,
            total_blocks=200,
            initial_position=initial_pos
        )
        create_test_requests(scheduler)
        scheduler.run_all()
        scheduler.print_schedule_sequence()

    print("\n所有算法测试完成！")
