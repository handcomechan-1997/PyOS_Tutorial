"""
内存管理高级概念 - TLB、页面置换算法

本模块实现：
1. TLB (Translation Lookaside Buffer)
2. 完整的页面置换算法 (LRU, Clock, LFU, etc.)
3. 工作集模型
"""

import time
from typing import Optional, Dict, List, Set, Tuple
from collections import OrderedDict, deque
from enum import Enum
from utils.logger import Logger


class PageReplacementAlgorithm(Enum):
    """页面置换算法"""
    FIFO = "fifo"
    LRU = "lru"
    CLOCK = "clock"
    LFU = "lfu"
    MFU = "mfu"
    OPTIMAL = "optimal"
    NRU = "nru"  # Not Recently Used


class TLBEntry:
    """TLB条目"""

    def __init__(self, page_number: int, frame_number: int):
        self.page_number = page_number
        self.frame_number = frame_number
        self.valid = True
        self.access_time = time.time()
        self.reference_bit = True
        self.dirty_bit = False

    def access(self, is_write: bool = False) -> None:
        """访问TLB条目"""
        self.access_time = time.time()
        self.reference_bit = True
        if is_write:
            self.dirty_bit = True


class TLB:
    """
    转换后备缓冲器 (Translation Lookaside Buffer)

    页表的硬件缓存，加速虚拟地址到物理地址的转换。
    """

    def __init__(self, size: int = 64):
        """
        初始化TLB

        Args:
            size: TLB条目数量
        """
        self._size = size
        self._entries: Dict[int, TLBEntry] = OrderedDict()
        self._lock = None  # 模拟中不需要真正的锁
        self._logger = Logger()

        # 统计
        self._hits = 0
        self._misses = 0

    def lookup(self, page_number: int) -> Optional[int]:
        """
        查找TLB

        Args:
            page_number: 页号

        Returns:
            Optional[int]: 页框号，未命中返回None
        """
        if page_number in self._entries:
            self._hits += 1
            entry = self._entries[page_number]
            entry.access()
            # LRU: 移到最后
            self._entries.move_to_end(page_number)
            self._logger.debug(f"TLB命中: 页 {page_number} -> 框 {entry.frame_number}")
            return entry.frame_number

        self._misses += 1
        self._logger.debug(f"TLB未命中: 页 {page_number}")
        return None

    def insert(self, page_number: int, frame_number: int) -> Optional[int]:
        """
        插入TLB条目

        Args:
            page_number: 页号
            frame_number: 页框号

        Returns:
            Optional[int]: 被替换的页号
        """
        replaced_page = None

        if len(self._entries) >= self._size:
            # LRU替换
            replaced_page, _ = self._entries.popitem(last=False)
            self._logger.debug(f"TLB替换: 移除页 {replaced_page}")

        self._entries[page_number] = TLBEntry(page_number, frame_number)
        self._logger.debug(f"TLB插入: 页 {page_number} -> 框 {frame_number}")

        return replaced_page

    def invalidate(self, page_number: int) -> bool:
        """使TLB条目失效"""
        if page_number in self._entries:
            del self._entries[page_number]
            return True
        return False

    def invalidate_all(self) -> None:
        """使所有TLB条目失效"""
        self._entries.clear()

    @property
    def hit_rate(self) -> float:
        """获取命中率"""
        total = self._hits + self._misses
        return (self._hits / total * 100) if total > 0 else 0

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'size': self._size,
            'entries': len(self._entries),
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': self.hit_rate
        }


class PageTableEntry:
    """页表条目"""

    def __init__(self, frame_number: int = -1):
        self.frame_number = frame_number
        self.valid = False
        self.present = False
        self.readable = True
        self.writable = True
        self.executable = False
        self.user_accessible = True
        self.referenced = False
        self.dirty = False
        self.access_time = 0
        self.last_access = 0


class PageFrame:
    """页框"""

    def __init__(self, frame_number: int):
        self.frame_number = frame_number
        self.page_number: Optional[int] = None
        self.process_id: Optional[int] = None
        self.is_free = True
        self.referenced = False
        self.dirty = False
        self.last_access = 0
        self.access_count = 0


