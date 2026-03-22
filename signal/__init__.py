"""
信号机制 - Unix风格的进程间信号

本模块实现：
1. 信号定义和发送
2. 信号处理函数注册
3. 信号掩码和阻塞
4. 常见信号模拟
"""

from typing import Callable, Optional, Dict, List, Set
from enum import Enum, auto
from collections import defaultdict
import threading
import time
from utils.logger import Logger


class Signal(Enum):
    """标准信号定义"""
    # 进程控制
    SIGINT = auto()      # 中断 (Ctrl+C)
    SIGTERM = auto()     # 终止
    SIGKILL = auto()     # 强制终止
    SIGSTOP = auto()     # 停止
    SIGCONT = auto()     # 继续
    SIGABRT = auto()     # 异常终止

    # 错误信号
    SIGSEGV = auto()     # 段错误
    SIGFPE = auto()      # 浮点异常
    SIGBUS = auto()      # 总线错误
    SIGILL = auto()      # 非法指令

    # 用户信号
    SIGUSR1 = auto()     # 用户定义1
    SIGUSR2 = auto()     # 用户定义2

    # I/O信号
    SIGIO = auto()       # I/O就绪
    SIGPIPE = auto()     # 管道破裂

    # 其他
    SIGCHLD = auto()     # 子进程状态改变
    SIGALRM = auto()     # 定时器
    SIGHUP = auto()      # 挂起


class SignalAction:
    """信号动作"""
    IGNORE = "ignore"
    DEFAULT = "default"
    CUSTOM = "custom"


class SignalHandler:
    """
    信号处理器

    管理进程的信号处理。
    """

    def __init__(self, pid: int):
        """
        初始化信号处理器

        Args:
            pid: 进程ID
        """
        self._pid = pid
        self._logger = Logger()

        # 信号处理函数
        self._handlers: Dict[Signal, Callable] = {}

        # 信号掩码（阻塞的信号）
        self._blocked: Set[Signal] = set()

        # 待处理信号
        self._pending: Set[Signal] = set()

        # 默认动作
        self._default_actions: Dict[Signal, str] = {
            Signal.SIGINT: SignalAction.DEFAULT,
            Signal.SIGTERM: SignalAction.DEFAULT,
            Signal.SIGKILL: SignalAction.DEFAULT,
            Signal.SIGSTOP: SignalAction.DEFAULT,
            Signal.SIGCONT: SignalAction.DEFAULT,
            Signal.SIGABRT: SignalAction.DEFAULT,
            Signal.SIGSEGV: SignalAction.DEFAULT,
            Signal.SIGFPE: SignalAction.DEFAULT,
            Signal.SIGBUS: SignalAction.DEFAULT,
            Signal.SIGILL: SignalAction.DEFAULT,
            Signal.SIGUSR1: SignalAction.IGNORE,
            Signal.SIGUSR2: SignalAction.IGNORE,
            Signal.SIGIO: SignalAction.IGNORE,
            Signal.SIGPIPE: SignalAction.DEFAULT,
            Signal.SIGCHLD: SignalAction.IGNORE,
            Signal.SIGALRM: SignalAction.DEFAULT,
            Signal.SIGHUP: SignalAction.DEFAULT,
        }

        # 锁
        self._lock = threading.Lock()

        # 统计
        self._sent_count = defaultdict(int)
        self._handled_count = defaultdict(int)

    def register_handler(self, signal: Signal, handler: Callable) -> Callable:
        """
        注册信号处理函数

        Args:
            signal: 信号类型
            handler: 处理函数

        Returns:
            Callable: 之前的处理函数
        """
        with self._lock:
            old_handler = self._handlers.get(signal)
            self._handlers[signal] = handler
            self._logger.debug(f"进程 {self._pid} 注册信号 {signal.name} 处理函数")
            return old_handler

    def ignore_signal(self, signal: Signal) -> None:
        """忽略信号"""
        with self._lock:
            self._handlers[signal] = SignalAction.IGNORE

    def restore_default(self, signal: Signal) -> None:
        """恢复默认处理"""
        with self._lock:
            if signal in self._handlers:
                del self._handlers[signal]

    def block_signal(self, signal: Signal) -> None:
        """阻塞信号"""
        with self._lock:
            self._blocked.add(signal)
            self._logger.debug(f"进程 {self._pid} 阻塞信号 {signal.name}")

    def unblock_signal(self, signal: Signal) -> None:
        """解除阻塞信号"""
        with self._lock:
            self._blocked.discard(signal)
            # 如果有待处理的信号，触发处理
            if signal in self._pending:
                self._pending.discard(signal)
                self._handle_signal(signal)

    def send_signal(self, signal: Signal) -> bool:
        """
        发送信号给进程

        Args:
            signal: 信号类型

        Returns:
            bool: 是否成功
        """
        with self._lock:
            self._sent_count[signal] += 1

            # SIGKILL 和 SIGSTOP 不能被阻塞
            if signal in (Signal.SIGKILL, Signal.SIGSTOP):
                self._handle_signal(signal)
                return True

            # 检查是否被阻塞
            if signal in self._blocked:
                self._pending.add(signal)
                self._logger.debug(f"进程 {self._pid} 信号 {signal.name} 被阻塞，加入待处理")
                return True

            self._handle_signal(signal)
            return True

    def _handle_signal(self, signal: Signal) -> None:
        """处理信号"""
        self._handled_count[signal] += 1

        # 检查是否有自定义处理函数
        if signal in self._handlers:
            handler = self._handlers[signal]
            if handler == SignalAction.IGNORE:
                self._logger.debug(f"进程 {self._pid} 忽略信号 {signal.name}")
                return
            elif callable(handler):
                self._logger.debug(f"进程 {self._pid} 执行信号 {signal.name} 的自定义处理函数")
                try:
                    handler(signal, self._pid)
                except Exception as e:
                    self._logger.error(f"信号处理函数错误: {e}")
                return

        # 执行默认动作
        self._execute_default(signal)

    def _execute_default(self, signal: Signal) -> None:
        """执行默认动作"""
        action = self._default_actions.get(signal, SignalAction.DEFAULT)

        self._logger.info(f"进程 {self._pid} 执行信号 {signal.name} 的默认动作: {action}")

        if signal in (Signal.SIGKILL, Signal.SIGTERM, Signal.SIGINT,
                      Signal.SIGABRT, Signal.SIGSEGV, Signal.SIGFPE,
                      Signal.SIGBUS, Signal.SIGILL):
            # 终止进程
            print(f"  [进程 {self._pid}] 被信号 {signal.name} 终止")
        elif signal == Signal.SIGSTOP:
            # 停止进程
            print(f"  [进程 {self._pid}] 被信号 {signal.name} 停止")
        elif signal == Signal.SIGCONT:
            # 继续进程
            print(f"  [进程 {self._pid}] 被信号 {signal.name} 继续")

    def get_pending_signals(self) -> List[Signal]:
        """获取待处理信号"""
        with self._lock:
            return list(self._pending)

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            return {
                'pid': self._pid,
                'blocked_signals': [s.name for s in self._blocked],
                'pending_signals': [s.name for s in self._pending],
                'sent_count': {s.name: c for s, c in self._sent_count.items()},
                'handled_count': {s.name: c for s, c in self._handled_count.items()}
            }


