"""
进程高级概念 - 僵尸进程、孤儿进程、守护进程

本模块实现：
1. 僵尸进程 (Zombie Process)
2. 孤儿进程 (Orphan Process)
3. 守护进程 (Daemon Process)
4. 进程组与会话
"""

import threading
import time
from typing import Optional, List, Dict, Callable
from enum import Enum
from utils.logger import Logger


class ProcessType(Enum):
    """进程类型"""
    NORMAL = "normal"
    ZOMBIE = "zombie"
    ORPHAN = "orphan"
    DAEMON = "daemon"


class AdvancedProcess:
    """
    高级进程类

    支持僵尸、孤儿、守护进程状态。
    """

    _next_pid = 1

    def __init__(self, name: str, parent_pid: Optional[int] = None,
                 is_daemon: bool = False):
        """
        初始化进程

        Args:
            name: 进程名称
            parent_pid: 父进程PID
            is_daemon: 是否是守护进程
        """
        self.pid = AdvancedProcess._next_pid
        AdvancedProcess._next_pid += 1
        self.name = name
        self.parent_pid = parent_pid
        self.child_pids: List[int] = []
        self.is_daemon = is_daemon

        # 状态
        self._state = "running"
        self._exit_code: Optional[int] = None
        self._process_type = ProcessType.DAEMON if is_daemon else ProcessType.NORMAL

        # 线程
        self._thread: Optional[threading.Thread] = None
        self._target: Optional[Callable] = None
        self._args = ()

        # 进程组和会话
        self._pgid = self.pid  # 进程组ID
        self._sid: Optional[int] = None  # 会话ID

        # 统计
        self._start_time = time.time()
        self._end_time: Optional[float] = None

        self._logger = Logger()

    @property
    def state(self) -> str:
        return self._state

    @property
    def exit_code(self) -> Optional[int]:
        return self._exit_code

    @property
    def process_type(self) -> ProcessType:
        return self._process_type

    def set_target(self, target: Callable, args: tuple = ()) -> None:
        """设置执行目标"""
        self._target = target
        self._args = args

    def start(self) -> None:
        """启动进程"""
        if self._target:
            self._thread = threading.Thread(
                target=self._run_wrapper,
                daemon=self.is_daemon
            )
            self._thread.start()

    def _run_wrapper(self) -> None:
        """执行包装器"""
        try:
            if self._target:
                self._target(*self._args)
            self._exit_code = 0
        except Exception as e:
            self._logger.error(f"进程 {self.name} 异常: {e}")
            self._exit_code = 1
        finally:
            self._end_time = time.time()
            self._state = "terminated"

    def join(self, timeout: float = None) -> bool:
        """等待进程结束"""
        if self._thread:
            self._thread.join(timeout)
            return not self._thread.is_alive()
        return True

    def terminate(self) -> None:
        """终止进程"""
        self._state = "terminated"
        self._exit_code = -1

    def become_zombie(self) -> None:
        """变成僵尸进程"""
        self._state = "zombie"
        self._process_type = ProcessType.ZOMBIE
        self._logger.debug(f"进程 {self.name} (PID: {self.pid}) 变成僵尸进程")

    def become_orphan(self) -> None:
        """变成孤儿进程"""
        self._process_type = ProcessType.ORPHAN
        self.parent_pid = 1  # 被init进程收养
        self._logger.debug(f"进程 {self.name} (PID: {self.pid}) 变成孤儿进程，被init收养")

    def get_info(self) -> dict:
        """获取进程信息"""
        return {
            'pid': self.pid,
            'name': self.name,
            'parent_pid': self.parent_pid,
            'state': self._state,
            'type': self._process_type.value,
            'exit_code': self._exit_code,
            'is_daemon': self.is_daemon,
            'pgid': self._pgid,
            'sid': self._sid,
            'children': self.child_pids.copy(),
            'runtime': (self._end_time or time.time()) - self._start_time
        }


class ProcessGroup:
    """
    进程组

    一组相关进程的集合，用于作业控制。
    """

    def __init__(self, pgid: int, leader_pid: int):
        """
        初始化进程组

        Args:
            pgid: 进程组ID
            leader_pid: 组长进程PID
        """
        self.pgid = pgid
        self.leader_pid = leader_pid
        self.members: List[int] = [leader_pid]
        self._logger = Logger()

    def add_member(self, pid: int) -> None:
        """添加成员"""
        if pid not in self.members:
            self.members.append(pid)

    def remove_member(self, pid: int) -> None:
        """移除成员"""
        if pid in self.members:
            self.members.remove(pid)

    def is_empty(self) -> bool:
        """检查是否为空"""
        return len(self.members) == 0


