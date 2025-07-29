"""
虚拟内存模块 - 实现虚拟内存管理
"""

import threading
import time
from typing import Dict, List, Optional, Tuple
from enum import Enum

from utils.logger import Logger

class PageState(Enum):
    """页面状态枚举"""
    FREE = "free"
    ALLOCATED = "allocated"
    SWAPPED_OUT = "swapped_out"

class Page:
    """内存页面"""
    
    def __init__(self, page_number: int, size: int = 4096):
        self.page_number = page_number
        self.size = size
        self.state = PageState.FREE
        self.process_id = None
        self.frame_number = None
        self.access_time = 0
        self.modified = False
        self.reference_count = 0

class VirtualMemory:
    """虚拟内存管理器"""
    
    def __init__(self, physical_memory_size: int = 1024 * 1024, page_size: int = 4096):
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
        
        # 页面置换算法
        self.page_replacement = None  # 将在后续实现
        
        # 统计信息
        self.page_faults = 0
        self.page_hits = 0
        
        # 同步锁
        self.lock = threading.Lock()
        
        self.logger.info(f"虚拟内存管理器初始化: {physical_memory_size} bytes, {self.total_pages} pages")
    
    def allocate_pages(self, process_id: int, num_pages: int) -> bool:
        """为进程分配虚拟页面"""
        with self.lock:
            if num_pages > len(self.free_pages):
                self.logger.warning(f"物理内存不足，请求: {num_pages}, 可用: {len(self.free_pages)}")
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
                    
                    self.physical_frames[frame_number] = page
                    self.page_tables[process_id][page.page_number] = page
            
            self.logger.log_memory_event(f"为进程 {process_id} 分配了 {num_pages} 个页面")
            return True
    
    def access_memory(self, process_id: int, virtual_address: int) -> bool:
        """访问虚拟内存地址"""
        with self.lock:
            page_number = virtual_address // self.page_size
            offset = virtual_address % self.page_size
            
            if process_id not in self.page_tables:
                self.logger.error(f"进程 {process_id} 的页面表不存在")
                return False
            
            if page_number not in self.page_tables[process_id]:
                # 页面不存在，触发缺页中断
                self.page_faults += 1
                self.logger.log_memory_event(f"缺页中断: 进程 {process_id}, 页面 {page_number}")
                return self._handle_page_fault(process_id, page_number)
            else:
                # 页面存在，更新访问信息
                page = self.page_tables[process_id][page_number]
                page.access_time = time.time()
                page.reference_count += 1
                self.page_hits += 1
                return True
    
    def _handle_page_fault(self, process_id: int, page_number: int) -> bool:
        """处理缺页中断"""
        # TODO: 实现页面置换算法
        # 1. 查找空闲物理帧
        # 2. 如果没有空闲帧，进行页面置换
        # 3. 将页面加载到物理内存
        
        # 临时实现：简单分配
        if self.free_pages:
            frame_number = self.free_pages.pop(0)
            page = Page(page_number, self.page_size)
            page.state = PageState.ALLOCATED
            page.process_id = process_id
            page.frame_number = frame_number
            
            self.physical_frames[frame_number] = page
            self.page_tables[process_id][page_number] = page
            
            self.logger.log_memory_event(f"页面 {page_number} 加载到帧 {frame_number}")
            return True
        else:
            self.logger.error("没有可用的物理帧")
            return False
    
    def free_pages(self, process_id: int) -> bool:
        """释放进程的所有页面"""
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
    
    def get_memory_stats(self) -> Dict[str, int]:
        """获取内存统计信息"""
        with self.lock:
            return {
                'total_pages': self.total_pages,
                'free_pages': len(self.free_pages),
                'allocated_pages': self.total_pages - len(self.free_pages),
                'page_faults': self.page_faults,
                'page_hits': self.page_hits,
                'fault_rate': self.page_faults / (self.page_faults + self.page_hits) if (self.page_faults + self.page_hits) > 0 else 0
            }
    
    def print_memory_map(self):
        """打印内存映射"""
        with self.lock:
            print(f"\n虚拟内存映射:")
            print("-" * 60)
            print(f"{'帧号':<6} {'进程ID':<8} {'页面号':<8} {'状态':<12}")
            print("-" * 60)
            
            for i, page in enumerate(self.physical_frames):
                if page:
                    print(f"{i:<6} {page.process_id:<8} {page.page_number:<8} {page.state.value:<12}")
                else:
                    print(f"{i:<6} {'FREE':<8} {'-':<8} {'FREE':<12}")
            
            print("-" * 60)
            stats = self.get_memory_stats()
            print(f"统计: 总页面 {stats['total_pages']}, 空闲 {stats['free_pages']}, "
                  f"已分配 {stats['allocated_pages']}")
            print(f"缺页率: {stats['fault_rate']:.2%}") 