class PageReplacer:
    """
    页面置换算法实现

    支持多种置换算法。
    """

    def __init__(self, algorithm: PageReplacementAlgorithm = PageReplacementAlgorithm.LRU):
        """
        初始化页面置换器

        Args:
            algorithm: 置换算法
        """
        self._algorithm = algorithm
        self._logger = Logger()

        # 用于不同算法的数据结构
        self._fifo_queue: deque = deque()
        self._lru_list: OrderedDict = OrderedDict()
        self._clock_hand = 0
        self._clock_frames: List[PageFrame] = []
        self._lfu_count: Dict[int, int] = {}

    def select_victim(self, frames: List[PageFrame]) -> Optional[PageFrame]:
        """
        选择牺牲页框

        Args:
            frames: 页框列表

        Returns:
            Optional[PageFrame]: 被选中的页框
        """
        if self._algorithm == PageReplacementAlgorithm.FIFO:
            return self._fifo_select(frames)
        elif self._algorithm == PageReplacementAlgorithm.LRU:
            return self._lru_select(frames)
        elif self._algorithm == PageReplacementAlgorithm.CLOCK:
            return self._clock_select(frames)
        elif self._algorithm == PageReplacementAlgorithm.LFU:
            return self._lfu_select(frames)
        else:
            return self._fifo_select(frames)

    def _fifo_select(self, frames: List[PageFrame]) -> Optional[PageFrame]:
        """FIFO算法"""
        for frame in frames:
            if not frame.is_free:
                return frame
        return frames[0] if frames else None

    def _lru_select(self, frames: List[PageFrame]) -> Optional[PageFrame]:
        """LRU算法 - 选择最近最少使用的"""
        victim = None
        min_access = float('inf')

        for frame in frames:
            if not frame.is_free and frame.last_access < min_access:
                min_access = frame.last_access
                victim = frame

        return victim or (frames[0] if frames else None)

    def _clock_select(self, frames: List[PageFrame]) -> Optional[PageFrame]:
        """Clock算法 - 二次机会算法"""
        n = len(frames)
        if n == 0:
            return None

        start = self._clock_hand
        while True:
            frame = frames[self._clock_hand]
            if not frame.is_free:
                if frame.referenced:
                    frame.referenced = False
                else:
                    self._clock_hand = (self._clock_hand + 1) % n
                    return frame

            self._clock_hand = (self._clock_hand + 1) % n
            if self._clock_hand == start:
                # 找不到可替换的，返回第一个非空闲页框
                for f in frames:
                    if not f.is_free:
                        return f
                return frames[0]

    def _lfu_select(self, frames: List[PageFrame]) -> Optional[PageFrame]:
        """LFU算法 - 选择访问次数最少的"""
        victim = None
        min_count = float('inf')

        for frame in frames:
            if not frame.is_free and frame.access_count < min_count:
                min_count = frame.access_count
                victim = frame

        return victim or (frames[0] if frames else None)

    def on_access(self, frame: PageFrame) -> None:
        """访问页框时更新状态"""
        frame.referenced = True
        frame.last_access = time.time()
        frame.access_count += 1


class WorkingSet:
    """
    工作集模型

    跟踪进程在最近一段时间内访问的页面集合。
    """

    def __init__(self, window_size: int = 10):
        """
        初始化工作集

        Args:
            window_size: 工作集窗口大小（访问次数）
        """
        self._window_size = window_size
        self._access_history: deque = deque()
        self._current_set: Set[int] = set()
        self._logger = Logger()

    def access(self, page_number: int) -> None:
        """记录页面访问"""
        self._access_history.append(page_number)
        self._current_set.add(page_number)

        # 维护窗口大小
        while len(self._access_history) > self._window_size:
            old_page = self._access_history.popleft()
            # 检查是否还有该页面的访问
            if old_page not in self._access_history:
                self._current_set.discard(old_page)

    def get_working_set(self) -> Set[int]:
        """获取当前工作集"""
        return self._current_set.copy()

    def get_working_set_size(self) -> int:
        """获取工作集大小"""
        return len(self._current_set)

    def is_in_working_set(self, page_number: int) -> bool:
        """检查页面是否在工作集中"""
        return page_number in self._current_set


