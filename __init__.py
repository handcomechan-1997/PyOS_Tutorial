"""
PyOS Tutorial Package

Python简单操作系统教学演示包

本包实现了操作系统核心概念的Python演示，包括：
- 进程管理
- 内存管理（虚拟内存、页面置换）
- 文件系统
- 设备管理
- 系统调用

使用示例:
    from pyos_tutorial import VirtualMemory, PageReplacementAlgorithm
    
    # 创建虚拟内存管理器
    vm = VirtualMemory(replacement_algorithm=PageReplacementAlgorithm.LRU)
    
    # 分配页面
    vm.allocate_pages(1, 3)
    
    # 访问内存
    vm.access_memory(1, 0)
"""

__version__ = "1.0.0"
__author__ = "HandsomeChen"
__email__ = "handsomechen@example.com"

# 导出主要的模块和类
from .memory import (
    VirtualMemory,
    PageReplacementAlgorithm,
    AlgorithmAnalyzer,
    Page,
    PageState
)

from .process import Process, ProcessManager
from .filesystem import FileSystem, File, Directory
from .device import DeviceManager
from .kernel import Kernel

__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__email__",
    
    # 内存管理
    "VirtualMemory",
    "PageReplacementAlgorithm", 
    "AlgorithmAnalyzer",
    "Page",
    "PageState",
    
    # 进程管理
    "Process",
    "ProcessManager",
    
    # 文件系统
    "FileSystem",
    "File", 
    "Directory",
    
    # 设备管理
    "DeviceManager",
    
    # 内核
    "Kernel",
] 