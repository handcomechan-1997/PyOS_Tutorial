# PyOS - Python操作系统学习项目

一个用Python实现的简单操作系统模拟器，用于学习和演示操作系统的基本概念。这是一个**教学项目**，旨在通过动手实践来深入理解操作系统原理。

## 📘 教学使用说明

为了帮助初学者快速上手，本项目的模块设计和注释都尽量保持简洁明了。建议按照以下步骤进行学习：

1. **阅读入口程序**：查看 [`main.py`](main.py) 了解系统是如何启动的。
2. **探索内核模块**：重点阅读 [`kernel/system.py`](kernel/system.py) 和 [`kernel/scheduler.py`](kernel/scheduler.py)，理解系统如何管理进程和资源。
3. **动手实践**：运行项目并在 Shell 中尝试内置命令，观察日志输出与代码实现之间的联系。

在学习过程中，尝试逐步完善 TODO 标记的函数，通过“阅读代码 → 修改实现 → 验证效果”的流程来加深对操作系统原理的理解。

## 🎯 项目目标

通过实现这个项目，你将深入理解：

1. **操作系统原理**: 进程、内存、文件系统等核心概念
2. **系统编程**: 系统调用、中断处理、设备驱动
3. **并发编程**: 多线程、进程同步、死锁处理
4. **数据结构**: 队列、栈、树、哈希表在系统中的应用
5. **算法设计**: 调度算法、页面置换算法等

## 🏗️ 当前项目架构

```
PyOS/
├── kernel/                 # 内核模块
│   ├── system.py          # ✅ 系统核心 (已完成)
│   ├── scheduler.py       # ✅ 进程调度器框架 (已完成)
│   ├── memory_manager.py  # 🔄 内存管理器 (基础框架)
│   ├── interrupt.py       # ✅ 中断处理框架 (已完成)
│   └── system_call.py     # ✅ 系统调用框架 (已完成)
├── process/               # 进程管理
│   ├── process.py         # ✅ 进程类 (已完成)
│   ├── pcb.py            # ✅ 进程控制块 (已完成)
│   ├── process_table.py   # ✅ 进程表 (已完成)
│   └── process_manager.py # ✅ 进程管理器 (已完成)
├── memory/                # 内存管理
│   ├── virtual_memory.py  # ✅ 虚拟内存框架 (已完成)
│   ├── page_table.py      # ✅ 页表管理框架 (已完成)
│   └── memory_allocator.py # ✅ 内存分配器框架 (已完成)
├── filesystem/            # 文件系统
│   ├── file_system.py     # ✅ 文件系统核心框架 (已完成)
│   ├── inode.py          # ✅ 索引节点框架 (已完成)
│   ├── directory.py      # ✅ 目录管理框架 (已完成)
│   └── file_operations.py # ✅ 文件操作框架 (已完成)
├── device/                # 设备管理
│   ├── device_manager.py  # ✅ 设备管理器 (已完成)
│   ├── terminal.py        # ✅ 终端设备 (已完成)
│   ├── keyboard.py        # ✅ 键盘设备 (已完成)
│   └── display.py         # ✅ 显示设备 (已完成)
├── shell/                 # 命令行界面
│   ├── shell.py          # ✅ Shell核心框架 (已完成)
│   ├── commands.py       # ✅ 内置命令框架 (已完成)
│   └── parser.py         # ✅ 命令解析器框架 (已完成)
├── utils/                 # 工具模块
│   ├── logger.py         # ✅ 日志系统 (已完成)
│   └── config.py         # 🔄 配置管理 (基础框架)
├── main.py               # ✅ 主程序入口 (已完成)
├── requirements.txt      # ✅ 依赖包 (已完成)
└── README.md            # 📖 项目说明 (当前文件)
```

**图例**: ✅ 已完成框架 | 🔄 部分完成 | ⏳ 待实现

## 🚀 快速开始

### 环境准备

```bash
# 确保Python版本 >= 3.8
python --version

# 安装依赖
pip install -r requirements.txt
```

### 运行系统

```bash
# 运行系统
python main.py
```

