"""
内核架构模拟 - 微内核与模块化设计

本模块实现：
1. 微内核架构
2. 内核模块系统
3. 进程间通信机制
"""

from typing import Dict, List, Optional, Callable, Any
from abc import ABC, abstractmethod
import threading
import time
from enum import Enum
from utils.logger import Logger


class KernelType(Enum):
    """内核类型"""
    MONOLITHIC = "monolithic"  # 单内核
    MICROKERNEL = "microkernel"  # 微内核
    HYBRID = "hybrid"  # 混合内核


class ServiceType(Enum):
    """服务类型"""
    FILE_SYSTEM = "file_system"
    MEMORY = "memory"
    PROCESS = "process"
    DEVICE = "device"
    NETWORK = "network"
    SECURITY = "security"


class Message:
    """内核消息"""

    def __init__(self, sender: str, receiver: str, msg_type: str,
                 data: Any = None):
        self.sender = sender
        self.receiver = receiver
        self.msg_type = msg_type
        self.data = data
        self.timestamp = time.time()
        self.response: Optional[Any] = None


class KernelService(ABC):
    """内核服务基类"""

    def __init__(self, name: str, service_type: ServiceType):
        self.name = name
        self.service_type = service_type
        self._running = False
        self._logger = Logger()

    @abstractmethod
    def start(self) -> None:
        """启动服务"""
        pass

    @abstractmethod
    def stop(self) -> None:
        """停止服务"""
        pass

    @abstractmethod
    def handle_message(self, message: Message) -> Optional[Any]:
        """处理消息"""
        pass

    @property
    def is_running(self) -> bool:
        return self._running


class KernelModule:
    """内核模块"""

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.loaded = False
        self.dependencies: List[str] = []
        self._init_func: Optional[Callable] = None
        self._exit_func: Optional[Callable] = None
        self._logger = Logger()

    def set_init(self, func: Callable) -> None:
        """设置初始化函数"""
        self._init_func = func

    def set_exit(self, func: Callable) -> None:
        """设置退出函数"""
        self._exit_func = func

    def load(self) -> bool:
        """加载模块"""
        if self.loaded:
            return True

        try:
            if self._init_func:
                self._init_func()
            self.loaded = True
            self._logger.info(f"模块 '{self.name}' v{self.version} 已加载")
            return True
        except Exception as e:
            self._logger.error(f"模块 '{self.name}' 加载失败: {e}")
            return False

    def unload(self) -> bool:
        """卸载模块"""
        if not self.loaded:
            return True

        try:
            if self._exit_func:
                self._exit_func()
            self.loaded = False
            self._logger.info(f"模块 '{self.name}' 已卸载")
            return True
        except Exception as e:
            self._logger.error(f"模块 '{self.name}' 卸载失败: {e}")
            return False


class Microkernel:
    """
    微内核

    只提供最基本的服务：
    - 进程间通信
    - 调度
    - 低级内存管理
    - 中断处理

    其他服务作为用户态进程运行。
    """

    def __init__(self):
        """初始化微内核"""
        self._kernel_type = KernelType.MICROKERNEL
        self._services: Dict[str, KernelService] = {}
        self._modules: Dict[str, KernelModule] = {}
        self._message_queue: List[Message] = []
        self._lock = threading.Lock()
        self._running = False
        self._logger = Logger()

        # 统计
        self._messages_processed = 0

    def register_service(self, service: KernelService) -> bool:
        """注册服务"""
        with self._lock:
            if service.name in self._services:
                return False
            self._services[service.name] = service
            self._logger.info(f"注册服务: {service.name} ({service.service_type.value})")
            return True

    def unregister_service(self, name: str) -> bool:
        """注销服务"""
        with self._lock:
            if name not in self._services:
                return False
            service = self._services[name]
            if service.is_running:
                service.stop()
            del self._services[name]
            return True

    def load_module(self, module: KernelModule) -> bool:
        """加载模块"""
        # 检查依赖
        for dep in module.dependencies:
            if dep not in self._modules or not self._modules[dep].loaded:
                self._logger.error(f"模块 '{module.name}' 缺少依赖: {dep}")
                return False

        with self._lock:
            if module.load():
                self._modules[module.name] = module
                return True
        return False

    def unload_module(self, name: str) -> bool:
        """卸载模块"""
        with self._lock:
            if name not in self._modules:
                return False

            # 检查是否有其他模块依赖它
            for module in self._modules.values():
                if name in module.dependencies and module.loaded:
                    self._logger.error(f"无法卸载 '{name}'，被 '{module.name}' 依赖")
                    return False

            module = self._modules[name]
            if module.unload():
                del self._modules[name]
                return True
        return False

    def send_message(self, message: Message) -> Optional[Any]:
        """
        发送消息

        微内核的核心功能：进程间通信

        Args:
            message: 消息对象

        Returns:
            Optional[Any]: 响应
        """
        with self._lock:
            # 查找目标服务
            service = self._services.get(message.receiver)
            if not service:
                self._logger.error(f"目标服务不存在: {message.receiver}")
                return None

            # 处理消息
            response = service.handle_message(message)
            self._messages_processed += 1

            return response

    def start(self) -> None:
        """启动微内核"""
        self._running = True

        # 启动所有服务
        for service in self._services.values():
            service.start()

        self._logger.info("微内核启动")

    def stop(self) -> None:
        """停止微内核"""
        self._running = False

        # 停止所有服务
        for service in self._services.values():
            service.stop()

        # 卸载所有模块
        for module in list(self._modules.values()):
            module.unload()

        self._logger.info("微内核停止")

    def get_info(self) -> dict:
        """获取内核信息"""
        return {
            'kernel_type': self._kernel_type.value,
            'running': self._running,
            'services': list(self._services.keys()),
            'loaded_modules': [m.name for m in self._modules.values() if m.loaded],
            'messages_processed': self._messages_processed
        }


