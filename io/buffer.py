"""
缓冲区管理 - I/O缓冲与缓存

==========================================
       缓冲区管理深入学习教程
==========================================

🎯 什么是缓冲区？
----------------
缓冲区是内存中用于临时存储数据的区域，
用于协调I/O设备与CPU之间的速度差异。

📚 为什么需要缓冲？
------------------
1. 速度匹配：设备速度慢，CPU速度快
2. 减少中断次数
3. 提高I/O效率
4. 支持异步I/O

💡 缓冲技术类型
---------------
1. 单缓冲 (Single Buffering)
   - 一个缓冲区，简单但效率低

2. 双缓冲 (Double Buffering)
   - 两个缓冲区交替使用
   - 一个填充时另一个处理

3. 循环缓冲 (Circular Buffering)
   - 多个缓冲区组成环
   - 适合生产者-消费者模式

4. 缓冲池 (Buffer Pool)
   - 多个缓冲区统一管理
   - 动态分配和回收

🔧 缓冲区替换策略
-----------------
- LRU (最近最少使用)
- FIFO (先进先出)
- Clock (时钟算法)
"""

import threading
import time
from typing import Optional, List, Dict, Any
from collections import deque
from enum import Enum
from utils.logger import Logger


class BufferState(Enum):
    """缓冲区状态"""
    FREE = "free"          # 空闲
    BUSY = "busy"          # 忙碌
    DELAYED_WRITE = "delayed_write"  # 延迟写


class Buffer:
    """
    缓冲区

    表示单个缓冲区的数据结构和操作。
    """

    _next_id = 1

    def __init__(self, size: int = 4096):
        """
        初始化缓冲区

        Args:
            size: 缓冲区大小（字节）
        """
        self._id = Buffer._next_id
        Buffer._next_id += 1
        self._size = size
        self._data = bytearray(size)
        self._data_len = 0  # 实际数据长度
        self._state = BufferState.FREE

        # 关联信息
        self._block_number: Optional[int] = None
        self._device_id: Optional[int] = None

        # 时间戳
        self._access_time = time.time()
        self._modify_time: Optional[float] = None

        # 引用计数
        self._ref_count = 0

        # 哈希队列链接
        self._hash_next: Optional['Buffer'] = None
        self._hash_prev: Optional['Buffer'] = None

        # 空闲队列链接
        self._free_next: Optional['Buffer'] = None
        self._free_prev: Optional['Buffer'] = None

    @property
    def id(self) -> int:
        return self._id

    @property
    def size(self) -> int:
        return self._size

    @property
    def state(self) -> BufferState:
        return self._state

    @property
    def is_free(self) -> bool:
        return self._state == BufferState.FREE and self._ref_count == 0

    @property
    def is_dirty(self) -> bool:
        return self._state == BufferState.DELAYED_WRITE

    @property
    def block_number(self) -> Optional[int]:
        return self._block_number

    def read(self, offset: int = 0, length: int = -1) -> bytes:
        """
        读取缓冲区数据

        Args:
            offset: 偏移量
            length: 读取长度，-1表示全部

        Returns:
            bytes: 读取的数据
        """
        if length == -1:
            length = self._data_len - offset

        self._access_time = time.time()
        return bytes(self._data[offset:offset + length])

    def write(self, data: bytes, offset: int = 0) -> int:
        """
        写入数据到缓冲区

        Args:
            data: 要写入的数据
            offset: 偏移量

        Returns:
            int: 写入的字节数
        """
        length = len(data)
        if offset + length > self._size:
            length = self._size - offset

        self._data[offset:offset + length] = data
        self._data_len = max(self._data_len, offset + length)
        self._modify_time = time.time()
        self._access_time = time.time()

        return length

    def assign(self, device_id: int, block_number: int) -> None:
        """分配缓冲区给指定设备块"""
        self._device_id = device_id
        self._block_number = block_number
        self._state = BufferState.BUSY
        self._ref_count += 1
        self._access_time = time.time()

    def release(self) -> None:
        """释放缓冲区"""
        self._ref_count -= 1
        if self._ref_count <= 0:
            self._ref_count = 0
            if self._state != BufferState.DELAYED_WRITE:
                self._state = BufferState.FREE

    def mark_dirty(self) -> None:
        """标记为脏（延迟写）"""
        self._state = BufferState.DELAYED_WRITE

    def clear(self) -> None:
        """清空缓冲区"""
        self._data = bytearray(self._size)
        self._data_len = 0
        self._state = BufferState.FREE
        self._block_number = None
        self._device_id = None
        self._ref_count = 0
        self._modify_time = None

    def get_info(self) -> dict:
        """获取缓冲区信息"""
        return {
            'id': self._id,
            'size': self._size,
            'data_len': self._data_len,
            'state': self._state.value,
            'block_number': self._block_number,
            'device_id': self._device_id,
            'ref_count': self._ref_count,
            'access_time': self._access_time,
            'is_dirty': self.is_dirty
        }

    def __str__(self) -> str:
        return (f"Buffer(id={self._id}, size={self._size}, "
                f"state={self._state.value}, block={self._block_number})")