**预期输出**:
```
==================================================
    Python简单操作系统 (PyOS)
    版本: 1.0.0
    作者: HandsomeChen
==================================================
2025-07-10 19:49:49 - PyOS - INFO - PyOS系统启动中...
2025-07-10 19:49:49 - PyOS - INFO - 注册系统调用: getpid
2025-07-10 19:49:49 - PyOS - INFO - 注册系统调用: time
2025-07-10 19:49:49 - PyOS - INFO - 注册系统调用: sleep
2025-07-10 19:49:49 - PyOS - INFO - 文件系统初始化
2025-07-10 19:49:49 - device.device_manager - INFO - Device Manager initialized
2025-07-10 19:49:49 - PyOS - INFO - 系统核心初始化完成
2025-07-10 19:49:49 - PyOS - INFO - 系统启动中...
2025-07-10 19:49:49 - PyOS - INFO - 文件系统初始化完成
2025-07-10 19:49:49 - device.device_manager - INFO - Initializing Device Manager...
2025-07-10 19:49:49 - device.device_manager - INFO - Device terminal_0 (System Terminal) registered
2025-07-10 19:49:49 - device.device_manager - INFO - Device keyboard_0 (System Keyboard) registered
2025-07-10 19:49:49 - device.device_manager - INFO - Device display_0 (System Display) registered
2025-07-10 19:49:49 - device.terminal - INFO - Terminal terminal_0 initialized
2025-07-10 19:49:49 - PyOS - INFO - 进程管理器初始化完成
2025-07-10 19:49:49 - PyOS - INFO - 进程调度器启动
2025-07-10 19:49:49 - PyOS - INFO - 所有子系统初始化完成
2025-07-10 19:49:49 - PyOS - INFO - 系统启动完成
系统启动成功！
欢迎使用PyOS Shell!
输入 'help' 查看可用命令，输入 'exit' 退出系统

PyOS:/>
```

## 📚 详细学习路径

### 阶段1: 基础功能完善 (第1天)

#### 1.1 熟悉系统架构
**学习目标**: 理解PyOS的整体架构和各模块的职责。

**任务**:
1. 阅读系统核心代码，理解启动流程
2. 了解各个模块的基本功能
3. 运行系统，体验基本的Shell交互

**验证方法**:
```bash
python main.py
PyOS:/> help
PyOS:/> version
PyOS:/> echo "Hello PyOS!"
PyOS:/> info
```

#### 1.2 实现基础Shell命令
**学习目标**: 理解命令解析和执行流程。

**任务**: 完善以下基础命令：
- `help` - 显示帮助信息
- `version` - 显示系统版本
- `echo` - 输出文本
- `clear` - 清屏
- `info` - 显示系统信息

**实现位置**: `shell/commands.py`

**预期输出**:
```
PyOS Shell 帮助
================
基本命令:
  help            - 显示此帮助
  version         - 显示系统版本
  echo <文本>     - 输出文本
  clear           - 清屏
  info            - 显示系统信息
  exit            - 退出系统

PyOS:/> version
PyOS 版本: 1.0.0

PyOS:/> echo "Hello World"
Hello World
```

### 阶段2: 进程管理实现 (第2-3天)

#### 2.1 理解进程管理框架
**学习目标**: 理解进程创建、调度和管理的核心概念。

**关键文件**:
- `process/process.py` - 进程类定义
- `process/process_manager.py` - 进程管理器
- `kernel/scheduler.py` - 进程调度器

**学习任务**:
1. 阅读进程相关代码，理解进程状态转换
2. 理解进程控制块(PCB)的作用
3. 理解调度器的工作原理

#### 2.2 实现进程创建和基本调度
**任务**: 完善进程创建和基本调度功能。

**实现位置**: `process/process_manager.py`

**关键方法**:
```python
def create_process(self, name: str, target=None, priority=0) -> Process:
    """创建新进程"""
    # TODO: 实现进程创建逻辑
    pass

def start_process(self, pid: int) -> bool:
    """启动进程"""
    # TODO: 实现进程启动逻辑
    pass
```

**验证方法**:
```python
# 在 main.py 中添加测试代码
def test_process_creation():
    system = System()
    system.boot()
    
    # 创建测试进程
    def test_task():
        print("Hello from test process!")
        return "test completed"
    
    process = system.process_manager.create_process("test_process", target=test_task)
    print(f"Created process: {process}")
    
    # 启动进程
    system.process_manager.start_process(process.pid)
    
    # 等待进程执行
    import time
    time.sleep(2)
    
    system.shutdown()
```

**预期输出**:
```
Created process: Process(id=1, name=test_process, state=READY)
Hello from test process!
Process test_process completed with result: test completed
```

#### 2.3 实现进程命令
**任务**: 在Shell中实现进程管理命令。

