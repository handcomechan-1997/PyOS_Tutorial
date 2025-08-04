"""
虚拟内存模块 - 实现虚拟内存管理

本模块实现了完整的虚拟内存管理系统, 包括:
1. 页面管理: 页面的创建, 分配, 释放
2. 内存访问: 虚拟地址到物理地址的转换
3. 统计信息: 缺页率, 命中率等性能指标

页面置换算法实现在 page_replacement.py 模块中.

教学要点:
- 理解虚拟内存的基本概念
- 掌握页面管理的核心机制
- 学习内存访问的处理流程
"""

import threading
import time
from typing import Dict, List, Optional, Tuple
from enum import Enum

from utils.logger import Logger
from .page_replacement import PageReplacementAlgorithm, PageReplacementFactory

class PageState(Enum):
    """页面状态枚举"""
    FREE = "free"           # 空闲状态
    ALLOCATED = "allocated" # 已分配状态
    SWAPPED_OUT = "swapped_out"  # 已换出状态

class Page:
    """
    内存页面类
    
    表示虚拟内存中的一个页面, 包含页面的所有元数据信息.
    页面是虚拟内存管理的基本单位, 通常大小为4KB.
    
    属性说明:
        page_number (int): 页面编号, 在进程虚拟地址空间中的唯一标识
        size (int): 页面大小, 单位为字节, 默认4096字节(4KB)
        state (PageState): 页面当前状态(空闲/已分配/已换出)
        process_id (int): 占用该页面的进程ID, None表示未被占用
        frame_number (int): 页面映射到的物理帧号, None表示未映射
        access_time (float): 上次访问时间戳, 用于页面置换算法
        modified (bool): 页面是否被修改(脏页标志), 用于写回策略
        reference_count (int): 页面被引用的次数, 用于LRU等算法
        reference_bit (bool): 引用位, 用于Clock算法
    """

    def __init__(self, page_number: int, size: int = 4096):
        self.page_number = page_number      # 页面编号
        self.size = size                    # 页面大小(字节)
        self.state = PageState.FREE         # 页面当前状态
        self.process_id = None              # 占用该页面的进程ID
        self.frame_number = None            # 页面映射到的物理帧号
        self.access_time = 0                # 上次访问时间
        self.modified = False               # 页面是否被修改(脏页标志)
        self.reference_count = 0            # 页面被引用的次数
        self.reference_bit = False          # 引用位(用于Clock算法)

    def __str__(self):
        """返回页面的字符串表示"""
        return f"Page({self.page_number}, pid={self.process_id}, frame={self.frame_number}, state={self.state.value})"

