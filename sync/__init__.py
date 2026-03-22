"""
同步模块 - 进程同步与互斥

本模块实现操作系统中核心的同步原语，是理解并发编程的基础。
"""

from .semaphore import Semaphore, BinarySemaphore, CountingSemaphore
from .mutex import Mutex, RecursiveMutex
from .condition import ConditionVariable
from .rwlock import ReadWriteLock
from .spinlock import SpinLock
from .barrier import Barrier
from .classic_problems import (
    ProducerConsumer,
    ReadersWriters,
    DiningPhilosophers,
    SleepingBarber
)

__all__ = [
    'Semaphore',
    'BinarySemaphore',
    'CountingSemaphore',
    'Mutex',
    'RecursiveMutex',
    'ConditionVariable',
    'ReadWriteLock',
    'SpinLock',
    'Barrier',
    'ProducerConsumer',
    'ReadersWriters',
    'DiningPhilosophers',
    'SleepingBarber'
]
