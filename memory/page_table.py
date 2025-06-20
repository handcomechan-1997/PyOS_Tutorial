"""
页表管理模块 - 管理进程的页表
"""

import threading
from typing import Dict, List, Optional, Tuple
from enum import Enum

from utils.logger import Logger

class PageTableEntry:
    """页表项"""
    
    def __init__(self, virtual_page: int, physical_frame: Optional[int] = None):
        self.virtual_page = virtual_page
        self.physical_frame = physical_frame
        self.present = physical_frame is not None
        self.accessed = False
        self.modified = False
        self.protection = 0  # 保护位
        self.reference_count = 0
        self.access_time = 0

class PageTable:
    """页表"""
    
    def __init__(self, process_id: int):
        """初始化页表"""
        self.process_id = process_id
        self.entries: Dict[int, PageTableEntry] = {}
        self.logger = Logger()
        self.lock = threading.Lock()
    
    def add_entry(self, virtual_page: int, physical_frame: Optional[int] = None) -> PageTableEntry:
        """添加页表项"""
        with self.lock:
            entry = PageTableEntry(virtual_page, physical_frame)
            self.entries[virtual_page] = entry
            self.logger.log_memory_event(f"添加页表项: 进程 {self.process_id}, 虚拟页 {virtual_page}")
            return entry
    
    def get_entry(self, virtual_page: int) -> Optional[PageTableEntry]:
        """获取页表项"""
        with self.lock:
            return self.entries.get(virtual_page)
    
    def update_entry(self, virtual_page: int, physical_frame: int):
        """更新页表项"""
        with self.lock:
            if virtual_page in self.entries:
                entry = self.entries[virtual_page]
                entry.physical_frame = physical_frame
                entry.present = True
                entry.accessed = True
                self.logger.log_memory_event(f"更新页表项: 进程 {self.process_id}, 虚拟页 {virtual_page} -> 物理帧 {physical_frame}")
    
    def remove_entry(self, virtual_page: int) -> bool:
        """移除页表项"""
        with self.lock:
            if virtual_page in self.entries:
                del self.entries[virtual_page]
                self.logger.log_memory_event(f"移除页表项: 进程 {self.process_id}, 虚拟页 {virtual_page}")
                return True
            return False
    
    def is_present(self, virtual_page: int) -> bool:
        """检查页面是否在内存中"""
        with self.lock:
            entry = self.entries.get(virtual_page)
            return entry is not None and entry.present
    
    def get_physical_frame(self, virtual_page: int) -> Optional[int]:
        """获取物理帧号"""
        with self.lock:
            entry = self.entries.get(virtual_page)
            return entry.physical_frame if entry and entry.present else None
    
    def mark_accessed(self, virtual_page: int):
        """标记页面被访问"""
        with self.lock:
            if virtual_page in self.entries:
                entry = self.entries[virtual_page]
                entry.accessed = True
                entry.reference_count += 1
                entry.access_time = time.time()
    
    def mark_modified(self, virtual_page: int):
        """标记页面被修改"""
        with self.lock:
            if virtual_page in self.entries:
                entry = self.entries[virtual_page]
                entry.modified = True
    
    def get_stats(self) -> Dict[str, int]:
        """获取页表统计信息"""
        with self.lock:
            total_entries = len(self.entries)
            present_entries = sum(1 for entry in self.entries.values() if entry.present)
            accessed_entries = sum(1 for entry in self.entries.values() if entry.accessed)
            modified_entries = sum(1 for entry in self.entries.values() if entry.modified)
            
            return {
                'total_entries': total_entries,
                'present_entries': present_entries,
                'accessed_entries': accessed_entries,
                'modified_entries': modified_entries
            }
    
    def print_page_table(self):
        """打印页表"""
        with self.lock:
            print(f"\n进程 {self.process_id} 的页表:")
            print("-" * 80)
            print(f"{'虚拟页':<8} {'物理帧':<8} {'存在':<6} {'访问':<6} {'修改':<6} {'引用次数':<8}")
            print("-" * 80)
            
            for virtual_page, entry in sorted(self.entries.items()):
                physical_frame = entry.physical_frame if entry.present else "N/A"
                present = "是" if entry.present else "否"
                accessed = "是" if entry.accessed else "否"
                modified = "是" if entry.modified else "否"
                
                print(f"{virtual_page:<8} {physical_frame:<8} {present:<6} {accessed:<6} {modified:<6} {entry.reference_count:<8}")
            
            print("-" * 80)
            stats = self.get_stats()
            print(f"统计: 总项数 {stats['total_entries']}, 存在 {stats['present_entries']}, "
                  f"已访问 {stats['accessed_entries']}, 已修改 {stats['modified_entries']}")

# 导入时间模块
import time 