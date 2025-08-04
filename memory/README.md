# 虚拟内存管理模块

## 概述

本模块实现了一个完整的虚拟内存管理系统，用于教学演示虚拟内存的核心概念和页面置换算法。该实现采用了良好的软件设计模式，包括策略模式、工厂模式等，使代码更加清晰和可扩展。

## 模块结构

```
memory/
├── __init__.py              # 包初始化文件
├── virtual_memory.py        # 虚拟内存管理器核心实现
├── page_replacement.py      # 页面置换算法实现
├── test_virtual_memory.py   # 测试文件
└── README.md               # 说明文档
```

## 设计模式

### 策略模式 (Strategy Pattern)
页面置换算法使用策略模式实现，允许在运行时切换不同的算法：

```python
# 不同的算法策略
vm = VirtualMemory(replacement_algorithm=PageReplacementAlgorithm.LRU)
vm.set_replacement_algorithm(PageReplacementAlgorithm.FIFO)
```

### 工厂模式 (Factory Pattern)
使用工厂类创建具体的页面置换算法实例：

```python
# 通过工厂创建算法
algorithm = PageReplacementFactory.create_algorithm(
    PageReplacementAlgorithm.LRU, 
    virtual_memory
)
```

## 核心概念

### 虚拟内存
虚拟内存是一种内存管理技术，它允许程序使用比实际物理内存更大的地址空间。通过页面置换算法，系统可以在物理内存和磁盘之间交换页面。

### 页面和帧
- **页面(Page)**: 虚拟地址空间中的固定大小块，通常是4KB
- **帧(Frame)**: 物理内存中的固定大小块，与页面大小相同
- **页面表**: 记录虚拟页面到物理帧的映射关系

### 页面置换算法
当物理内存不足时，需要选择一些页面置换到磁盘，为新页面腾出空间。

## 功能特性

### 1. 页面管理
- 页面分配和释放
- 页面状态跟踪（空闲、已分配、已换出）
- 页面元数据管理（访问时间、修改位、引用位等）

### 2. 页面置换算法
实现了三种经典的页面置换算法：

#### FIFO (First In First Out)
- **原理**: 选择最早进入内存的页面进行置换
- **优点**: 实现简单，开销小
- **缺点**: 不考虑页面使用频率，性能可能较差
- **适用场景**: 对性能要求不高的简单系统

#### LRU (Least Recently Used)
- **原理**: 选择最久未被访问的页面进行置换
- **优点**: 考虑了页面使用频率，性能较好
- **缺点**: 需要记录每个页面的访问时间，开销较大
- **适用场景**: 对性能要求较高的系统

#### Clock (时钟算法)
- **原理**: 使用循环队列和引用位，选择引用位为0的页面进行置换
- **优点**: 实现相对简单，性能介于FIFO和LRU之间
- **缺点**: 仍然可能置换掉有用的页面
- **适用场景**: 平衡性能和复杂度的系统

### 3. 内存访问
- 虚拟地址到物理地址的转换
- 缺页中断处理
- 读写操作支持

### 4. 统计信息
- 缺页次数和命中次数
- 缺页率和命中率
- 内存使用情况

### 5. 算法分析工具
- 性能比较功能
- 访问模式分析
- 算法评估报告

## 使用方法

### 基本使用

```python
from memory import VirtualMemory, PageReplacementAlgorithm

# 创建虚拟内存管理器
vm = VirtualMemory(
    physical_memory_size=1024*1024,  # 1MB物理内存
    page_size=4096,                  # 4KB页面
    replacement_algorithm=PageReplacementAlgorithm.LRU  # 使用LRU算法
)

# 为进程分配页面
vm.allocate_pages(process_id=1, num_pages=3)

# 访问内存
vm.access_memory(process_id=1, virtual_address=0)
vm.access_memory(process_id=1, virtual_address=4096, is_write=True)

# 查看统计信息
stats = vm.get_memory_stats()
print(f"缺页率: {stats['fault_rate']:.2%}")

# 打印内存映射
vm.print_memory_map()

# 释放进程页面
vm.free_pages(process_id=1)
```

