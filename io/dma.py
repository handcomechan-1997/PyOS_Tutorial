"""
DMA (直接内存访问) - 高效I/O数据传输

==========================================
        DMA深入学习教程
==========================================

🎯 什么是DMA？
-------------
DMA (Direct Memory Access) 是一种允许I/O设备直接访问内存的技术，
无需CPU参与数据传输，大大提高了I/O效率。

📚 为什么需要DMA？
-----------------
1. CPU速度远快于I/O设备
2. 程序控制I/O会浪费大量CPU时间
3. DMA可以让CPU在I/O期间执行其他任务

💡 DMA工作方式
--------------
1. CPU设置DMA控制器（源地址、目标地址、传输长度）
2. DMA控制器接管总线，执行数据传输
3. 传输完成后，DMA向CPU发送中断
4. CPU处理中断，继续后续操作

🔧 DMA传输模式
--------------
1. 突发模式 (Burst Mode)
   - 一次传输完成所有数据
   - 期间CPU无法访问内存

2. 周期窃取模式 (Cycle Stealing)
   - 每次传输一个字
   - 在CPU不使用总线周期时进行

3. 交错模式 (Interleaved)
   - 与CPU交替访问内存
   - 对CPU影响最小

📚 DMA控制器结构
----------------
- 内存地址寄存器 (MAR): 目标内存地址
- 设备地址寄存器: I/O设备地址
- 传输计数器: 剩余传输字节数
- 控制寄存器: 传输方向、模式等
"""

import threading
import time
from typing import Optional, Callable, List
from enum import Enum
from dataclasses import dataclass
from utils.logger import Logger


class DMATransferType(Enum):
    """DMA传输类型"""
    READ = "read"      # 从设备读取到内存
    WRITE = "write"    # 从内存写入到设备


class DMAState(Enum):
    """DMA状态"""
    IDLE = "idle"
    TRANSFERRING = "transferring"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class DMATransfer:
    """DMA传输任务"""
    transfer_id: int
    source: int           # 源地址
    destination: int      # 目标地址
    size: int             # 传输大小
    transfer_type: DMATransferType
    device_id: int        # 设备ID

    # 状态
    state: DMAState = DMAState.IDLE
    bytes_transferred: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None

    # 回调
    callback: Optional[Callable] = None


