"""
内存管理器 - 负责内存的分配、回收和管理
"""

import threading
import time
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum

from memory.memory_allocator import MemoryAllocator, AllocationStrategy
from memory.virtual_memory import VirtualMemory
from memory.page_table import PageTable
from utils.logger import Logger

class MemoryType(Enum):
    """内存类型枚举"""
    PHYSICAL = "physical"      # 物理内存
    VIRTUAL = "virtual"        # 虚拟内存
    SHARED = "shared"          # 共享内存

class MemoryProtection(Enum):
    """内存保护级别"""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    EXECUTE = "execute"
    NONE = "none"

class MemoryManager:
    """内存管理器 - 统一管理物理内存和虚拟内存"""
    
    def __init__(self, total_memory: int = 1024 * 1024, page_size: int = 4096):
        """初始化内存管理器"""
        self.logger = Logger()
        self.total_memory = total_memory
        self.page_size = page_size
        
        # 内存分配器
        self.memory_allocator = MemoryAllocator(total_memory, AllocationStrategy.FIRST_FIT)
        
        # 虚拟内存管理器
        self.virtual_memory = VirtualMemory(total_memory, page_size)
        
        # 页表管理 (进程ID -> 页表)
        self.page_tables: Dict[int, PageTable] = {}
        
        # 进程内存映射 (进程ID -> 内存信息)
        self.process_memory: Dict[int, Dict[str, Union[int, List[int]]]] = {}
        
        # 共享内存区域
        self.shared_memory: Dict[str, Dict[str, Union[int, int, List[int]]]] = {}
        
        # 内存统计
        self.total_allocated = 0
        self.total_freed = 0
        self.allocation_count = 0
        self.deallocation_count = 0
        
        # 同步锁
        self.lock = threading.Lock()
        
        self.logger.info(f"内存管理器初始化: 总内存 {total_memory} bytes, 页面大小 {page_size} bytes")
    
    def initialize(self):
        """初始化内存管理器"""
        self.logger.info("初始化内存管理器...")
        
        try:
            # 初始化内存分配器
            self.logger.info("初始化内存分配器...")
            # 内存分配器已在构造函数中初始化
            
            # 初始化虚拟内存管理器
            self.logger.info("初始化虚拟内存管理器...")
            # 虚拟内存管理器已在构造函数中初始化
            
            # 创建系统保留内存区域
            self._create_system_reserved_memory()
            
            self.logger.info("内存管理器初始化完成")
            
        except Exception as e:
            self.logger.error(f"内存管理器初始化失败: {e}")
            raise
    
    def _create_system_reserved_memory(self):
        """创建系统保留内存区域"""
        # 为系统保留一些内存
        system_memory_size = min(self.total_memory // 10, 64 * 1024)  # 最多64KB或总内存的10%
        
        if system_memory_size > 0:
            self.memory_allocator.allocate(system_memory_size, 0)  # 进程ID 0 表示系统
            self.logger.info(f"为系统保留内存: {system_memory_size} bytes")
    
    def allocate_memory(self, pid: int, size: int, memory_type: MemoryType = MemoryType.PHYSICAL) -> Optional[int]:
        """为进程分配内存"""
        with self.lock:
            try:
                if size <= 0:
                    self.logger.warning(f"无效的内存分配请求: 进程 {pid}, 大小 {size}")
                    return None
                
                if memory_type == MemoryType.PHYSICAL:
                    # 物理内存分配
                    address = self._allocate_physical_memory(pid, size)
                elif memory_type == MemoryType.VIRTUAL:
                    # 虚拟内存分配
                    address = self._allocate_virtual_memory(pid, size)
                elif memory_type == MemoryType.SHARED:
                    # 共享内存分配
                    address = self._allocate_shared_memory(pid, size)
                else:
                    self.logger.error(f"不支持的内存类型: {memory_type}")
                    return None
                
                if address is not None:
                    self._update_process_memory(pid, address, size, memory_type)
                    self.allocation_count += 1
                    self.total_allocated += size
                    self.logger.log_memory_event(f"内存分配成功: 进程 {pid}, 大小 {size}, 地址 {address}, 类型 {memory_type.value}")
                
                return address
                
            except Exception as e:
                self.logger.error(f"内存分配失败: 进程 {pid}, 大小 {size}, 错误 {e}")
                return None
    
    def _allocate_physical_memory(self, pid: int, size: int) -> Optional[int]:
        """分配物理内存"""
        return self.memory_allocator.allocate(size, pid)
    
    def _allocate_virtual_memory(self, pid: int, size: int) -> Optional[int]:
        """分配虚拟内存"""
        # 计算需要的页面数
        num_pages = (size + self.page_size - 1) // self.page_size
        
        # 确保进程有页表
        if pid not in self.page_tables:
            self.page_tables[pid] = PageTable(pid)
        
        # 分配虚拟页面
        if self.virtual_memory.allocate_pages(pid, num_pages):
            # 返回虚拟地址（这里简化处理，实际应该返回虚拟地址）
            return self.total_allocated  # 临时返回一个地址
        else:
            return None
    
    def _allocate_shared_memory(self, pid: int, size: int) -> Optional[int]:
        """分配共享内存"""
        # 生成共享内存标识符
        shared_id = f"shared_{pid}_{int(time.time())}"
        
        # 分配物理内存
        address = self.memory_allocator.allocate(size, pid)
        if address is not None:
            self.shared_memory[shared_id] = {
                'address': address,
                'size': size,
                'owner_pid': pid,
                'access_pids': [pid]
            }
            return address
        
        return None
    
    def _update_process_memory(self, pid: int, address: int, size: int, memory_type: MemoryType):
        """更新进程内存信息"""
        if pid not in self.process_memory:
            self.process_memory[pid] = {
                'total_allocated': 0,
                'physical_addresses': [],
                'virtual_addresses': [],
                'shared_addresses': []
            }
        
        self.process_memory[pid]['total_allocated'] += size
        
        if memory_type == MemoryType.PHYSICAL:
            self.process_memory[pid]['physical_addresses'].append(address)
        elif memory_type == MemoryType.VIRTUAL:
            self.process_memory[pid]['virtual_addresses'].append(address)
        elif memory_type == MemoryType.SHARED:
            self.process_memory[pid]['shared_addresses'].append(address)
    
    def free_memory(self, pid: int, address: Optional[int] = None) -> bool:
        """释放进程内存"""
        with self.lock:
            try:
                if pid not in self.process_memory:
                    self.logger.warning(f"进程 {pid} 没有分配的内存")
                    return False
                
                if address is not None:
                    # 释放指定地址的内存
                    return self._free_specific_memory(pid, address)
                else:
                    # 释放进程的所有内存
                    return self._free_all_process_memory(pid)
                
            except Exception as e:
                self.logger.error(f"内存释放失败: 进程 {pid}, 错误 {e}")
                return False
    
    def _free_specific_memory(self, pid: int, address: int) -> bool:
        """释放指定地址的内存"""
        # 检查是否是物理内存
        if address in self.process_memory[pid]['physical_addresses']:
            if self.memory_allocator.deallocate(address):
                self.process_memory[pid]['physical_addresses'].remove(address)
                self.deallocation_count += 1
                self.logger.log_memory_event(f"释放物理内存: 进程 {pid}, 地址 {address}")
                return True
        
        # 检查是否是共享内存
        for shared_id, shared_info in self.shared_memory.items():
            if shared_info['address'] == address and pid in shared_info['access_pids']:
                shared_info['access_pids'].remove(pid)
                if not shared_info['access_pids']:
                    # 没有进程访问了，释放共享内存
                    if self.memory_allocator.deallocate(address):
                        del self.shared_memory[shared_id]
                        self.deallocation_count += 1
                        self.logger.log_memory_event(f"释放共享内存: 进程 {pid}, 地址 {address}")
                        return True
        
        # 检查是否是虚拟内存
        if address in self.process_memory[pid]['virtual_addresses']:
            # 释放虚拟内存页面
            if self.virtual_memory.free_pages(pid):
                self.process_memory[pid]['virtual_addresses'].remove(address)
                self.deallocation_count += 1
                self.logger.log_memory_event(f"释放虚拟内存: 进程 {pid}, 地址 {address}")
                return True
        
        self.logger.warning(f"未找到要释放的内存: 进程 {pid}, 地址 {address}")
        return False
    
    def _free_all_process_memory(self, pid: int) -> bool:
        """释放进程的所有内存"""
        success = True
        
        # 释放物理内存
        for address in self.process_memory[pid]['physical_addresses'][:]:
            if not self._free_specific_memory(pid, address):
                success = False
        
        # 释放虚拟内存
        if pid in self.page_tables:
            if self.virtual_memory.free_pages(pid):
                del self.page_tables[pid]
            else:
                success = False
        
        # 清理进程内存记录
        if pid in self.process_memory:
            del self.process_memory[pid]
        
        self.logger.log_memory_event(f"释放进程 {pid} 的所有内存")
        return success
    
    def get_memory_usage(self) -> Dict[str, Union[int, float]]:
        """获取内存使用情况"""
        with self.lock:
            # 获取内存分配器统计
            allocator_stats = self.memory_allocator.get_memory_stats()
            
            # 获取虚拟内存统计
            virtual_stats = self.virtual_memory.get_memory_stats()
            
            # 计算进程内存使用
            process_count = len(self.process_memory)
            total_process_memory = sum(info['total_allocated'] for info in self.process_memory.values())
            
            # 计算共享内存使用
            shared_memory_count = len(self.shared_memory)
            total_shared_memory = sum(info['size'] for info in self.shared_memory.values())
            
            return {
                'total_memory': self.total_memory,
                'allocated_memory': allocator_stats['allocated_memory'],
                'free_memory': allocator_stats['free_memory'],
                'utilization': allocator_stats['utilization'],
                'process_count': process_count,
                'total_process_memory': total_process_memory,
                'shared_memory_count': shared_memory_count,
                'total_shared_memory': total_shared_memory,
                'virtual_pages': virtual_stats['total_pages'],
                'allocated_virtual_pages': virtual_stats['allocated_pages'],
                'page_faults': virtual_stats['page_faults'],
                'page_hits': virtual_stats['page_hits'],
                'fault_rate': virtual_stats['fault_rate'],
                'allocation_count': self.allocation_count,
                'deallocation_count': self.deallocation_count
            }
    
    def get_process_memory_info(self, pid: int) -> Optional[Dict[str, Union[int, List[int]]]]:
        """获取进程内存信息"""
        with self.lock:
            if pid in self.process_memory:
                return self.process_memory[pid].copy()
            return None
    
    def print_memory_status(self):
        """打印内存状态"""
        with self.lock:
            print(f"\n内存管理器状态:")
            print("=" * 60)
            
            # 总体统计
            usage = self.get_memory_usage()
            print(f"总内存: {usage['total_memory']:,} bytes")
            print(f"已分配: {usage['allocated_memory']:,} bytes")
            print(f"空闲内存: {usage['free_memory']:,} bytes")
            print(f"利用率: {usage['utilization']:.1f}%")
            print(f"进程数: {usage['process_count']}")
            print(f"共享内存区域: {usage['shared_memory_count']}")
            
            # 虚拟内存统计
            print(f"\n虚拟内存:")
            print(f"  总页面: {usage['virtual_pages']}")
            print(f"  已分配页面: {usage['allocated_virtual_pages']}")
            print(f"  缺页次数: {usage['page_faults']}")
            print(f"  命中次数: {usage['page_hits']}")
            print(f"  缺页率: {usage['fault_rate']:.2%}")
            
            # 分配统计
            print(f"\n分配统计:")
            print(f"  分配次数: {usage['allocation_count']}")
            print(f"  释放次数: {usage['deallocation_count']}")
            
            # 进程内存详情
            if self.process_memory:
                print(f"\n进程内存详情:")
                for pid, info in self.process_memory.items():
                    print(f"  进程 {pid}: {info['total_allocated']:,} bytes")
                    if info['physical_addresses']:
                        print(f"    物理地址: {len(info['physical_addresses'])} 个")
                    if info['virtual_addresses']:
                        print(f"    虚拟地址: {len(info['virtual_addresses'])} 个")
                    if info['shared_addresses']:
                        print(f"    共享地址: {len(info['shared_addresses'])} 个")
    
    def cleanup(self):
        """清理内存管理器"""
        self.logger.info("清理内存管理器...")
        
        try:
            # 释放所有进程的内存
            for pid in list(self.process_memory.keys()):
                self.free_memory(pid)
            
            # 清理共享内存
            for shared_id in list(self.shared_memory.keys()):
                shared_info = self.shared_memory[shared_id]
                self.memory_allocator.deallocate(shared_info['address'])
            
            # 清理页表
            self.page_tables.clear()
            
            # 清理进程内存记录
            self.process_memory.clear()
            
            # 清理共享内存记录
            self.shared_memory.clear()
            
            self.logger.info("内存管理器清理完成")
            
        except Exception as e:
            self.logger.error(f"内存管理器清理失败: {e}")
    
    def defragment_memory(self) -> bool:
        """内存碎片整理"""
        with self.lock:
            try:
                self.logger.info("开始内存碎片整理...")
                
                # 调用内存分配器的碎片整理
                self.memory_allocator.defragment()
                
                self.logger.info("内存碎片整理完成")
                return True
                
            except Exception as e:
                self.logger.error(f"内存碎片整理失败: {e}")
                return False 