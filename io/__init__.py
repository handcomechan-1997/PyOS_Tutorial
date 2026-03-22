"""
I/O系统模块 - I/O调度、缓冲区管理、DMA

本模块实现：
1. I/O调度算法
2. 缓冲区管理
3. DMA (直接内存访问) 模拟
4. I/O请求队列管理
"""

from .scheduler import IOScheduler, IORequest
from .buffer import BufferManager, Buffer, CircularBuffer
from .dma import DMAController, DMATransfer

__all__ = [
    'IOScheduler',
    'IORequest',
    'BufferManager',
    'Buffer',
    'CircularBuffer',
    'DMAController',
    'DMATransfer'
]