**实现位置**: `shell/commands.py`

**需要实现的命令**:
- `ps` - 显示进程列表
- `kill <pid>` - 终止进程
- `sleep <seconds>` - 创建睡眠进程

**验证方法**:
```bash
PyOS:/> ps
PID  Name         State    Priority
1    init         RUNNING  0
2    shell        READY    1

PyOS:/> sleep 5 &
[1] 3

PyOS:/> ps
PID  Name         State    Priority
1    init         RUNNING  0
2    shell        READY    1
3    sleep        SLEEPING 0

PyOS:/> kill 3
Process 3 terminated
```

### 阶段3: 内存管理实现 (第4-5天)

#### 3.1 理解内存管理框架
**学习目标**: 理解虚拟内存、分页和内存分配的概念。

**关键文件**:
- `memory/virtual_memory.py` - 虚拟内存管理
- `memory/page_table.py` - 页表管理
- `memory/memory_allocator.py` - 内存分配器

#### 3.2 实现基本内存分配
**任务**: 实现简单的内存分配和释放功能。

**实现位置**: `memory/memory_allocator.py`

**关键方法**:
```python
def allocate_memory(self, size: int, pid: int) -> Optional[int]:
    """分配内存"""
    # TODO: 实现内存分配逻辑
    pass

def free_memory(self, address: int, pid: int) -> bool:
    """释放内存"""
    # TODO: 实现内存释放逻辑
    pass
```

**验证方法**:
```python
def test_memory_allocation():
    allocator = MemoryAllocator(1024 * 1024)  # 1MB内存
    
    # 分配内存
    addr1 = allocator.allocate_memory(1024, 1)
    addr2 = allocator.allocate_memory(2048, 1)
    
    print(f"Allocated addresses: {addr1}, {addr2}")
    
    # 释放内存
    allocator.free_memory(addr1, 1)
    
    # 查看内存使用情况
    print(f"Memory usage: {allocator.get_memory_usage()}")
```

**预期输出**:
```
Allocated addresses: 0, 1024
Memory usage: 3072/1048576 bytes (0.3%)
```

#### 3.3 实现内存管理命令
**任务**: 在Shell中实现内存管理命令。

**需要实现的命令**:
- `meminfo` - 显示内存使用情况
- `malloc <size>` - 分配内存
- `free <address>` - 释放内存

**验证方法**:
```bash
PyOS:/> meminfo
Memory Usage: 1024/1048576 bytes (0.1%)
Free Memory: 1047552 bytes
Fragmentation: 0%

PyOS:/> malloc 1024
Allocated 1024 bytes at address 0x1000

PyOS:/> meminfo
Memory Usage: 2048/1048576 bytes (0.2%)
Free Memory: 1046528 bytes
Fragmentation: 0%
```

### 阶段4: 文件系统实现 (第6-7天)

#### 4.1 理解文件系统框架
**学习目标**: 理解文件系统的基本概念，包括目录结构、文件操作等。

**关键文件**:
- `filesystem/file_system.py` - 文件系统核心
- `filesystem/directory.py` - 目录管理
- `filesystem/file_operations.py` - 文件操作

#### 4.2 实现基本文件操作
**任务**: 实现文件的创建、读取、写入和删除功能。

**实现位置**: `filesystem/file_operations.py`

**关键方法**:
```python
def create_file(self, path: str, content: str = "") -> bool:
    """创建文件"""
    # TODO: 实现文件创建逻辑
    pass

def read_file(self, path: str) -> Optional[str]:
    """读取文件"""
    # TODO: 实现文件读取逻辑
    pass

def write_file(self, path: str, content: str) -> bool:
    """写入文件"""
    # TODO: 实现文件写入逻辑
    pass
```

**验证方法**:
```python
def test_file_operations():
    fs = FileSystem()
    
    # 创建文件
    fs.create_file("/test.txt", "Hello, PyOS!")
    
    # 读取文件
    content = fs.read_file("/test.txt")
    print(f"File content: {content}")
    
    # 写入文件
    fs.write_file("/test.txt", "Updated content")
    
    # 列出目录
    files = fs.list_directory("/")
    print(f"Files in root: {files}")
```

**预期输出**:
```
File content: Hello, PyOS!
Files in root: ['test.txt']
```

#### 4.3 实现文件系统命令
**任务**: 在Shell中实现文件系统命令。