class SignalManager:
    """
    信号管理器

    管理所有进程的信号处理。
    """

    def __init__(self):
        """初始化信号管理器"""
        self._handlers: Dict[int, SignalHandler] = {}
        self._lock = threading.Lock()
        self._logger = Logger()

    def register_process(self, pid: int) -> SignalHandler:
        """注册进程"""
        with self._lock:
            if pid not in self._handlers:
                self._handlers[pid] = SignalHandler(pid)
                self._logger.debug(f"注册进程 {pid} 的信号处理器")
            return self._handlers[pid]

    def unregister_process(self, pid: int) -> None:
        """注销进程"""
        with self._lock:
            if pid in self._handlers:
                del self._handlers[pid]

    def send_signal(self, pid: int, signal: Signal) -> bool:
        """
        发送信号给指定进程

        Args:
            pid: 进程ID
            signal: 信号类型

        Returns:
            bool: 是否成功
        """
        with self._lock:
            handler = self._handlers.get(pid)
            if handler:
                return handler.send_signal(signal)
            return False

    def broadcast_signal(self, signal: Signal, exclude_pid: int = None) -> None:
        """广播信号给所有进程"""
        with self._lock:
            for pid, handler in self._handlers.items():
                if pid != exclude_pid:
                    handler.send_signal(signal)

    def get_handler(self, pid: int) -> Optional[SignalHandler]:
        """获取进程的信号处理器"""
        return self._handlers.get(pid)


# 使用示例
if __name__ == "__main__":
    print("=== 信号机制演示 ===\n")

    # 创建信号管理器
    sm = SignalManager()

    # 注册进程
    handler1 = sm.register_process(1)
    handler2 = sm.register_process(2)

    # 注册自定义处理函数
    def sigusr1_handler(signal, pid):
        print(f"  [进程 {pid}] 收到 SIGUSR1，执行自定义处理")

    handler1.register_handler(Signal.SIGUSR1, sigusr1_handler)

    def sigusr2_handler(signal, pid):
        print(f"  [进程 {pid}] 收到 SIGUSR2，执行自定义处理")

    handler2.register_handler(Signal.SIGUSR2, sigusr2_handler)

    # 发送信号
    print("1. 发送用户信号")
    sm.send_signal(1, Signal.SIGUSR1)
    sm.send_signal(2, Signal.SIGUSR2)

    # 测试信号阻塞
    print("\n2. 测试信号阻塞")
    handler1.block_signal(Signal.SIGUSR1)
    sm.send_signal(1, Signal.SIGUSR1)  # 应该被阻塞
    print(f"  待处理信号: {handler1.get_pending_signals()}")
    handler1.unblock_signal(Signal.SIGUSR1)  # 解除阻塞后处理

    # 测试默认动作
    print("\n3. 测试默认动作")
    sm.send_signal(1, Signal.SIGTERM)

    # 打印统计
    print("\n4. 统计信息")
    print(f"  进程1: {handler1.get_stats()}")
    print(f"  进程2: {handler2.get_stats()}")

    print("\n演示完成！")