class FileSystemService(KernelService):
    """文件系统服务示例"""

    def __init__(self):
        super().__init__("filesystem", ServiceType.FILE_SYSTEM)
        self._files: Dict[str, str] = {}

    def start(self) -> None:
        self._running = True
        self._logger.info("文件系统服务启动")

    def stop(self) -> None:
        self._running = False
        self._logger.info("文件系统服务停止")

    def handle_message(self, message: Message) -> Optional[Any]:
        if message.msg_type == "read":
            return self._files.get(message.data)
        elif message.msg_type == "write":
            path, content = message.data
            self._files[path] = content
            return True
        elif message.msg_type == "list":
            return list(self._files.keys())
        return None


class MemoryService(KernelService):
    """内存服务示例"""

    def __init__(self, total_memory: int = 1024 * 1024):
        super().__init__("memory", ServiceType.MEMORY)
        self._total_memory = total_memory
        self._allocated: Dict[int, int] = {}  # pid -> size
        self._used = 0

    def start(self) -> None:
        self._running = True
        self._logger.info("内存服务启动")

    def stop(self) -> None:
        self._running = False
        self._logger.info("内存服务停止")

    def handle_message(self, message: Message) -> Optional[Any]:
        if message.msg_type == "allocate":
            pid, size = message.data
            if self._used + size <= self._total_memory:
                self._allocated[pid] = self._allocated.get(pid, 0) + size
                self._used += size
                return True
            return False
        elif message.msg_type == "free":
            pid = message.data
            if pid in self._allocated:
                self._used -= self._allocated[pid]
                del self._allocated[pid]
                return True
            return False
        elif message.msg_type == "stats":
            return {
                'total': self._total_memory,
                'used': self._used,
                'free': self._total_memory - self._used
            }
        return None


# 使用示例
if __name__ == "__main__":
    print("=== 微内核架构演示 ===\n")

    # 创建微内核
    kernel = Microkernel()

    # 注册服务
    fs_service = FileSystemService()
    mem_service = MemoryService()

    kernel.register_service(fs_service)
    kernel.register_service(mem_service)

    # 创建模块
    network_module = KernelModule("network", "1.0.0")
    network_module.set_init(lambda: print("  网络模块初始化..."))
    network_module.set_exit(lambda: print("  网络模块清理..."))

    kernel.load_module(network_module)

    # 启动内核
    print("1. 启动微内核")
    kernel.start()

    # 通过消息通信
    print("\n2. 通过消息进行进程间通信")

    # 文件系统操作
    msg1 = Message("process1", "filesystem", "write", ("/test.txt", "Hello, Microkernel!"))
    kernel.send_message(msg1)
    print(f"  写入文件: /test.txt")

    msg2 = Message("process1", "filesystem", "read", "/test.txt")
    content = kernel.send_message(msg2)
    print(f"  读取文件: {content}")

    # 内存操作
    msg3 = Message("process1", "memory", "allocate", (1, 1024))
    result = kernel.send_message(msg3)
    print(f"  分配内存: {result}")

    msg4 = Message("process1", "memory", "stats", None)
    stats = kernel.send_message(msg4)
    print(f"  内存统计: {stats}")

    # 打印内核信息
    print(f"\n3. 内核信息")
    print(f"  {kernel.get_info()}")

    # 停止内核
    print("\n4. 停止微内核")
    kernel.stop()

    print("\n演示完成！")