**需要实现的命令**:
- `ls` - 列出文件和目录
- `cat <file>` - 显示文件内容
- `mkdir <dir>` - 创建目录
- `rm <file>` - 删除文件
- `cd <dir>` - 切换目录

**验证方法**:
```bash
PyOS:/> ls
total 0
drwxr-xr-x  .    4096 2025-06-21 00:00
drwxr-xr-x  ..   4096 2025-06-21 00:00

PyOS:/> mkdir testdir
PyOS:/> cd testdir
PyOS:/testdir> echo "Hello World" > hello.txt
PyOS:/testdir> ls
total 1
-rw-r--r--  hello.txt   12 2025-06-21 00:01

PyOS:/testdir> cat hello.txt
Hello World

PyOS:/testdir> cd ..
PyOS:/> rm testdir/hello.txt
PyOS:/> rmdir testdir
```

### 阶段5: 高级功能实现 (第8-10天)

#### 5.1 实现进程间通信
**学习目标**: 理解进程间通信的基本概念。

**任务**: 实现简单的进程间通信机制。

**实现位置**: 新建 `process/ipc.py`

**关键功能**:
- 管道通信
- 共享内存
- 信号机制

#### 5.2 实现高级调度算法
**学习目标**: 理解不同调度算法的特点。

**任务**: 实现优先级调度和多级反馈队列调度。

**实现位置**: `kernel/scheduler.py`

**需要实现的算法**:
- 优先级调度
- 多级反馈队列调度
- 最短作业优先调度

#### 5.3 实现系统监控
**学习目标**: 理解系统监控和性能分析。

**任务**: 实现系统状态监控功能。

**需要实现的命令**:
- `top` - 显示系统状态
- `uptime` - 显示系统运行时间
- `ps aux` - 显示详细进程信息

## 🔧 开发指南

### 代码规范
1. **命名规范**: 使用Python命名规范，类名用PascalCase，函数名用snake_case
2. **文档字符串**: 为所有类和方法添加docstring
3. **类型提示**: 使用类型提示提高代码可读性
4. **异常处理**: 适当处理异常，记录错误日志

### 调试技巧
1. **日志输出**: 使用Logger记录关键信息
2. **状态打印**: 定期打印系统状态
3. **断点调试**: 使用pdb进行调试

### 测试方法
1. **单元测试**: 为每个模块编写单元测试
2. **集成测试**: 测试模块间的交互
3. **功能测试**: 测试完整的功能流程

## 📝 学习检查清单

### 阶段1检查清单
- [ ] 熟悉系统架构和各模块功能
- [ ] 完善基础Shell命令 (help, version, echo, clear, info)
- [ ] 验证系统能正常启动Shell界面

### 阶段2检查清单
- [ ] 理解进程管理框架
- [ ] 实现进程创建和启动功能
- [ ] 实现进程管理命令 (ps, kill, sleep)
- [ ] 验证进程调度正常工作

### 阶段3检查清单
- [ ] 理解内存管理框架
- [ ] 实现基本内存分配和释放
- [ ] 实现内存管理命令 (meminfo, malloc, free)
- [ ] 验证内存管理正常工作

### 阶段4检查清单
- [ ] 理解文件系统框架
- [ ] 实现基本文件操作 (创建、读取、写入、删除)
- [ ] 实现文件系统命令 (ls, cat, mkdir, rm, cd)
- [ ] 验证文件系统正常工作

### 阶段5检查清单
- [ ] 实现进程间通信
- [ ] 实现高级调度算法
- [ ] 实现系统监控功能
- [ ] 完成项目演示

## 🎯 预期学习成果

完成这个项目后，你将能够：

1. **理解操作系统核心概念**: 进程、内存、文件系统、设备管理
2. **掌握系统编程技能**: 多线程编程、内存管理、文件操作
3. **学会模块化设计**: 如何设计可扩展的系统架构
4. **提高调试能力**: 通过日志和状态监控调试复杂系统
5. **增强算法理解**: 调度算法、内存分配算法等

## 🤝 获取帮助

如果在学习过程中遇到问题：

1. **查看日志**: 系统会输出详细的日志信息
2. **阅读代码**: 每个模块都有详细的注释
3. **分步调试**: 按照学习路径逐步实现功能
4. **参考文档**: 查看相关操作系统的文档

## 📄 许可证

MIT License

---

*这是一个教育项目，旨在帮助理解操作系统的基本概念和实现原理。通过动手实践，你将获得对操作系统内部工作原理的深入理解。* 