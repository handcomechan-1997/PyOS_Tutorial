"""
死锁模块 - 死锁检测、预防和避免

本模块实现操作系统中死锁相关的核心概念：
1. 死锁检测算法
2. 死锁预防策略
3. 银行家算法（死锁避免）
4. 资源分配图
"""

from .detector import DeadlockDetector, ResourceAllocationGraph
from .prevention import DeadlockPrevention
from .banker import BankersAlgorithm, ResourceManager

__all__ = [
    'DeadlockDetector',
    'ResourceAllocationGraph',
    'DeadlockPrevention',
    'BankersAlgorithm',
    'ResourceManager'
]