class VirtualMemory:
    """
    虚拟内存管理器
    
    实现完整的虚拟内存管理功能, 包括:
    - 页面分配和释放
    - 虚拟地址到物理地址的转换
    - 页面置换算法(通过策略模式)
    - 内存统计信息
    
    参数说明:
        physical_memory_size (int): 物理内存大小, 默认1MB
        page_size (int): 页面大小, 默认4KB
        replacement_algorithm (PageReplacementAlgorithm): 页面置换算法, 默认LRU
    """
    
    def __init__(self, physical_memory_size: int = 1024 * 1024, 
                 page_size: int = 4096, 
                 replacement_algorithm: PageReplacementAlgorithm = PageReplacementAlgorithm.LRU):
        """初始化虚拟内存管理器"""
        self.logger = Logger()
        self.physical_memory_size = physical_memory_size
        self.page_size = page_size
        self.total_pages = physical_memory_size // page_size
        
        # 物理内存帧
        self.physical_frames: List[Optional[Page]] = [None] * self.total_pages
        
        # 页面表 (进程ID -> 页面表)
        self.page_tables: Dict[int, Dict[int, Page]] = {}
        
        # 空闲页面列表
        self.free_pages: List[int] = list(range(self.total_pages))
        
        # 页面置换算法(使用工厂模式创建)
        self.page_replacement = PageReplacementFactory.create_algorithm(replacement_algorithm, self)
        
        # 统计信息
        self.page_faults = 0
        self.page_hits = 0
        self.total_accesses = 0
        
        # 同步锁
        self.lock = threading.Lock()
        
        self.logger.info(f"虚拟内存管理器初始化: {physical_memory_size} bytes, {self.total_pages} pages")
        self.logger.info(f"使用页面置换算法: {self.page_replacement.name}")
    
    def set_replacement_algorithm(self, algorithm: PageReplacementAlgorithm):
        """设置页面置换算法"""
        self.page_replacement = PageReplacementFactory.create_algorithm(algorithm, self)
        self.logger.info(f"切换到页面置换算法: {self.page_replacement.name}")
    
    def allocate_pages(self, process_id: int, num_pages: int) -> bool:
        """
        为进程分配虚拟页面
        
        参数:
            process_id (int): 进程ID
            num_pages (int): 要分配的页面数量
            
        返回:
            bool: 分配是否成功
        """
        with self.lock:
            if num_pages > len(self.free_pages):
                self.logger.warning(f"物理内存不足, 请求: {num_pages}, 可用: {len(self.free_pages)}")
                return False
            
            # 创建进程页面表
            if process_id not in self.page_tables:
                self.page_tables[process_id] = {}
            
            # 分配页面
            for i in range(num_pages):
                if self.free_pages:
                    frame_number = self.free_pages.pop(0)
                    page = Page(len(self.page_tables[process_id]), self.page_size)
                    page.state = PageState.ALLOCATED
                    page.process_id = process_id
                    page.frame_number = frame_number
                    page.access_time = time.time()
                    
                    self.physical_frames[frame_number] = page
                    self.page_tables[process_id][page.page_number] = page
                    
                    # 如果是FIFO算法, 将页面添加到队列
                    if hasattr(self.page_replacement, 'add_page'):
                        self.page_replacement.add_page(frame_number)
            
            self.logger.log_memory_event(f"为进程 {process_id} 分配了 {num_pages} 个页面")
            return True
    
    def access_memory(self, process_id: int, virtual_address: int, is_write: bool = False) -> bool:
        """
        访问虚拟内存地址
        
        参数:
            process_id (int): 进程ID
            virtual_address (int): 虚拟地址
            is_write (bool): 是否为写操作
            
        返回:
            bool: 访问是否成功
        """
        with self.lock:
            self.total_accesses += 1
            page_number = virtual_address // self.page_size
            offset = virtual_address % self.page_size
            
            if process_id not in self.page_tables:
                self.logger.error(f"进程 {process_id} 的页面表不存在")
                return False
            
            if page_number not in self.page_tables[process_id]:
                # 页面不存在, 触发缺页中断
                self.page_faults += 1
                self.logger.log_memory_event(f"缺页中断: 进程 {process_id}, 页面 {page_number}")
                return self._handle_page_fault(process_id, page_number, is_write)
            else:
                # 页面存在, 更新访问信息
                page = self.page_tables[process_id][page_number]
                page.access_time = time.time()
                page.reference_count += 1
                page.modified = page.modified or is_write
                
                # 更新页面置换算法的引用信息
                self.page_replacement.update_reference(page)
                
                self.page_hits += 1
                return True
    
    def _handle_page_fault(self, process_id: int, page_number: int, is_write: bool = False) -> bool:
        """
        处理缺页中断(Page Fault)

        缺页中断是指进程在访问虚拟地址时, 发现所需的页面不在物理内存中(即页面未被加载到内存),
        由硬件或操作系统触发的一种中断. 此时操作系统需要暂停当前进程的执行, 通过以下步骤处理缺页:
        1. 查找空闲物理帧, 若有则直接分配;
        2. 若无空闲帧, 则根据页面置换算法选择一个页面进行置换(如FIFO、LRU、Clock等);
        3. 将所需页面从外存(如磁盘)加载到物理内存的相应帧中;
        4. 更新页表和相关元数据, 恢复进程执行.

        参数:
            process_id (int): 进程ID
            page_number (int): 页面号
            is_write (bool): 是否为写操作

        返回:
            bool: 处理是否成功
        """
        # 1. 查找空闲物理帧
        if self.free_pages:
            frame_number = self.free_pages.pop(0)
            page = Page(page_number, self.page_size)
            page.state = PageState.ALLOCATED
            page.process_id = process_id
            page.frame_number = frame_number
            page.access_time = time.time()
            page.modified = is_write
            page.reference_count = 1

            self.physical_frames[frame_number] = page
            self.page_tables[process_id][page_number] = page
            
            # 如果是FIFO算法, 将页面添加到队列
            if hasattr(self.page_replacement, 'add_page'):
                self.page_replacement.add_page(frame_number)

            self.logger.log_memory_event(f"页面 {page_number} 加载到帧 {frame_number}")
            return True

        # 2. 没有空闲帧, 执行页面置换
        victim_result = self.page_replacement.select_victim()
        if victim_result is None:
            self.logger.error("无法找到可置换的页面")
            return False
        
        victim_page, victim_frame = victim_result
        
        if victim_page:
            # 置换现有页面
            old_process_id = victim_page.process_id
            old_page_number = victim_page.page_number

            # 从原进程的页表中移除
            if old_process_id in self.page_tables and old_page_number in self.page_tables[old_process_id]:
                del self.page_tables[old_process_id][old_page_number]

            self.logger.log_memory_event(
                f"页面置换: 进程 {old_process_id} 的页面 {old_page_number} 被置换出帧 {victim_frame}"
            )

        # 加载新页面到被置换的帧
        new_page = Page(page_number, self.page_size)
        new_page.state = PageState.ALLOCATED
        new_page.process_id = process_id
        new_page.frame_number = victim_frame
        new_page.access_time = time.time()
        new_page.modified = is_write
        new_page.reference_count = 1

        self.physical_frames[victim_frame] = new_page
        self.page_tables[process_id][page_number] = new_page
        
        # 如果是FIFO算法, 将页面添加到队列
        if hasattr(self.page_replacement, 'add_page'):
            self.page_replacement.add_page(victim_frame)

        self.logger.log_memory_event(f"页面 {page_number} 加载到帧 {victim_frame}")
        return True
    
    def free_pages(self, process_id: int) -> bool:
        """
        释放进程的所有页面
        
        参数:
            process_id (int): 进程ID
            
        返回:
            bool: 释放是否成功
        """
        with self.lock:
            if process_id not in self.page_tables:
                return False
            
            for page in self.page_tables[process_id].values():
                if page.frame_number is not None:
                    self.physical_frames[page.frame_number] = None
                    self.free_pages.append(page.frame_number)
            
            del self.page_tables[process_id]
            self.logger.log_memory_event(f"释放进程 {process_id} 的所有页面")
            return True
    
    def get_memory_stats(self) -> Dict[str, float]:
        """
        获取内存统计信息
        
        返回:
            Dict[str, float]: 包含各种统计信息的字典
        """
        with self.lock:
            total_accesses = self.page_faults + self.page_hits
            fault_rate = self.page_faults / total_accesses if total_accesses > 0 else 0
            hit_rate = self.page_hits / total_accesses if total_accesses > 0 else 0
            
            return {
                'total_pages': self.total_pages,
                'free_pages': len(self.free_pages),
                'allocated_pages': self.total_pages - len(self.free_pages),
                'page_faults': self.page_faults,
                'page_hits': self.page_hits,
                'total_accesses': total_accesses,
                'fault_rate': fault_rate,
                'hit_rate': hit_rate,
                'replacement_algorithm': self.page_replacement.name
            }
    
    def print_memory_map(self):
        """打印内存映射表"""
        with self.lock:
            print(f"\n虚拟内存映射表 (使用算法: {self.page_replacement.name}):")
            print("=" * 80)
            print(f"{'帧号':<6} {'进程ID':<8} {'页面号':<8} {'状态':<12} {'引用位':<8} {'修改位':<8}")
            print("-" * 80)
            
            for i, page in enumerate(self.physical_frames):
                if page:
                    ref_bit = "1" if page.reference_bit else "0"
                    mod_bit = "1" if page.modified else "0"
                    print(f"{i:<6} {page.process_id:<8} {page.page_number:<8} {page.state.value:<12} {ref_bit:<8} {mod_bit:<8}")
                else:
                    print(f"{i:<6} {'FREE':<8} {'-':<8} {'FREE':<12} {'-':<8} {'-':<8}")
            
            print("-" * 80)
            stats = self.get_memory_stats()
            print(f"统计信息:")
            print(f"  总页面数: {stats['total_pages']}, 空闲页面: {stats['free_pages']}, 已分配页面: {stats['allocated_pages']}")
            print(f"  总访问次数: {stats['total_accesses']}, 缺页次数: {stats['page_faults']}, 命中次数: {stats['page_hits']}")
            print(f"  缺页率: {stats['fault_rate']:.2%}, 命中率: {stats['hit_rate']:.2%}")
            print("=" * 80)