class Session:
    """
    会话

    一个或多个进程组的集合。
    """

    def __init__(self, sid: int, leader_pid: int):
        """
        初始化会话

        Args:
            sid: 会话ID
            leader_pid: 会话首进程PID
        """
        self.sid = sid
        self.leader_pid = leader_pid
        self.process_groups: Dict[int, ProcessGroup] = {}
        self._controlling_terminal: Optional[str] = None
        self._logger = Logger()

    def add_process_group(self, pg: ProcessGroup) -> None:
        """添加进程组"""
        self.process_groups[pg.pgid] = pg

    def remove_process_group(self, pgid: int) -> None:
        """移除进程组"""
        if pgid in self.process_groups:
            del self.process_groups[pgid]

    def set_controlling_terminal(self, terminal: str) -> None:
        """设置控制终端"""
        self._controlling_terminal = terminal


class AdvancedProcessManager:
    """
    高级进程管理器

    管理进程的创建、终止、回收等。
    """

    def __init__(self):
        """初始化进程管理器"""
        self._processes: Dict[int, AdvancedProcess] = {}
        self._process_groups: Dict[int, ProcessGroup] = {}
        self._sessions: Dict[int, Session] = {}
        self._lock = threading.Lock()
        self._logger = Logger()

        # init进程
        self._init_process = self._create_init_process()

        # 守护进程列表
        self._daemon_processes: List[int] = []

        # 僵尸进程列表
        self._zombie_processes: List[int] = []

    def _create_init_process(self) -> AdvancedProcess:
        """创建init进程"""
        init = AdvancedProcess("init", parent_pid=None)
        init._sid = init.pid
        init._pgid = init.pid
        self._processes[init.pid] = init

        # 创建会话
        session = Session(init.pid, init.pid)
        self._sessions[init.pid] = session

        self._logger.info(f"init进程创建，PID: {init.pid}")
        return init

    def create_process(self, name: str, parent_pid: int = None,
                      is_daemon: bool = False) -> AdvancedProcess:
        """
        创建新进程

        Args:
            name: 进程名称
            parent_pid: 父进程PID
            is_daemon: 是否是守护进程

        Returns:
            AdvancedProcess: 创建的进程
        """
        with self._lock:
            if parent_pid is None:
                parent_pid = self._init_process.pid

            process = AdvancedProcess(name, parent_pid, is_daemon)

            # 设置进程组
            parent = self._processes.get(parent_pid)
            if parent:
                process._pgid = parent._pgid
                parent.child_pids.append(process.pid)

            self._processes[process.pid] = process

            if is_daemon:
                self._daemon_processes.append(process.pid)
                # 守护进程脱离父进程
                process.parent_pid = self._init_process.pid

            self._logger.debug(f"创建进程: {name}, PID: {process.pid}")
            return process

    def terminate_process(self, pid: int, exit_code: int = 0) -> None:
        """
        终止进程

        Args:
            pid: 进程ID
            exit_code: 退出码
        """
        with self._lock:
            process = self._processes.get(pid)
            if not process:
                return

            process._exit_code = exit_code
            process._state = "terminated"
            process._end_time = time.time()

            # 变成僵尸进程，等待父进程回收
            process.become_zombie()
            self._zombie_processes.append(pid)

            # 处理子进程（变成孤儿）
            for child_pid in process.child_pids:
                child = self._processes.get(child_pid)
                if child:
                    child.become_orphan()
                    self._init_process.child_pids.append(child_pid)

            self._logger.debug(f"进程 {process.name} (PID: {pid}) 终止，退出码: {exit_code}")

    def wait_process(self, pid: int) -> Optional[int]:
        """
        等待进程结束并回收

        Args:
            pid: 进程ID

        Returns:
            Optional[int]: 退出码
        """
        with self._lock:
            process = self._processes.get(pid)
            if not process:
                return None

            # 等待进程结束
            if process._state not in ("terminated", "zombie"):
                return None

            exit_code = process._exit_code

            # 回收僵尸进程
            if pid in self._zombie_processes:
                self._zombie_processes.remove(pid)

            # 从父进程的子进程列表中移除
            parent = self._processes.get(process.parent_pid)
            if parent and pid in parent.child_pids:
                parent.child_pids.remove(pid)

            # 从进程表中移除
            del self._processes[pid]

            self._logger.debug(f"回收进程 PID: {pid}, 退出码: {exit_code}")
            return exit_code

    def create_daemon(self, name: str, target: Callable,
                     args: tuple = ()) -> AdvancedProcess:
        """
        创建守护进程

        Args:
            name: 进程名称
            target: 执行函数
            args: 参数

        Returns:
            AdvancedProcess: 守护进程
        """
        daemon = self.create_process(name, is_daemon=True)
        daemon.set_target(target, args)

        # 守护进程创建新会话
        daemon._sid = daemon.pid
        daemon._pgid = daemon.pid

        session = Session(daemon.pid, daemon.pid)
        pg = ProcessGroup(daemon.pid, daemon.pid)
        pg.add_member(daemon.pid)
        session.add_process_group(pg)

        self._sessions[daemon.pid] = session
        self._process_groups[daemon.pid] = pg

        daemon.start()
        self._logger.info(f"守护进程 '{name}' 启动，PID: {daemon.pid}")
        return daemon

    def get_zombie_processes(self) -> List[AdvancedProcess]:
        """获取所有僵尸进程"""
        return [self._processes[pid] for pid in self._zombie_processes
                if pid in self._processes]

    def get_orphan_processes(self) -> List[AdvancedProcess]:
        """获取所有孤儿进程"""
        return [p for p in self._processes.values()
                if p.process_type == ProcessType.ORPHAN]

    def get_daemon_processes(self) -> List[AdvancedProcess]:
        """获取所有守护进程"""
        return [self._processes[pid] for pid in self._daemon_processes
                if pid in self._processes]

    def reap_zombies(self) -> int:
        """回收所有僵尸进程"""
        count = 0
        for pid in list(self._zombie_processes):
            if self.wait_process(pid) is not None:
                count += 1
        return count

    def print_process_status(self) -> None:
        """打印进程状态"""
        print("\n进程状态:")
        print("-" * 80)
        print(f"{'PID':<6} {'名称':<15} {'类型':<10} {'状态':<10} {'父PID':<6} {'子进程':<15}")
        print("-" * 80)

        for process in self._processes.values():
            info = process.get_info()
            children = str(info['children']) if info['children'] else "[]"
            print(f"{info['pid']:<6} {info['name']:<15} {info['type']:<10} "
                  f"{info['state']:<10} {info['parent_pid']:<6} {children:<15}")

        print("-" * 80)
        print(f"僵尸进程数: {len(self._zombie_processes)}")
        print(f"守护进程数: {len(self._daemon_processes)}")