class CircularBuffer:
    """
    循环缓冲区

    用于生产者-消费者场景的环形缓冲区实现。
    """

    def __init__(self, capacity: int):
        """
        初始化循环缓冲区

        Args:
            capacity: 缓冲区容量
        """
        self._capacity = capacity
        self._buffer: List[Any] = [None] * capacity
        self._head = 0  # 写入位置
        self._tail = 0  # 读取位置
        self._count = 0  # 当前元素数
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
        self._logger = Logger()

    def put(self, item: Any, timeout: float = None) -> bool:
        """
        放入元素

        Args:
            item: 要放入的元素
            timeout: 超时时间

        Returns:
            bool: 是否成功
        """
        with self._not_full:
            while self._count >= self._capacity:
                if not self._not_full.wait(timeout=timeout):
                    return False

            self._buffer[self._head] = item
            self._head = (self._head + 1) % self._capacity
            self._count += 1
            self._not_empty.notify()
            return True

    def get(self, timeout: float = None) -> Any:
        """
        获取元素

        Args:
            timeout: 超时时间

        Returns:
            Any: 获取的元素，超时返回None
        """
        with self._not_empty:
            while self._count <= 0:
                if not self._not_empty.wait(timeout=timeout):
                    return None

            item = self._buffer[self._tail]
            self._tail = (self._tail + 1) % self._capacity
            self._count -= 1
            self._not_full.notify()
            return item

    def peek(self) -> Any:
        """查看队首元素但不移除"""
        with self._lock:
            if self._count > 0:
                return self._buffer[self._tail]
            return None

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def size(self) -> int:
        return self._count

    @property
    def is_empty(self) -> bool:
        return self._count == 0

    @property
    def is_full(self) -> bool:
        return self._count >= self._capacity

    def get_stats(self) -> dict:
        return {
            'capacity': self._capacity,
            'size': self._count,
            'head': self._head,
            'tail': self._tail
        }