class DMAController:
    """
    DMA控制器模拟

    实现DMA传输的基本功能。
    """

    _next_transfer_id = 1

    def __init__(self, name: str = "", transfer_rate: int = 1024 * 1024):
        """
        初始化DMA控制器

        Args:
            name: 控制器名称
            transfer_rate: 传输速率（字节/秒）
        """
        self._name = name or f"DMA-{id(self)}"
        self._transfer_rate = transfer_rate
        self._logger = Logger()

        # 寄存器
        self._memory_address = 0
        self._device_address = 0
        self._transfer_count = 0
        self._control = 0

        # 状态
        self._state = DMAState.IDLE
        self._current_transfer: Optional[DMATransfer] = None

        # 传输队列
        self._transfer_queue: List[DMATransfer] = []
        self._completed_transfers: List[DMATransfer] = []

        # 线程
        self._lock = threading.Lock()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None

        # 中断回调
        self._interrupt_handler: Optional[Callable] = None

        # 统计
        self._total_transfers = 0
        self._total_bytes = 0
        self._total_time = 0.0

        self._logger.info(f"DMA控制器 '{self._name}' 创建，传输速率: {transfer_rate} B/s")

    @property
    def state(self) -> DMAState:
        return self._state

    @property
    def is_idle(self) -> bool:
        return self._state == DMAState.IDLE

    def set_interrupt_handler(self, handler: Callable) -> None:
        """设置中断处理函数"""
        self._interrupt_handler = handler

    def request_transfer(self, source: int, destination: int, size: int,
                        transfer_type: DMATransferType, device_id: int,
                        callback: Callable = None) -> int:
        """
        请求DMA传输

        Args:
            source: 源地址
            destination: 目标地址
            size: 传输大小
            transfer_type: 传输类型
            device_id: 设备ID
            callback: 完成回调

        Returns:
            int: 传输ID
        """
        with self._lock:
            transfer = DMATransfer(
                transfer_id=DMAController._next_transfer_id,
                source=source,
                destination=destination,
                size=size,
                transfer_type=transfer_type,
                device_id=device_id,
                callback=callback
            )
            DMAController._next_transfer_id += 1

            self._transfer_queue.append(transfer)
            self._logger.debug(f"DMA传输请求: ID={transfer.transfer_id}, "
                              f"大小={size}字节, 类型={transfer_type.value}")

            return transfer.transfer_id

    def start(self) -> None:
        """启动DMA控制器"""
        if self._running:
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        self._logger.info(f"DMA控制器 '{self._name}' 启动")

    def stop(self) -> None:
        """停止DMA控制器"""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=2.0)
        self._logger.info(f"DMA控制器 '{self._name}' 停止")

    def _worker_loop(self) -> None:
        """DMA工作线程"""
        while self._running:
            transfer = self._get_next_transfer()

            if transfer is None:
                time.sleep(0.01)
                continue

            self._execute_transfer(transfer)

    def _get_next_transfer(self) -> Optional[DMATransfer]:
        """获取下一个传输任务"""
        with self._lock:
            if self._transfer_queue:
                return self._transfer_queue.pop(0)
            return None

    def _execute_transfer(self, transfer: DMATransfer) -> None:
        """执行DMA传输"""
        self._state = DMAState.TRANSFERRING
        self._current_transfer = transfer

        transfer.state = DMAState.TRANSFERRING
        transfer.start_time = time.time()

        self._logger.debug(f"开始DMA传输 ID={transfer.transfer_id}")

        try:
            # 模拟DMA传输
            remaining = transfer.size
            while remaining > 0 and self._running:
                # 计算本次传输量
                chunk_size = min(remaining, self._transfer_rate // 100)
                transfer.bytes_transferred += chunk_size
                remaining -= chunk_size

                # 模拟传输时间
                time.sleep(chunk_size / self._transfer_rate)

            if remaining == 0:
                transfer.state = DMAState.COMPLETED
            else:
                transfer.state = DMAState.ERROR
                transfer.error_message = "传输被中断"

        except Exception as e:
            transfer.state = DMAState.ERROR
            transfer.error_message = str(e)
            self._logger.error(f"DMA传输错误: {e}")

        finally:
            transfer.end_time = time.time()

            # 更新统计
            self._total_transfers += 1
            self._total_bytes += transfer.bytes_transferred
            self._total_time += transfer.end_time - transfer.start_time

            # 记录完成
            with self._lock:
                self._completed_transfers.append(transfer)

            self._state = DMAState.IDLE
            self._current_transfer = None

            # 触发中断
            self._trigger_interrupt(transfer)

            # 调用回调
            if transfer.callback:
                transfer.callback(transfer)

    def _trigger_interrupt(self, transfer: DMATransfer) -> None:
        """触发DMA中断"""
        self._logger.debug(f"DMA中断: 传输ID={transfer.transfer_id}, "
                          f"状态={transfer.state.value}")

        if self._interrupt_handler:
            self._interrupt_handler(transfer)

    def get_transfer_status(self, transfer_id: int) -> Optional[DMATransfer]:
        """获取传输状态"""
        with self._lock:
            # 检查当前传输
            if self._current_transfer and self._current_transfer.transfer_id == transfer_id:
                return self._current_transfer

            # 检查已完成传输
            for transfer in self._completed_transfers:
                if transfer.transfer_id == transfer_id:
                    return transfer

            return None

    def wait_for_transfer(self, transfer_id: int, timeout: float = None) -> bool:
        """
        等待传输完成

        Args:
            transfer_id: 传输ID
            timeout: 超时时间

        Returns:
            bool: 是否完成
        """
        start = time.time()
        while True:
            transfer = self.get_transfer_status(transfer_id)
            if transfer and transfer.state in (DMAState.COMPLETED, DMAState.ERROR):
                return transfer.state == DMAState.COMPLETED

            if timeout and (time.time() - start) >= timeout:
                return False

            time.sleep(0.01)

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            avg_speed = self._total_bytes / self._total_time if self._total_time > 0 else 0

            return {
                'name': self._name,
                'state': self._state.value,
                'transfer_rate': self._transfer_rate,
                'total_transfers': self._total_transfers,
                'total_bytes': self._total_bytes,
                'total_time': self._total_time,
                'average_speed': avg_speed,
                'pending_transfers': len(self._transfer_queue),
                'completed_transfers': len(self._completed_transfers)
            }


class DMAMemory:
    """
    DMA内存模拟

    模拟可被DMA访问的内存区域。
    """

    def __init__(self, size: int = 1024 * 1024):
        """
        初始化DMA内存

        Args:
            size: 内存大小
        """
        self._size = size
        self._memory = bytearray(size)
        self._lock = threading.Lock()
        self._logger = Logger()

    def read(self, address: int, size: int) -> bytes:
        """读取内存"""
        with self._lock:
            if address + size > self._size:
                raise ValueError("读取范围超出内存边界")
            return bytes(self._memory[address:address + size])

    def write(self, address: int, data: bytes) -> int:
        """写入内存"""
        with self._lock:
            size = len(data)
            if address + size > self._size:
                raise ValueError("写入范围超出内存边界")
            self._memory[address:address + size] = data
            return size

    def clear(self) -> None:
        """清空内存"""
        with self._lock:
            self._memory = bytearray(self._size)

    @property
    def size(self) -> int:
        return self._size


class DMAChannel:
    """
    DMA通道

    每个DMA控制器可以有多个通道，每个通道可以独立传输。
    """

    def __init__(self, channel_id: int, controller: DMAController):
        """
        初始化DMA通道

        Args:
            channel_id: 通道ID
            controller: 所属DMA控制器
        """
        self._channel_id = channel_id
        self._controller = controller
        self._logger = Logger()

    def transfer(self, source: int, destination: int, size: int,
                transfer_type: DMATransferType, device_id: int,
                callback: Callable = None) -> int:
        """发起传输"""
        return self._controller.request_transfer(
            source, destination, size, transfer_type, device_id, callback
        )

    @property
    def channel_id(self) -> int:
        return self._channel_id


# 使用示例
if __name__ == "__main__":
    print("=== DMA控制器演示 ===\n")

    # 创建DMA控制器
    dma = DMAController(name="DMA-0", transfer_rate=10000)  # 10KB/s

    # 设置中断处理
    def on_dma_interrupt(transfer):
        print(f"  [中断] 传输ID={transfer.transfer_id} 完成，"
              f"状态={transfer.state.value}，"
              f"传输={transfer.bytes_transferred}字节")

    dma.set_interrupt_handler(on_dma_interrupt)

    # 创建DMA内存
    memory = DMAMemory(size=65536)

    # 写入测试数据
    test_data = b"Hello, DMA! This is a test data for DMA transfer." * 100
    memory.write(0, test_data)

    # 启动DMA
    dma.start()

    print("1. 发起DMA传输")

    def on_complete(transfer):
        print(f"  [回调] 传输 {transfer.transfer_id} 完成！")

    # 发起传输
    tid1 = dma.request_transfer(
        source=0,
        destination=1000,
        size=len(test_data),
        transfer_type=DMATransferType.READ,
        device_id=1,
        callback=on_complete
    )

    tid2 = dma.request_transfer(
        source=1000,
        destination=2000,
        size=len(test_data) // 2,
        transfer_type=DMATransferType.WRITE,
        device_id=2,
        callback=on_complete
    )

    print(f"  传输ID: {tid1}, {tid2}")

    # 等待传输完成
    print("\n2. 等待传输完成...")
    dma.wait_for_transfer(tid1, timeout=10)
    dma.wait_for_transfer(tid2, timeout=10)

    # 打印统计
    print(f"\n3. 统计信息:")
    stats = dma.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 停止DMA
    dma.stop()

    print("\n演示完成！")
