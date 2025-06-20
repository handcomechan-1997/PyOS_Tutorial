"""
内存管理模块 - 负责虚拟内存、分页和内存分配
"""

from .virtual_memory import VirtualMemory
from .page_table import PageTable
from .memory_allocator import MemoryAllocator

__all__ = [
    'VirtualMemory',
    'PageTable', 
    'MemoryAllocator'
] 