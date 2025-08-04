"""
虚拟内存管理包

本包提供了完整的虚拟内存管理功能，包括：
- 虚拟内存管理器 (VirtualMemory)
- 页面置换算法 (PageReplacementAlgorithm)
- 算法分析工具 (AlgorithmAnalyzer)

使用示例:
    from memory import VirtualMemory, PageReplacementAlgorithm
    
    # 创建虚拟内存管理器
    vm = VirtualMemory(replacement_algorithm=PageReplacementAlgorithm.LRU)
    
    # 分配页面
    vm.allocate_pages(1, 3)
    
    # 访问内存
    vm.access_memory(1, 0)
"""

from .virtual_memory import VirtualMemory, Page, PageState
from .page_replacement import (
    PageReplacementAlgorithm, 
    PageReplacementStrategy,
    FIFOStrategy,
    LRUStrategy,
    ClockStrategy,
    PageReplacementFactory,
    AlgorithmAnalyzer
)

__version__ = "1.0.0"
__author__ = "PyOS Tutorial"

__all__ = [
    # 核心类
    "VirtualMemory",
    "Page", 
    "PageState",
    
    # 页面置换算法
    "PageReplacementAlgorithm",
    "PageReplacementStrategy",
    "FIFOStrategy",
    "LRUStrategy", 
    "ClockStrategy",
    "PageReplacementFactory",
    
    # 工具类
    "AlgorithmAnalyzer",
] 