# 示例使用函数
def demo_virtual_memory():
    """
    虚拟内存管理演示函数
    
    展示如何使用虚拟内存管理器, 包括:
    1. 创建虚拟内存管理器
    2. 为进程分配页面
    3. 访问内存地址
    4. 观察页面置换过程
    5. 查看统计信息
    """
    print("=== 虚拟内存管理演示 ===\n")
    
    # 创建虚拟内存管理器(使用较小的内存便于演示)
    vm = VirtualMemory(physical_memory_size=16*4096, page_size=4096, 
                      replacement_algorithm=PageReplacementAlgorithm.LRU)
    
    print("1. 为进程1分配3个页面")
    vm.allocate_pages(1, 3)
    vm.print_memory_map()
    
    print("\n2. 为进程2分配2个页面")
    vm.allocate_pages(2, 2)
    vm.print_memory_map()
    
    print("\n3. 访问进程1的内存地址")
    for i in range(5):
        vm.access_memory(1, i * 4096)
    vm.print_memory_map()
    
    print("\n4. 访问进程2的内存地址(触发页面置换)")
    for i in range(3):
        vm.access_memory(2, i * 4096)
    vm.print_memory_map()
    
    print("\n5. 释放进程1的所有页面")
    vm.free_pages(1)
    vm.print_memory_map()

if __name__ == "__main__":
    # 运行演示
    demo_virtual_memory()
