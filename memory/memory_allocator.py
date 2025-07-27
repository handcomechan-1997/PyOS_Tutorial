"""
内存分配器模块 - 实现动态内存分配
"""

import threading
import time
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum

from utils.logger import Logger

class AllocationStrategy(Enum):
    """分配策略枚举"""
    FIRST_FIT = "first_fit"
    BEST_FIT = "best_fit"
    WORST_FIT = "worst_fit"

class MemoryBlock:
    """内存块"""
    
    def __init__(self, start_address: int, size: int, is_free: bool = True):
        self.start_address = start_address
        self.size = size
        self.is_free = is_free
        self.next_block: Optional['MemoryBlock'] = None
        self.prev_block: Optional['MemoryBlock'] = None
        self.allocated_time: Optional[float] = None
        self.process_id: Optional[int] = None

class MemoryAllocator:
    """内存分配器"""
    
    def __init__(self, total_memory: int = 1024 * 1024, strategy: AllocationStrategy = AllocationStrategy.FIRST_FIT):
        """初始化内存分配器"""
        self.logger = Logger()
        self.total_memory = total_memory
        self.strategy = strategy
        self.allocated_memory = 0
        self.free_memory = total_memory
        
        # 内存块链表
        self.head = MemoryBlock(0, total_memory, True)
        
        # 分配统计
        self.allocation_count = 0
        self.deallocation_count = 0
        self.fragmentation_count = 0
        
        # 同步锁
        self.lock = threading.Lock()
        
        self.logger.info(f"内存分配器初始化: {total_memory} bytes, 策略: {strategy.value}")
    
    def allocate(self, size: int, process_id: Optional[int] = None) -> Optional[int]:
        """分配内存"""
        with self.lock:
            if size <= 0:
                self.logger.warning(f"无效的分配大小: {size}")
                return None
            
            if size > self.free_memory:
                self.logger.warning(f"内存不足，请求: {size}, 可用: {self.free_memory}")
                return None
            
            # 根据策略查找合适的块
            block = self._find_suitable_block(size)
            if not block:
                self.logger.warning(f"无法找到合适的内存块，大小: {size}")
                return None
            
            # 分配内存
            address = self._allocate_block(block, size, process_id)
            if address is not None:
                self.allocation_count += 1
                self.allocated_memory += size
                self.free_memory -= size
                self.logger.log_memory_event(f"分配内存: 地址 {address}, 大小 {size}, 进程 {process_id}")
            
            return address
    
    def deallocate(self, address: int) -> bool:
        """释放内存"""
        with self.lock:
            block = self._find_block_by_address(address)
            if not block or block.is_free:
                self.logger.warning(f"无效的释放地址: {address}")
                return False
            
            # 释放内存
            size = block.size
            block.is_free = True
            block.allocated_time = None
            block.process_id = None
            
            # 合并相邻的空闲块
            self._merge_free_blocks()
            
            self.deallocation_count += 1
            self.allocated_memory -= size
            self.free_memory += size
            
            self.logger.log_memory_event(f"释放内存: 地址 {address}, 大小 {size}")
            return True
    
    def _find_suitable_block(self, size: int) -> Optional[MemoryBlock]:
        """根据策略查找合适的内存块"""
        if self.strategy == AllocationStrategy.FIRST_FIT:
            return self._first_fit(size)
        elif self.strategy == AllocationStrategy.BEST_FIT:
            return self._best_fit(size)
        elif self.strategy == AllocationStrategy.WORST_FIT:
            return self._worst_fit(size)
        else:
            return self._first_fit(size)
    
    def _first_fit(self, size: int) -> Optional[MemoryBlock]:
        """首次适应算法"""
        current = self.head
        while current:
            if current.is_free and current.size >= size:
                return current
            current = current.next_block
        return None
    
    def _best_fit(self, size: int) -> Optional[MemoryBlock]:
        """最佳适应算法"""
        best_block = None
        best_size = float('inf')
        current = self.head
        
        while current:
            if current.is_free and current.size >= size:
                if current.size < best_size:
                    best_size = current.size
                    best_block = current
            current = current.next_block
        
        return best_block
    
    def _worst_fit(self, size: int) -> Optional[MemoryBlock]:
        """最坏适应算法"""
        worst_block = None
        worst_size = 0
        current = self.head
        
        while current:
            if current.is_free and current.size >= size:
                if current.size > worst_size:
                    worst_size = current.size
                    worst_block = current
            current = current.next_block
        
        return worst_block
    
    def _allocate_block(self, block: MemoryBlock, size: int, process_id: Optional[int]) -> Optional[int]:
        """在指定块中分配内存"""
        address = block.start_address
        
        if block.size == size:
            # 完全匹配
            block.is_free = False
            block.allocated_time = time.time()
            block.process_id = process_id
        else:
            # 需要分割块
            new_block = MemoryBlock(block.start_address + size, block.size - size, True)
            new_block.next_block = block.next_block
            if block.next_block:
                block.next_block.prev_block = new_block
            
            block.size = size
            block.is_free = False
            block.allocated_time = time.time()
            block.process_id = process_id
            block.next_block = new_block
            new_block.prev_block = block
        
        return address
    
    def _find_block_by_address(self, address: int) -> Optional[MemoryBlock]:
        """根据地址查找内存块"""
        current = self.head
        while current:
            if current.start_address == address:
                return current
            current = current.next_block
        return None
    
    def _merge_free_blocks(self):
        """合并相邻的空闲块"""
        current = self.head
        while current and current.next_block:
            if current.is_free and current.next_block.is_free:
                # 合并当前块和下一个块
                current.size += current.next_block.size
                current.next_block = current.next_block.next_block
                if current.next_block:
                    current.next_block.prev_block = current
                self.fragmentation_count += 1
            else:
                current = current.next_block
    
    def get_memory_stats(self) -> Dict[str, Union[int, float]]:
        """获取内存统计信息"""
        with self.lock:
            return {
                'total_memory': self.total_memory,
                'allocated_memory': self.allocated_memory,
                'free_memory': self.free_memory,
                'allocation_count': self.allocation_count,
                'deallocation_count': self.deallocation_count,
                'fragmentation_count': self.fragmentation_count,
                'utilization': (self.allocated_memory / self.total_memory) * 100 if self.total_memory > 0 else 0
            }
    
    def print_memory_map(self):
        """打印内存映射"""
        with self.lock:
            print(f"\n内存分配器映射 (策略: {self.strategy.value}):")
            print("-" * 80)
            print(f"{'起始地址':<12} {'大小':<10} {'状态':<10} {'进程ID':<10}")
            print("-" * 80)
            
            current = self.head
            while current:
                status = "FREE" if current.is_free else "ALLOCATED"
                process_id = current.process_id if current.process_id else "N/A"
                print(f"{current.start_address:<12} {current.size:<10} {status:<10} {process_id:<10}")
                current = current.next_block
            
            print("-" * 80)
            stats = self.get_memory_stats()
            print(f"统计: 总内存 {stats['total_memory']}, 已分配 {stats['allocated_memory']}, "
                  f"空闲 {stats['free_memory']}, 利用率 {stats['utilization']:.1f}%")
    
    def defragment(self):
        """内存碎片整理"""
        with self.lock:
            # TODO: 实现内存碎片整理
            # 1. 移动已分配的块
            # 2. 合并空闲块
            # 3. 更新地址映射
            self.logger.info("内存碎片整理功能待实现") 