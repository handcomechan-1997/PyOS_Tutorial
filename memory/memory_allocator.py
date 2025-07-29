"""
内存分配器模块 - 实现动态内存分配

==========================================
           内存分配深入学习教程
==========================================

🎯 学习目标与意义
-----------------
内存分配是操作系统的核心功能之一，理解内存分配机制对于深入理解操作系统原理至关重要。

通过本模块的学习，你将：
1. 掌握内存分配的基本原理和实现机制
2. 理解不同分配算法的设计思想和适用场景
3. 学会分析内存碎片化问题及其解决方案
4. 具备设计和实现高效内存分配器的能力
5. 为后续学习虚拟内存、进程管理等高级概念奠定基础

📚 内存分配基础理论
-------------------

1. 内存分配的本质
   - 内存分配是操作系统为程序提供存储空间的过程
   - 涉及物理内存的管理和虚拟地址空间的映射
   - 需要在内存利用率和分配效率之间找到平衡

2. 内存分配的分类
   - 静态分配：程序编译时确定内存大小和位置
   - 动态分配：程序运行时根据需要分配和释放内存
   - 连续分配：分配连续的内存空间
   - 非连续分配：允许内存空间分散存储

3. 内存分配的基本要求
   - 正确性：确保分配的内存地址有效且可访问
   - 效率性：分配和释放操作要快速完成
   - 利用率：最大化内存空间的使用效率
   - 安全性：防止内存泄漏和越界访问

🔧 内存分配算法深度解析
-----------------------

1. 首次适应算法 (First Fit Algorithm)
   
   核心思想：
   - 从内存起始位置开始，查找第一个足够大的空闲块
   - 一旦找到合适的块就立即分配，不再继续查找
   
   算法特点：
   - 时间复杂度：O(n)，其中n是内存块数量
   - 空间复杂度：O(1)，只需要遍历链表
   - 分配速度：较快，通常在前几个块就能找到
   
   适用场景：
   - 内存使用相对均匀的情况
   - 对分配速度要求较高的系统
   - 内存碎片化程度不严重的环境
   
   优缺点分析：
   优点：实现简单，分配速度快，适合一般用途
   缺点：容易在内存前端产生碎片，可能导致后续大块分配困难

2. 最佳适应算法 (Best Fit Algorithm)
   
   核心思想：
   - 遍历所有空闲块，找到大小最接近请求的空闲块
   - 选择能够满足需求的最小空闲块进行分配
   
   算法特点：
   - 时间复杂度：O(n)，需要遍历所有空闲块
   - 空间复杂度：O(1)，只需要记录最佳匹配
   - 分配速度：较慢，需要完整遍历
   
   适用场景：
   - 内存资源紧张，需要最大化利用率
   - 对内存碎片化要求严格的系统
   - 长期运行且内存使用模式稳定的应用
   
   优缺点分析：
   优点：内存利用率最高，产生的内部碎片最小
   缺点：分配速度较慢，可能产生较多外部碎片

3. 最坏适应算法 (Worst Fit Algorithm)
   
   核心思想：
   - 在所有空闲块中选择最大的块进行分配
   - 目的是减少大块碎片，便于后续分配
   
   算法特点：
   - 时间复杂度：O(n)，需要遍历所有空闲块
   - 空间复杂度：O(1)，需要记录最大块
   - 分配速度：较慢，需要完整遍历
   
   适用场景：
   - 大块内存分配较多的系统
   - 希望保持大块空闲内存的环境
   - 内存使用模式变化较大的应用
   
   优缺点分析：
   优点：减少大块碎片，便于后续大块分配
   缺点：可能产生较多小块碎片，分配速度较慢

🔍 内存碎片化问题深度分析
-------------------------

1. 内存碎片的类型与成因
   
   内部碎片 (Internal Fragmentation)：
   - 定义：分配给进程的内存块大于实际需要的内存
   - 成因：内存分配的最小单位限制，对齐要求
   - 影响：降低内存利用率，浪费存储空间
   - 解决：使用合适的最小分配单位，优化对齐策略
   
   外部碎片 (External Fragmentation)：
   - 定义：内存中有足够的总空闲空间，但无法满足大块请求
   - 成因：频繁的分配和释放操作导致空闲空间分散
   - 影响：无法分配大块内存，降低系统性能
   - 解决：内存碎片整理，使用非连续分配技术

2. 碎片化的影响机制
   
   对系统性能的影响：
   - 降低内存利用率，增加内存需求
   - 影响分配效率，增加查找时间
   - 可能导致系统不稳定或崩溃
   
   对应用程序的影响：
   - 限制程序可用的最大内存块
   - 增加内存分配失败的概率
   - 影响程序的运行效率

3. 碎片化的预防与解决
   
   预防策略：
   - 选择合适的分配算法
   - 合理设计内存分配策略
   - 避免频繁的小块分配和释放
   
   解决技术：
   - 内存碎片整理：移动已分配块，合并空闲块
   - 分页技术：将内存分割成固定大小的页面
   - 段式管理：根据程序逻辑分段管理内存

🏗️ 内存分配器的设计原则
------------------------

1. 设计目标
   
   功能性要求：
   - 支持动态分配和释放
   - 提供多种分配策略
   - 支持内存统计和监控
   
   性能要求：
   - 分配和释放操作要快速
   - 内存利用率要高
   - 碎片化程度要低
   
   可靠性要求：
   - 防止内存泄漏
   - 保证数据完整性
   - 支持错误恢复

2. 数据结构设计
   
   内存块管理：
   - 使用链表结构组织内存块
   - 维护空闲块和已分配块的信息
   - 支持快速查找和合并操作
   
   元数据管理：
   - 记录分配统计信息
   - 维护内存使用状态
   - 支持调试和监控功能

3. 并发控制
   
   线程安全：
   - 使用锁机制保护共享数据
   - 避免竞态条件
   - 保证操作的原子性
   
   性能优化：
   - 减少锁的持有时间
   - 使用细粒度锁
   - 考虑无锁数据结构

📊 内存分配性能分析
--------------------

1. 性能指标
   
   时间性能：
   - 分配时间：从请求到获得内存的时间
   - 释放时间：从释放请求到完成的时间
   - 查找时间：在空闲块中查找合适块的时间
   
   空间性能：
   - 内存利用率：已分配内存占总内存的比例
   - 碎片化程度：外部碎片的严重程度
   - 分配成功率：成功分配请求的比例

2. 性能优化技术
   
   算法优化：
   - 使用快速查找算法
   - 维护空闲块索引
   - 采用分层管理策略
   
   数据结构优化：
   - 使用高效的数据结构
   - 减少内存访问次数
   - 优化缓存局部性

🔬 实际应用场景分析
--------------------

1. 操作系统内核
   
   应用特点：
   - 对性能和可靠性要求极高
   - 内存使用模式复杂多变
   - 需要支持多种分配策略
   
   设计考虑：
   - 使用多种分配算法
   - 实现内存保护机制
   - 支持内存回收和整理

2. 应用程序
   
   应用特点：
   - 内存使用模式相对稳定
   - 对分配速度要求较高
   - 需要防止内存泄漏
   
   设计考虑：
   - 使用简单的分配算法
   - 实现内存池技术
   - 提供调试和监控功能

3. 嵌入式系统
   
   应用特点：
   - 内存资源极其有限
   - 对实时性要求高
   - 需要确定性行为
   
   设计考虑：
   - 使用静态分配为主
   - 实现内存保护机制
   - 优化内存使用效率

🎓 学习进阶路径
---------------

1. 理论基础
   - 深入理解计算机体系结构
   - 掌握操作系统原理
   - 学习算法和数据结构

2. 实践技能
   - 实现各种分配算法
   - 分析性能瓶颈
   - 优化内存使用

3. 高级主题
   - 虚拟内存管理
   - 垃圾回收技术
   - 内存安全机制

4. 前沿技术
   - 非易失性内存管理
   - 异构内存系统
   - 内存计算技术

==========================================
            开始你的深入学习之旅！
==========================================

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
        """
        在指定的内存块中分配内存。

        参数:
            block: 需要分配的内存块（必须是空闲块，且大小 >= size）
            size:  需要分配的内存大小
            process_id: 分配给哪个进程（可选）

        返回:
            分配的起始地址（int），如果分配失败则返回 None
        """
        address = block.start_address  # 记录分配的起始地址

        if block.size == size:
            # 情况1：请求的大小与当前空闲块完全相等，无需分割
            block.is_free = False  # 标记为已分配
            block.allocated_time = time.time()  # 记录分配时间
            block.process_id = process_id  # 记录分配给哪个进程
        else:
            # 情况2：请求的大小小于当前空闲块，需要将空闲块分割
            # 创建一个新的空闲块，起始地址为当前块起始地址+size，大小为剩余部分
            new_block = MemoryBlock(
                block.start_address + size,  # 新块的起始地址
                block.size - size,           # 新块的大小
                True                         # 新块初始为“空闲”
            )
            # 维护链表指针：新块的 next_block 指向原来当前块的 next_block
            new_block.next_block = block.next_block
            if block.next_block:
                # 如果当前块后面还有块，则把它的 prev_block 指向新块
                block.next_block.prev_block = new_block

            # 更新当前块的信息：只保留分配出去的部分
            block.size = size
            block.is_free = False
            block.allocated_time = time.time()
            block.process_id = process_id
            block.next_block = new_block  # 当前块的 next_block 指向新块
            new_block.prev_block = block  # 新块的 prev_block 指向当前块

        # 返回分配的起始地址
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
            self.logger.info("开始内存碎片整理...")

            # 1. 收集所有已分配块的信息
            allocated_blocks = []
            current = self.head
            while current:
                if not current.is_free:
                    allocated_blocks.append(current)
                current = current.next_block

            # 2. 重新排列已分配块到内存前部，合并所有空闲空间到末尾
            new_address = 0
            prev_block = None
            for block in allocated_blocks:
                if block.start_address != new_address:
                    # 移动块
                    block.start_address = new_address
                block.prev_block = prev_block
                if prev_block:
                    prev_block.next_block = block
                prev_block = block
                new_address += block.size

            # 3. 创建一个新的大空闲块（如果有剩余空间）
            free_size = self.total_memory - new_address
            if free_size > 0:
                free_block = type(self.head)(
                    start_address=new_address,
                    size=free_size,
                    is_free=True,
                    process_id=None
                )
                free_block.prev_block = prev_block
                if prev_block:
                    prev_block.next_block = free_block
                free_block.next_block = None
                prev_block = free_block
            else:
                free_block = None
                if prev_block:
                    prev_block.next_block = None

            # 4. 更新链表头
            if allocated_blocks:
                self.head = allocated_blocks[0]
            elif free_block:
                self.head = free_block
            else:
                self.head = None

            # 5. 统计碎片整理
            self.fragmentation_count += 1

            self.logger.info("内存碎片整理完成。")