### 算法比较

```python
from memory import AlgorithmAnalyzer, PageReplacementAlgorithm

# 创建分析器
analyzer = AlgorithmAnalyzer()

# 定义访问模式
access_pattern = [0, 1, 2, 3, 0, 1, 4, 5, 0, 1, 2, 3, 4, 5]

# 比较算法性能
results = analyzer.compare_algorithms(access_pattern, memory_size=4)

# 打印比较结果
analyzer.print_comparison(results)
```

### 算法切换

```python
# 运行时切换算法
vm.set_replacement_algorithm(PageReplacementAlgorithm.FIFO)
vm.set_replacement_algorithm(PageReplacementAlgorithm.CLOCK)
```

## 教学要点

### 1. 虚拟内存的基本概念
- 理解虚拟地址和物理地址的区别
- 掌握页面和帧的概念
- 了解页面表的作用

### 2. 页面置换算法
- **FIFO算法**: 理解先进先出的置换策略
- **LRU算法**: 掌握基于时间戳的置换策略
- **Clock算法**: 理解基于引用位的置换策略

### 3. 设计模式
- **策略模式**: 理解算法族的设计和封装
- **工厂模式**: 掌握对象创建的封装
- **开闭原则**: 学习对扩展开放、对修改封闭的设计

### 4. 性能分析
- 缺页率对系统性能的影响
- 不同算法的适用场景
- 内存访问模式对算法性能的影响

### 5. 实际应用
- 现代操作系统的内存管理
- 数据库系统的缓存管理
- Web服务器的页面缓存

## 运行示例

### 运行演示
```bash
cd memory
python virtual_memory.py
```

### 运行算法演示
```bash
python page_replacement.py
```

### 运行测试
```bash
python test_virtual_memory.py
```

## 代码结构详解

### 主要类

#### VirtualMemory
虚拟内存管理器的主类，负责：
- 页面分配和释放
- 内存访问处理
- 统计信息收集

#### Page
内存页面类，包含：
- 页面元数据（编号、大小、状态等）
- 访问信息（时间戳、引用位、修改位等）

#### PageReplacementStrategy
页面置换策略基类，定义了算法接口：
- `select_victim()`: 选择要置换的页面
- `update_reference()`: 更新页面引用信息

#### 具体算法类
- `FIFOStrategy`: FIFO算法实现
- `LRUStrategy`: LRU算法实现
- `ClockStrategy`: Clock算法实现

#### PageReplacementFactory
算法工厂类，负责创建具体的算法实例。

#### AlgorithmAnalyzer
算法分析工具，用于比较不同算法的性能。

## 扩展建议

### 1. 添加新的页面置换算法
```python
class OPTStrategy(PageReplacementStrategy):
    """最优置换算法"""
    def select_victim(self):
        # 实现最优置换逻辑
        pass
```

### 2. 增加更多功能
- 支持页面大小可变
- 实现页面预取
- 添加内存压缩功能
- 支持多级页面表

### 3. 性能优化
- 使用更高效的数据结构
- 实现并行处理
- 添加缓存机制

### 4. 可视化功能
- 内存映射可视化
- 算法执行过程动画
- 性能图表展示

## 注意事项

1. **线程安全**: 当前实现使用锁保证线程安全，但在高并发场景下可能需要优化
2. **内存限制**: 这是一个教学演示实现，实际使用中需要考虑内存限制
3. **错误处理**: 代码包含了基本的错误处理，但在生产环境中需要更完善的错误处理机制
4. **性能考虑**: 当前实现优先考虑教学清晰性，实际应用中需要优化性能

## 参考资料

- 《操作系统概念》- Abraham Silberschatz
- 《现代操作系统》- Andrew S. Tanenbaum
- 《计算机系统：程序员的视角》- Randal E. Bryant
- 《设计模式：可复用面向对象软件的基础》- Gang of Four

## 许可证

本代码仅用于教学目的，请勿用于商业用途。 