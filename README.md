# Python简单操作系统 (PyOS) - 学习教程

一个用Python实现的简单操作系统模拟器，用于学习和演示操作系统的基本概念。这是一个**教学项目**，旨在通过动手实践来深入理解操作系统原理。

## 🎯 项目目标

通过实现这个项目，你将深入理解：

1. **操作系统原理**: 进程、内存、文件系统等核心概念
2. **系统编程**: 系统调用、中断处理、设备驱动
3. **并发编程**: 多线程、进程同步、死锁处理
4. **数据结构**: 队列、栈、树、哈希表在系统中的应用
5. **算法设计**: 调度算法、页面置换算法等

## 📚 学习路径

### 阶段1: 基础框架理解 (1-2天)
- [x] 项目结构搭建
- [x] 基础类定义
- [ ] **任务**: 理解现有代码结构
- [ ] **任务**: 运行基础框架，观察日志输出

### 阶段2: 进程管理实现 (3-5天)
- [ ] **核心任务**: 实现进程调度算法
- [ ] **扩展任务**: 实现进程间通信
- [ ] **验证**: 创建多个进程并观察调度过程

### 阶段3: 内存管理实现 (3-5天)
- [ ] **核心任务**: 实现虚拟内存系统
- [ ] **扩展任务**: 实现页面置换算法
- [ ] **验证**: 模拟内存分配和回收

### 阶段4: 文件系统实现 (3-5天)
- [ ] **核心任务**: 实现基本文件操作
- [ ] **扩展任务**: 实现目录结构
- [ ] **验证**: 创建、读写、删除文件

### 阶段5: Shell和命令系统 (2-3天)
- [ ] **核心任务**: 实现基本Shell命令
- [ ] **扩展任务**: 实现管道和重定向
- [ ] **验证**: 在终端中运行命令

## 🏗️ 项目架构

```
PyOS/
├── kernel/                 # 内核模块
│   ├── __init__.py
│   ├── system.py          # ✅ 系统核心 (已完成)
│   ├── scheduler.py       # ✅ 进程调度器框架 (已完成)
│   ├── memory_manager.py  # 🔄 内存管理器 (需要实现)
│   ├── interrupt.py       # ⏳ 中断处理 (待实现)
│   └── system_call.py     # ⏳ 系统调用 (待实现)
├── process/               # 进程管理
│   ├── __init__.py
│   ├── process.py         # ✅ 进程类 (已完成)
│   ├── pcb.py            # ✅ 进程控制块 (已完成)
│   ├── process_table.py   # ✅ 进程表 (已完成)
│   └── process_manager.py # ✅ 进程管理器 (已完成)
├── memory/                # 内存管理
│   ├── __init__.py
│   ├── virtual_memory.py  # ⏳ 虚拟内存 (待实现)
│   ├── page_table.py      # ⏳ 页表管理 (待实现)
│   └── memory_allocator.py # ⏳ 内存分配器 (待实现)
├── filesystem/            # 文件系统
│   ├── __init__.py
│   ├── file_system.py     # ⏳ 文件系统核心 (待实现)
│   ├── inode.py          # ⏳ 索引节点 (待实现)
│   ├── directory.py      # ⏳ 目录管理 (待实现)
│   └── file_operations.py # ⏳ 文件操作 (待实现)
├── device/                # 设备管理
│   ├── __init__.py
│   ├── device_manager.py  # ⏳ 设备管理器 (待实现)
│   ├── terminal.py        # ⏳ 终端设备 (待实现)
│   ├── keyboard.py        # ⏳ 键盘设备 (待实现)
│   └── display.py         # ⏳ 显示设备 (待实现)
├── shell/                 # 命令行界面
│   ├── __init__.py
│   ├── shell.py          # ⏳ Shell核心 (待实现)
│   ├── commands.py       # ⏳ 内置命令 (待实现)
│   └── parser.py         # ⏳ 命令解析器 (待实现)
├── utils/                 # 工具模块
│   ├── __init__.py
│   ├── logger.py         # ✅ 日志系统 (已完成)
│   └── config.py         # ⏳ 配置管理 (待实现)
├── main.py               # ✅ 主程序入口 (已完成)
├── requirements.txt      # ✅ 依赖包 (已完成)
└── README.md            # 📖 项目说明 (当前文件)
```

**图例**: ✅ 已完成 | 🔄 部分完成 | ⏳ 待实现

## 🚀 快速开始

### 环境准备

```bash
# 确保Python版本 >= 3.8
python --version

# 克隆项目
git clone <repository-url>
cd PyOS

# 安装依赖
pip install -r requirements.txt
```

### 运行基础框架

```bash
# 运行系统
python main.py
```

你应该看到类似输出：
```
==================================================
    Python简单操作系统 (PyOS)
    版本: 1.0.0
    作者: 学习项目
==================================================
系统启动成功！
```

