"""
页面置换算法模块

本模块实现了各种页面置换算法, 包括:
- FIFO (First In First Out)
- LRU (Least Recently Used)  
- Clock (时钟算法)

教学要点:
- 理解不同页面置换算法的原理
- 掌握策略模式的设计思想
- 学习算法的性能特点
"""

import time
import sys
import os
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from collections import deque
from enum import Enum

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 避免循环导入
if TYPE_CHECKING:
    from memory.virtual_memory import VirtualMemory

class PageReplacementAlgorithm(Enum):
    """页面置换算法枚举"""
    FIFO = "fifo"      # 先进先出算法
    LRU = "lru"        # 最近最少使用算法
    CLOCK = "clock"    # 时钟算法

class PageReplacementStrategy:
    """
    页面置换策略基类
    
    定义了页面置换算法的接口, 所有具体的置换算法都应该继承此类.
    这是策略模式的典型应用.
    
    教学要点:
    - 策略模式: 定义算法族, 分别封装, 让它们之间可以互相替换
    - 开闭原则: 对扩展开放, 对修改封闭
    - 多态性: 通过基类接口调用具体算法
    """
    
    def __init__(self, virtual_memory: 'VirtualMemory'):
        self.virtual_memory = virtual_memory
        self.name = "Base"
    
    def select_victim(self) -> Optional[Tuple['Page', int]]:
        """
        选择要置换的页面
        
        返回:
            Tuple[Page, int]: (被置换的页面, 物理帧号) 或 None
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def update_reference(self, page: 'Page'):
        """
        更新页面引用信息
        
        参数:
            page (Page): 被访问的页面
        """
        raise NotImplementedError("子类必须实现此方法")

class FIFOStrategy(PageReplacementStrategy):
    """
    先进先出(FIFO)页面置换算法
    
    原理: 选择最早进入内存的页面进行置换
    优点: 实现简单, 开销小
    缺点: 不考虑页面的使用频率, 性能可能较差
    适用场景: 对性能要求不高的简单系统
    
    教学要点:
    - 队列数据结构的使用
    - 简单但有效的算法设计
    - 性能与复杂度的权衡
    """
    
    def __init__(self, virtual_memory: 'VirtualMemory'):
        super().__init__(virtual_memory)
        self.name = "FIFO"
        self.page_queue = deque()  # 存储页面进入内存的顺序
    
    def select_victim(self) -> Optional[Tuple['Page', int]]:
        """选择最早进入内存的页面进行置换"""
        if not self.page_queue:
            return None
        
        # 获取队列头部的页面
        frame_number = self.page_queue.popleft()
        page = self.virtual_memory.physical_frames[frame_number]
        
        if page:
            return (page, frame_number)
        return None
    
    def update_reference(self, page: 'Page'):
        """FIFO算法不需要更新引用信息"""
        pass
    
    def add_page(self, frame_number: int):
        """将新页面添加到队列尾部"""
        self.page_queue.append(frame_number)

class LRUStrategy(PageReplacementStrategy):
    """
    最近最少使用(LRU)页面置换算法
    
    原理: 选择最久未被访问的页面进行置换
    优点: 考虑了页面的使用频率, 性能较好
    缺点: 需要记录每个页面的访问时间, 开销较大
    适用场景: 对性能要求较高的系统
    
    教学要点:
    - 时间戳的使用
    - 全局最优策略
    - 空间换时间的思想
    """
    
    def __init__(self, virtual_memory: 'VirtualMemory'):
        super().__init__(virtual_memory)
        self.name = "LRU"
    
    def select_victim(self) -> Optional[Tuple['Page', int]]:
        """选择最久未被访问的页面进行置换"""
        lru_page = None
        lru_frame = None
        oldest_time = float('inf')
        
        for frame_idx, page in enumerate(self.virtual_memory.physical_frames):
            if page and page.access_time < oldest_time:
                oldest_time = page.access_time
                lru_page = page
                lru_frame = frame_idx
        
        if lru_page:
            return (lru_page, lru_frame)
        return None
    
    def update_reference(self, page: 'Page'):
        """更新页面的访问时间"""
        page.access_time = time.time()

class ClockStrategy(PageReplacementStrategy):
    """
    时钟(Clock)页面置换算法
    
    原理: 使用循环队列和引用位, 选择引用位为0的页面进行置换
    优点: 实现相对简单, 性能介于FIFO和LRU之间
    缺点: 仍然可能置换掉有用的页面
    适用场景: 平衡性能和复杂度的系统
    
    教学要点:
    - 引用位的使用
    - 循环扫描策略
    - 近似LRU算法
    """
    
    def __init__(self, virtual_memory: 'VirtualMemory'):
        super().__init__(virtual_memory)
        self.name = "Clock"
        self.clock_hand = 0  # 时钟指针
    
    def select_victim(self) -> Optional[Tuple['Page', int]]:
        """使用时钟算法选择要置换的页面"""
        start_hand = self.clock_hand
        
        while True:
            page = self.virtual_memory.physical_frames[self.clock_hand]
            
            if page is None:
                # 空闲帧, 直接使用
                frame_number = self.clock_hand
                self.clock_hand = (self.clock_hand + 1) % len(self.virtual_memory.physical_frames)
                return (None, frame_number)
            
            if not page.reference_bit:
                # 引用位为0, 选择此页面进行置换
                frame_number = self.clock_hand
                self.clock_hand = (self.clock_hand + 1) % len(self.virtual_memory.physical_frames)
                return (page, frame_number)
            else:
                # 引用位为1, 重置为0并继续查找
                page.reference_bit = False
                self.clock_hand = (self.clock_hand + 1) % len(self.virtual_memory.physical_frames)
                
                # 防止无限循环
                if self.clock_hand == start_hand:
                    # 所有页面引用位都为1, 重置所有引用位
                    for p in self.virtual_memory.physical_frames:
                        if p:
                            p.reference_bit = False
                    # 选择第一个页面
                    page = self.virtual_memory.physical_frames[0]
                    return (page, 0) if page else (None, 0)
    
    def update_reference(self, page: 'Page'):
        """设置页面的引用位为1"""
        page.reference_bit = True

# 算法工厂类
class PageReplacementFactory:
    """
    页面置换算法工厂类
    
    负责创建具体的页面置换算法实例.
    这是工厂模式的典型应用.
    
    教学要点:
    - 工厂模式: 封装对象创建逻辑
    - 依赖注入: 通过工厂创建依赖对象
    - 配置驱动: 通过枚举选择算法
    """
    
    @staticmethod
    def create_algorithm(algorithm: PageReplacementAlgorithm, virtual_memory: 'VirtualMemory') -> PageReplacementStrategy:
        """
        创建页面置换算法实例
        
        参数:
            algorithm (PageReplacementAlgorithm): 算法类型
            virtual_memory (VirtualMemory): 虚拟内存管理器
            
        返回:
            PageReplacementStrategy: 算法实例
        """
        if algorithm.value == "fifo":
            return FIFOStrategy(virtual_memory)
        elif algorithm.value == "lru":
            return LRUStrategy(virtual_memory)
        elif algorithm.value == "clock":
            return ClockStrategy(virtual_memory)
        else:
            raise ValueError(f"不支持的页面置换算法: {algorithm}")

# 算法性能分析工具
class AlgorithmAnalyzer:
    """
    算法性能分析工具
    
    用于比较不同页面置换算法的性能.
    
    教学要点:
    - 性能测试方法
    - 数据收集和分析
    - 算法评估标准
    """
    
    def __init__(self):
        self.results = {}
    
    def analyze_algorithm(self, algorithm: PageReplacementAlgorithm, 
                         access_pattern: List[int], 
                         memory_size: int = 4) -> Dict[str, float]:
        """
        分析单个算法的性能
        
        参数:
            algorithm (PageReplacementAlgorithm): 要分析的算法
            access_pattern (List[int]): 访问模式
            memory_size (int): 物理内存大小(页面数)
            
        返回:
            Dict[str, float]: 性能指标
        """
        # 延迟导入避免循环导入
        from memory.virtual_memory import VirtualMemory
        
        # 创建虚拟内存管理器
        vm = VirtualMemory(
            physical_memory_size=memory_size * 4096,
            page_size=4096,
            replacement_algorithm=algorithm
        )
        
        # 分配初始页面
        vm.allocate_pages(1, 1)
        
        # 执行访问模式
        start_time = time.time()
        for page_num in access_pattern:
            vm.access_memory(1, page_num * 4096)
        end_time = time.time()
        
        # 收集统计信息
        stats = vm.get_memory_stats()
        stats['execution_time'] = end_time - start_time
        
        return stats
    
    def compare_algorithms(self, access_pattern: List[int], 
                          memory_size: int = 4) -> Dict[str, Dict[str, float]]:
        """
        比较所有算法的性能
        
        参数:
            access_pattern (List[int]): 访问模式
            memory_size (int): 物理内存大小(页面数)
            
        返回:
            Dict[str, Dict[str, float]]: 所有算法的性能指标
        """
        algorithms = [
            PageReplacementAlgorithm.FIFO,
            PageReplacementAlgorithm.LRU,
            PageReplacementAlgorithm.CLOCK
        ]
        
        results = {}
        for algorithm in algorithms:
            results[algorithm.value] = self.analyze_algorithm(
                algorithm, access_pattern, memory_size
            )
        
        return results
    
    def print_comparison(self, results: Dict[str, Dict[str, float]]):
        """打印比较结果"""
        print("\n算法性能比较结果:")
        print("-" * 80)
        print(f"{'算法':<10} {'缺页次数':<10} {'命中次数':<10} {'缺页率':<10} {'执行时间(ms)':<12}")
        print("-" * 80)
        
        for alg_name, result in results.items():
            fault_rate_str = f"{result['fault_rate']:.2%}"
            execution_time_str = f"{result['execution_time']*1000:.2f}ms"
            print(f"{alg_name.upper():<10} {result['page_faults']:<10} {result['page_hits']:<10} "
                  f"{fault_rate_str:<10} {execution_time_str:<12}")
        print("-" * 80)


# 示例使用
def demo_algorithms():
    """演示不同算法的行为"""
    print("=== 页面置换算法演示 ===\n")
    
    # 创建一个典型的访问模式
    access_pattern = [0, 1, 2, 3, 0, 1, 4, 5, 0, 1, 2, 3, 4, 5]
    
    # 分析器
    analyzer = AlgorithmAnalyzer()
    
    # 比较算法性能
    results = analyzer.compare_algorithms(access_pattern, memory_size=4)
    
    # 打印结果
    analyzer.print_comparison(results)
    
    # 详细分析每个算法
    for alg_name, result in results.items():
        print(f"\n{alg_name.upper()} 算法详细分析:")
        print(f"  缺页次数: {result['page_faults']}")
        print(f"  命中次数: {result['page_hits']}")
        print(f"  缺页率: {result['fault_rate']:.2%}")
        print(f"  命中率: {result['hit_rate']:.2%}")
        print(f"  执行时间: {result['execution_time']*1000:.2f}ms")

if __name__ == "__main__":
    demo_algorithms() 