# 使用示例
if __name__ == "__main__":
    print("=== 进程高级概念演示 ===\n")

    pm = AdvancedProcessManager()

    # 1. 创建普通进程
    print("1. 创建普通进程")
    p1 = pm.create_process("worker-1")
    p2 = pm.create_process("worker-2", parent_pid=p1.pid)
    pm.print_process_status()

    # 2. 演示僵尸进程
    print("\n2. 演示僵尸进程")
    pm.terminate_process(p2.pid, exit_code=0)
    print(f"  僵尸进程: {[p.name for p in pm.get_zombie_processes()]}")

    # 回收僵尸进程
    pm.wait_process(p2.pid)
    print(f"  回收后僵尸进程: {[p.name for p in pm.get_zombie_processes()]}")

    # 3. 演示孤儿进程
    print("\n3. 演示孤儿进程")
    p3 = pm.create_process("child-1", parent_pid=p1.pid)
    pm.terminate_process(p1.pid)  # 父进程终止
    print(f"  孤儿进程: {[p.name for p in pm.get_orphan_processes()]}")
    print(f"  孤儿进程的新父进程: init (PID 1)")

    # 4. 演示守护进程
    print("\n4. 演示守护进程")

    def daemon_task():
        for i in range(3):
            print(f"  [守护进程] 运行中... {i}")
            time.sleep(0.3)

    daemon = pm.create_daemon("my-daemon", daemon_task)
    time.sleep(1)

    pm.print_process_status()

    print(f"\n守护进程: {[p.name for p in pm.get_daemon_processes()]}")

    print("\n演示完成！")