class BufferManager:
    """
    缓冲区管理器

    管理缓冲池，提供缓冲区的分配、回收和查找功能。
    """

    def __init__(self, num_buffers: int = 10, buffer_size: int = 4096):
        """
        初始化缓冲区管理器

        Args:
            num_buffers: 缓冲区数量
            buffer_size: 每个缓冲区大小
        """
        self._num_buffers = num_buffers
        self._buffer_size = buffer_size
        self._logger = Logger()
        self._lock = threading.Lock()

        # 创建缓冲池
        self._buffers: List[Buffer] = [Buffer(buffer_size) for _ in range(num_buffers)]

        # 哈希表：快速查找特定块号的缓冲区
        # key: (device_id, block_number), value: Buffer
        self._hash_table: Dict[tuple, Buffer] = {}

        # 空闲队列
        self._free_list: deque = deque()
        for buf in self._buffers:
            self._free_list.append(buf)

        # 统计
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_reads = 0
        self._total_writes = 0

        self._logger.info(f"缓冲区管理器创建: {num_buffers}个缓冲区，每块{buffer_size}字节")

    def get_buffer(self, device_id: int, block_number: int) -> Buffer:
        """
        获取指定块的缓冲区

        Args:
            device_id: 设备ID
            block_number: 块号

        Returns:
            Buffer: 缓冲区
        """
        with self._lock:
            self._total_reads += 1

            # 在哈希表中查找
            key = (device_id, block_number)
            if key in self._hash_table:
                buf = self._hash_table[key]
                self._cache_hits += 1

                # 如果在空闲队列中，移除
                if buf in self._free_list:
                    self._free_list.remove(buf)

                buf._ref_count += 1
                buf._access_time = time.time()
                self._logger.debug(f"缓存命中: 设备{device_id} 块{block_number}")
                return buf

            # 缓存未命中
            self._cache_misses += 1

            # 从空闲队列获取
            if self._free_list:
                buf = self._free_list.popleft()
            else:
                # 没有空闲缓冲区，需要替换
                buf = self._evict_buffer()

            # 分配给请求的块
            buf.assign(device_id, block_number)
            self._hash_table[key] = buf

            self._logger.debug(f"缓存未命中: 设备{device_id} 块{block_number}")
            return buf

    def release_buffer(self, buf: Buffer) -> None:
        """
        释放缓冲区

        Args:
            buf: 要释放的缓冲区
        """
        with self._lock:
            buf.release()
            if buf.is_free:
                self._free_list.append(buf)

    def _evict_buffer(self) -> Buffer:
        """替换缓冲区（LRU策略）"""
        # 找到最久未使用的空闲缓冲区
        if self._free_list:
            return self._free_list.popleft()

        # 没有空闲缓冲区，找一个引用计数为0的
        for buf in self._buffers:
            if buf._ref_count == 0:
                # 如果是脏块，需要先写回
                if buf.is_dirty:
                    self._write_back(buf)

                # 从哈希表移除
                key = (buf._device_id, buf._block_number)
                if key in self._hash_table:
                    del self._hash_table[key]

                buf.clear()
                return buf

        raise RuntimeError("没有可用的缓冲区")

    def _write_back(self, buf: Buffer) -> None:
        """写回脏缓冲区"""
        self._total_writes += 1
        self._logger.debug(f"写回缓冲区 {buf.id}: 设备{buf._device_id} 块{buf._block_number}")
        # 实际系统中这里会执行磁盘写操作

    def flush_all(self) -> None:
        """刷新所有脏缓冲区"""
        with self._lock:
            for buf in self._buffers:
                if buf.is_dirty:
                    self._write_back(buf)
                    buf._state = BufferState.FREE

        self._logger.info("所有脏缓冲区已刷新")

    def get_cache_hit_rate(self) -> float:
        """获取缓存命中率"""
        total = self._cache_hits + self._cache_misses
        return (self._cache_hits / total * 100) if total > 0 else 0

    def get_stats(self) -> dict:
        """获取统计信息"""
        free_count = len(self._free_list)
        busy_count = sum(1 for b in self._buffers if b.state == BufferState.BUSY)
        dirty_count = sum(1 for b in self._buffers if b.is_dirty)

        return {
            'total_buffers': self._num_buffers,
            'buffer_size': self._buffer_size,
            'free_buffers': free_count,
            'busy_buffers': busy_count,
            'dirty_buffers': dirty_count,
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate': self.get_cache_hit_rate(),
            'total_reads': self._total_reads,
            'total_writes': self._total_writes
        }

    def print_status(self) -> None:
        """打印缓冲区状态"""
        print("\n缓冲区状态:")
        print("-" * 70)
        print(f"{'ID':<4} {'状态':<12} {'块号':<8} {'引用':<4} {'脏':<4} {'数据长度':<8}")
        print("-" * 70)

        for buf in self._buffers:
            info = buf.get_info()
            print(f"{info['id']:<4} {info['state']:<12} "
                  f"{info['block_number'] or 'N/A':<8} "
                  f"{info['ref_count']:<4} "
                  f"{'是' if info['is_dirty'] else '否':<4} "
                  f"{info['data_len']:<8}")

        print("-" * 70)
        stats = self.get_stats()
        print(f"缓存命中率: {stats['hit_rate']:.1f}%")


# 使用示例
if __name__ == "__main__":
    print("=== 缓冲区管理演示 ===\n")

    # 示例1: 基本缓冲区操作
    print("1. 基本缓冲区操作")
    buf = Buffer(size=1024)
    buf.write(b"Hello, Buffer!")
    data = buf.read()
    print(f"  写入: 'Hello, Buffer!'")
    print(f"  读取: {data.decode()}")
    print(f"  信息: {buf.get_info()}")

    # 示例2: 循环缓冲区
    print("\n2. 循环缓冲区")
    cb = CircularBuffer(capacity=3)

    import threading

    def producer():
        for i in range(5):
            cb.put(f"item-{i}")
            print(f"  生产: item-{i}")
            time.sleep(0.1)

    def consumer():
        for _ in range(5):
            item = cb.get(timeout=1)
            if item:
                print(f"  消费: {item}")
            time.sleep(0.2)

    p = threading.Thread(target=producer)
    c = threading.Thread(target=consumer)
    p.start()
    c.start()
    p.join()
    c.join()

    # 示例3: 缓冲区管理器
    print("\n3. 缓冲区管理器")
    bm = BufferManager(num_buffers=5, buffer_size=1024)

    # 获取一些缓冲区
    b1 = bm.get_buffer(device_id=1, block_number=100)
    b1.write(b"Block 100 data")

    b2 = bm.get_buffer(device_id=1, block_number=200)
    b2.write(b"Block 200 data")

    # 再次获取相同的块（应该命中缓存）
    b1_again = bm.get_buffer(device_id=1, block_number=100)
    print(f"  再次获取块100: {b1_again.id == b1.id} (同一缓冲区)")

    bm.print_status()
    print(f"\n  统计: {bm.get_stats()}")

    print("\n演示完成！")