## 📖 详细教程

### 第一课: 理解现有框架

#### 1.1 系统启动流程
1. `main.py` 创建 `System` 对象
2. `System.boot()` 初始化各个子系统
3. 启动系统监控线程
4. 准备启动Shell (目前未实现)

#### 1.2 关键类说明
- **System**: 系统核心，协调各个子系统
- **Process**: 表示一个进程，包含状态、资源等信息
- **Scheduler**: 进程调度器，决定哪个进程运行
- **MemoryManager**: 内存管理器，分配和回收内存
- **Logger**: 日志系统，记录系统事件

#### 1.3 练习任务
```python
# 在 main.py 中添加以下代码来测试进程创建
def test_process_creation():
    system = System()
    system.boot()
    
    # 创建测试进程
    def test_task():
        print("Hello from test process!")
        return "test completed"
    
    process = system.process_manager.create_process("test_process", target=test_task)
    print(f"Created process: {process}")
    
    # 等待一段时间让进程执行
    import time
    time.sleep(2)
    
    system.shutdown()

if __name__ == "__main__":
    test_process_creation()
```

### 第二课: 实现进程调度算法

#### 2.1 当前状态
- 基础调度器框架已完成
- 使用简单的轮转调度
- 需要实现更高级的调度算法

#### 2.2 实现任务

**任务1: 实现优先级调度**
```python
# 在 kernel/scheduler.py 中实现
class PriorityScheduler(Scheduler):
    def __init__(self):
        super().__init__()
        self.priority_queues = {}  # 按优先级分组
    
    def add_process(self, process: Process):
        # TODO: 实现优先级队列
        pass
    
    def _scheduler_loop(self):
        # TODO: 实现优先级调度逻辑
        pass
```

**任务2: 实现多级反馈队列**
```python
# 在 kernel/scheduler.py 中实现
class MLFQScheduler(Scheduler):
    def __init__(self):
        super().__init__()
        self.queues = []  # 多个优先级队列
        self.time_slices = []  # 每个队列的时间片
    
    def add_process(self, process: Process):
        # TODO: 新进程加入最高优先级队列
        pass
    
    def _scheduler_loop(self):
        # TODO: 实现多级反馈队列调度
        pass
```

#### 2.3 验证方法
```python
def test_scheduling():
    system = System()
    system.boot()
    
    # 创建不同优先级的进程
    processes = []
    for i in range(5):
        def task(pid):
            return lambda: print(f"Process {pid} executing")
        
        process = system.process_manager.create_process(
            f"process_{i}", 
            priority=i,
            target=task(i)
        )
        processes.append(process)
    
    # 观察调度过程
    time.sleep(10)
    system.shutdown()
```

### 第三课: 实现内存管理

#### 3.1 当前状态
- 基础内存分配已完成
- 需要实现虚拟内存和分页

#### 3.2 实现任务

**任务1: 实现虚拟内存**
```python
# 在 memory/virtual_memory.py 中实现
class VirtualMemory:
    def __init__(self, physical_memory_size: int, page_size: int = 4096):
        self.physical_memory_size = physical_memory_size
        self.page_size = page_size
        self.page_frames = []
        self.page_tables = {}  # 进程页表
    
    def allocate_pages(self, pid: int, num_pages: int) -> bool:
        # TODO: 为进程分配虚拟页面
        pass
    
    def access_memory(self, pid: int, virtual_address: int) -> bool:
        # TODO: 处理内存访问，可能触发缺页中断
        pass
```

**任务2: 实现页面置换算法**
```python
# 在 memory/page_replacement.py 中实现
class PageReplacement:
    def __init__(self, algorithm: str = "LRU"):
        self.algorithm = algorithm
        self.page_frames = []
        self.page_faults = 0
    
    def handle_page_fault(self, page_number: int) -> int:
        # TODO: 实现页面置换
        if self.algorithm == "LRU":
            return self._lru_replacement(page_number)
        elif self.algorithm == "FIFO":
            return self._fifo_replacement(page_number)
        # 添加更多算法...
    
    def _lru_replacement(self, page_number: int) -> int:
        # TODO: 实现LRU算法
        pass
```

#### 3.3 验证方法
```python
def test_memory_management():
    # 创建虚拟内存系统
    vm = VirtualMemory(1024 * 1024)  # 1MB物理内存
    
    # 模拟进程内存访问
    vm.allocate_pages(1, 10)  # 进程1分配10页
    
    # 模拟内存访问序列
    access_sequence = [0, 1, 2, 3, 2, 1, 4, 5, 6, 7, 8, 9, 0, 1]
    for addr in access_sequence:
        vm.access_memory(1, addr * 4096)
    
    print(f"页面置换次数: {vm.page_replacement.page_faults}")
```

### 第四课: 实现文件系统

#### 4.1 实现任务