class AdvancedMemoryManager:
    """
    高级内存管理器

    集成TLB、页表和页面置换。
    """

    def __init__(self, total_frames: int = 256, page_size: int = 4096,
                 tlb_size: int = 64,
                 algorithm: PageReplacementAlgorithm = PageReplacementAlgorithm.LRU):
        """
        初始化高级内存管理器

        Args:
            total_frames: 总页框数
            page_size: 页面大小
            tlb_size: TLB大小
            algorithm: 页面置换算法
        """
        self._total_frames = total_frames
        self._page_size = page_size
        self._tlb = TLB(tlb_size)
        self._replacer = PageReplacer(algorithm)
        self._logger = Logger()

        # 页框
        self._frames: List[PageFrame] = [
            PageFrame(i) for i in range(total_frames)
        ]

        # 页表 (每个进程一个)
        self._page_tables: Dict[int, Dict[int, PageTableEntry]] = {}

        # 工作集
        self._working_sets: Dict[int, WorkingSet] = {}

        # 统计
        self._page_faults = 0
        self._total_accesses = 0

    def create_process_page_table(self, pid: int) -> None:
        """为进程创建页表"""
        self._page_tables[pid] = {}
        self._working_sets[pid] = WorkingSet()

    def access_memory(self, pid: int, virtual_address: int,
                     is_write: bool = False) -> Tuple[bool, int]:
        """
        访问内存

        Args:
            pid: 进程ID
            virtual_address: 虚拟地址
            is_write: 是否是写操作

        Returns:
            Tuple[bool, int]: (是否成功, 物理地址)
        """
        self._total_accesses += 1

        # 计算页号和偏移
        page_number = virtual_address // self._page_size
        offset = virtual_address % self._page_size

        # 1. 查找TLB
        frame_number = self._tlb.lookup(page_number)
        if frame_number is not None:
            # TLB命中
            frame = self._frames[frame_number]
            self._replacer.on_access(frame)
            if is_write:
                frame.dirty = True
            return True, frame_number * self._page_size + offset

        # 2. TLB未命中，查找页表
        page_table = self._page_tables.get(pid, {})
        pte = page_table.get(page_number)

        if pte and pte.present:
            # 页表命中
            frame_number = pte.frame_number
            self._tlb.insert(page_number, frame_number)
            frame = self._frames[frame_number]
            self._replacer.on_access(frame)
            if is_write:
                frame.dirty = True
                pte.dirty = True
            pte.referenced = True
            return True, frame_number * self._page_size + offset

        # 3. 页面错误
        self._page_faults += 1
        return self._handle_page_fault(pid, page_number, offset, is_write)

    def _handle_page_fault(self, pid: int, page_number: int,
                          offset: int, is_write: bool) -> Tuple[bool, int]:
        """处理页面错误"""
        self._logger.debug(f"页面错误: 进程 {pid}, 页 {page_number}")

        # 查找空闲页框
        free_frame = None
        for frame in self._frames:
            if frame.is_free:
                free_frame = frame
                break

        if free_frame:
            # 有空闲页框
            frame_number = free_frame.frame_number
        else:
            # 需要页面置换
            victim = self._replacer.select_victim(self._frames)
            if victim is None:
                return False, 0

            # 写回脏页
            if victim.dirty:
                self._logger.debug(f"写回脏页: 框 {victim.frame_number}")

            # 更新旧页表条目
            old_pid = victim.process_id
            old_page = victim.page_number
            if old_pid in self._page_tables:
                old_pte = self._page_tables[old_pid].get(old_page)
                if old_pte:
                    old_pte.present = False

            # 使TLB条目失效
            self._tlb.invalidate(old_page)

            frame_number = victim.frame_number

        # 加载新页面
        frame = self._frames[frame_number]
        frame.is_free = False
        frame.page_number = page_number
        frame.process_id = pid
        frame.referenced = True
        frame.dirty = is_write
        frame.last_access = time.time()
        frame.access_count = 1

        # 更新页表
        if pid not in self._page_tables:
            self._page_tables[pid] = {}

        pte = PageTableEntry(frame_number)
        pte.present = True
        pte.valid = True
        pte.referenced = True
        pte.dirty = is_write
        self._page_tables[pid][page_number] = pte

        # 更新TLB
        self._tlb.insert(page_number, frame_number)

        # 更新工作集
        if pid in self._working_sets:
            self._working_sets[pid].access(page_number)

        return True, frame_number * self._page_size + offset

    def get_page_fault_rate(self) -> float:
        """获取页面错误率"""
        return (self._page_faults / self._total_accesses * 100
                if self._total_accesses > 0 else 0)

    def get_stats(self) -> dict:
        """获取统计信息"""
        free_frames = sum(1 for f in self._frames if f.is_free)

        return {
            'total_frames': self._total_frames,
            'free_frames': free_frames,
            'used_frames': self._total_frames - free_frames,
            'page_faults': self._page_faults,
            'total_accesses': self._total_accesses,
            'page_fault_rate': self.get_page_fault_rate(),
            'tlb_stats': self._tlb.get_stats()
        }


# 使用示例
if __name__ == "__main__":
    print("=== 内存管理高级概念演示 ===\n")

    # 创建内存管理器
    mm = AdvancedMemoryManager(
        total_frames=16,
        page_size=4096,
        tlb_size=8,
        algorithm=PageReplacementAlgorithm.LRU
    )

    # 创建进程页表
    mm.create_process_page_table(pid=1)

    print("1. 模拟内存访问")
    # 模拟访问序列
    addresses = [0, 4096, 8192, 12288, 4096, 0, 16384, 4096]

    for addr in addresses:
        success, phys = mm.access_memory(1, addr)
        page = addr // 4096
        print(f"  访问虚拟地址 {addr} (页 {page}): "
              f"{'成功' if success else '失败'}, 物理地址 {phys}")

    print(f"\n2. TLB统计")
    print(f"  {mm._tlb.get_stats()}")

    print(f"\n3. 内存管理统计")
    print(f"  页面错误: {mm._page_faults}")
    print(f"  页面错误率: {mm.get_page_fault_rate():.1f}%")

    print("\n演示完成！")