**任务1: 实现基本文件操作**
```python
# 在 filesystem/file_system.py 中实现
class FileSystem:
    def __init__(self):
        self.root_directory = Directory("/")
        self.current_directory = self.root_directory
        self.open_files = {}
    
    def create_file(self, path: str, content: str = "") -> bool:
        # TODO: 创建文件
        pass
    
    def read_file(self, path: str) -> str:
        # TODO: 读取文件内容
        pass
    
    def write_file(self, path: str, content: str) -> bool:
        # TODO: 写入文件内容
        pass
    
    def delete_file(self, path: str) -> bool:
        # TODO: 删除文件
        pass
```

**任务2: 实现目录结构**
```python
# 在 filesystem/directory.py 中实现
class Directory:
    def __init__(self, name: str, parent=None):
        self.name = name
        self.parent = parent
        self.children = {}  # 子文件和目录
        self.created_time = time.time()
    
    def add_file(self, name: str, content: str = ""):
        # TODO: 添加文件到目录
        pass
    
    def add_directory(self, name: str):
        # TODO: 添加子目录
        pass
    
    def remove_item(self, name: str) -> bool:
        # TODO: 删除文件或目录
        pass
```

#### 4.2 验证方法
```python
def test_file_system():
    fs = FileSystem()
    
    # 创建文件和目录
    fs.create_file("/test.txt", "Hello, PyOS!")
    fs.create_file("/documents/readme.txt", "This is a readme file")
    
    # 读取文件
    content = fs.read_file("/test.txt")
    print(f"File content: {content}")
    
    # 列出目录内容
    fs.list_directory("/")
```

### 第五课: 实现Shell和命令系统

#### 5.1 实现任务

**任务1: 实现基本Shell**
```python
# 在 shell/shell.py 中实现
class Shell:
    def __init__(self, system: System):
        self.system = system
        self.running = False
        self.current_directory = "/"
        self.command_history = []
    
    def run(self):
        # TODO: 实现Shell主循环
        self.running = True
        while self.running:
            try:
                command = input(f"PyOS:{self.current_directory}> ")
                self.execute_command(command)
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def execute_command(self, command: str):
        # TODO: 解析和执行命令
        pass
```

**任务2: 实现基本命令**
```python
# 在 shell/commands.py 中实现
class Commands:
    def __init__(self, shell: Shell):
        self.shell = shell
    
    def ls(self, args: list):
        # TODO: 列出文件和目录
        pass
    
    def cd(self, args: list):
        # TODO: 切换目录
        pass
    
    def mkdir(self, args: list):
        # TODO: 创建目录
        pass
    
    def rm(self, args: list):
        # TODO: 删除文件或目录
        pass
    
    def cat(self, args: list):
        # TODO: 显示文件内容
        pass
    
    def echo(self, args: list):
        # TODO: 输出文本
        pass
    
    def ps(self, args: list):
        # TODO: 显示进程信息
        pass
```

#### 5.2 验证方法
```bash
# 启动系统后，测试以下命令：
PyOS:/> ls
PyOS:/> mkdir test
PyOS:/> cd test
PyOS:/test> echo "Hello World" > hello.txt
PyOS:/test> cat hello.txt
PyOS:/test> ps
PyOS:/test> cd ..
PyOS:/> rm -r test
```

## 🔧 开发指南

### 代码规范
1. **命名规范**: 使用Python命名规范，类名用PascalCase，函数名用snake_case
2. **文档字符串**: 为所有类和方法添加docstring
3. **类型提示**: 使用类型提示提高代码可读性
4. **异常处理**: 适当处理异常，记录错误日志

### 测试方法
1. **单元测试**: 为每个模块编写单元测试
2. **集成测试**: 测试模块间的交互
3. **功能测试**: 测试完整的功能流程

### 调试技巧
1. **日志输出**: 使用Logger记录关键信息
2. **状态打印**: 定期打印系统状态
3. **断点调试**: 使用pdb进行调试

## 📝 作业和挑战

### 基础作业
1. 实现优先级调度算法
2. 实现LRU页面置换算法
3. 实现基本的文件操作
4. 实现ls、cd、mkdir等命令

### 进阶挑战
1. 实现进程间通信（管道、信号）
2. 实现多级反馈队列调度
3. 实现文件系统权限管理
4. 实现Shell的管道和重定向功能
5. 实现简单的设备驱动程序

### 扩展项目
1. 添加图形用户界面
2. 实现网络功能
3. 添加安全机制
4. 实现多用户支持

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

### 提交规范
- 提交信息要清晰描述改动
- 代码要经过测试
- 添加必要的文档

## 📄 许可证

MIT License

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送邮件 KyleChen97@icloud.com

---

*这是一个教育项目，旨在帮助理解操作系统的基本概念和实现原理。通过动手实践，你将获得对操作系统内部工作原理的深入理解。* 