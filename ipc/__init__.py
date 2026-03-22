"""
IPC模块 - 进程间通信

本模块实现：
1. 管道 (匿名管道和命名管道)
2. 共享内存
3. 消息队列 (扩展现有实现)
"""

from typing import Optional, Any, Dict, List
from collections import deque
import threading
import time
from utils.logger import Logger


# ==========================================
# 管道实现
# ==========================================

class Pipe:
    """
    匿名管道

    单向通信通道，用于父子进程间通信。
    """

    def __init__(self, buffer_size: int = 65536):
        """
        初始化管道

        Args:
            buffer_size: 缓冲区大小
        """
        self._buffer_size = buffer_size
        self._buffer: deque = deque()
        self._lock = threading.Lock()
        self._read_condition = threading.Condition(self._lock)
        self._write_condition = threading.Condition(self._lock)
        self._closed = False
        self._logger = Logger()

        # 统计
        self._bytes_written = 0
        self._bytes_read = 0

    def write(self, data: bytes) -> int:
        """
        写入数据

        Args:
            data: 要写入的数据

        Returns:
            int: 写入的字节数
        """
        if self._closed:
            raise BrokenPipeError("管道已关闭")

        with self._write_condition:
            # 等待缓冲区有空间
            while len(self._buffer) >= self._buffer_size and not self._closed:
                self._write_condition.wait()

            if self._closed:
                raise BrokenPipeError("管道已关闭")

            # 写入数据
            for byte in data:
                self._buffer.append(byte)

            self._bytes_written += len(data)
            self._read_condition.notify()

        return len(data)

    def read(self, size: int = -1, timeout: float = None) -> bytes:
        """
        读取数据

        Args:
            size: 读取大小，-1表示读取所有可用数据
            timeout: 超时时间

        Returns:
            bytes: 读取的数据
        """
        with self._read_condition:
            # 等待数据可用
            start = time.time()
            while not self._buffer and not self._closed:
                if timeout is not None:
                    elapsed = time.time() - start
                    if elapsed >= timeout:
                        return b''
                    self._read_condition.wait(timeout - elapsed)
                else:
                    self._read_condition.wait()

            if not self._buffer:
                return b''

            # 读取数据
            if size == -1:
                size = len(self._buffer)

            data = []
            for _ in range(min(size, len(self._buffer))):
                data.append(self._buffer.popleft())

            result = bytes(data)
            self._bytes_read += len(result)
            self._write_condition.notify()

        return result

    def close(self) -> None:
        """关闭管道"""
        with self._lock:
            self._closed = True
            self._read_condition.notify_all()
            self._write_condition.notify_all()

    @property
    def is_closed(self) -> bool:
        return self._closed

    def get_stats(self) -> dict:
        return {
            'buffer_size': self._buffer_size,
            'current_size': len(self._buffer),
            'bytes_written': self._bytes_written,
            'bytes_read': self._bytes_read,
            'closed': self._closed
        }


class NamedPipe:
    """
    命名管道 (FIFO)

    可以被不相关的进程访问的管道。
    """

    _pipes: Dict[str, 'NamedPipe'] = {}

    def __init__(self, name: str, buffer_size: int = 65536):
        """
        初始化命名管道

        Args:
            name: 管道名称
            buffer_size: 缓冲区大小
        """
        self._name = name
        self._pipe = Pipe(buffer_size)
        self._readers = 0
        self._writers = 0
        self._lock = threading.Lock()
        self._logger = Logger()

    @classmethod
    def create(cls, name: str, buffer_size: int = 65536) -> 'NamedPipe':
        """创建命名管道"""
        if name in cls._pipes:
            raise FileExistsError(f"命名管道 '{name}' 已存在")

        pipe = NamedPipe(name, buffer_size)
        cls._pipes[name] = pipe
        return pipe

    @classmethod
    def open(cls, name: str) -> 'NamedPipe':
        """打开命名管道"""
        if name not in cls._pipes:
            raise FileNotFoundError(f"命名管道 '{name}' 不存在")
        return cls._pipes[name]

    @classmethod
    def unlink(cls, name: str) -> None:
        """删除命名管道"""
        if name in cls._pipes:
            cls._pipes[name]._pipe.close()
            del cls._pipes[name]

    def write(self, data: bytes) -> int:
        """写入数据"""
        with self._lock:
            self._writers += 1
        try:
            return self._pipe.write(data)
        finally:
            with self._lock:
                self._writers -= 1

    def read(self, size: int = -1, timeout: float = None) -> bytes:
        """读取数据"""
        with self._lock:
            self._readers += 1
        try:
            return self._pipe.read(size, timeout)
        finally:
            with self._lock:
                self._readers -= 1

    @property
    def name(self) -> str:
        return self._name

    def get_stats(self) -> dict:
        stats = self._pipe.get_stats()
        stats['name'] = self._name
        stats['readers'] = self._readers
        stats['writers'] = self._writers
        return stats


# ==========================================
# 共享内存实现
# ==========================================

class SharedMemory:
    """
    共享内存

    允许多个进程访问同一块内存区域。
    """

    _segments: Dict[str, 'SharedMemory'] = {}

    def __init__(self, name: str, size: int):
        """
        初始化共享内存

        Args:
            name: 共享内存名称
            size: 大小（字节）
        """
        self._name = name
        self._size = size
        self._memory = bytearray(size)
        self._lock = threading.Lock()
        self._ref_count = 0
        self._logger = Logger()

        # 同步原语
        self._attached_processes: List[int] = []

    @classmethod
    def create(cls, name: str, size: int) -> 'SharedMemory':
        """创建共享内存段"""
        if name in cls._segments:
            raise FileExistsError(f"共享内存 '{name}' 已存在")

        shm = SharedMemory(name, size)
        cls._segments[name] = shm
        return shm

    @classmethod
    def open(cls, name: str) -> 'SharedMemory':
        """打开共享内存段"""
        if name not in cls._segments:
            raise FileNotFoundError(f"共享内存 '{name}' 不存在")
        return cls._segments[name]

    def attach(self, pid: int) -> None:
        """附加进程"""
        with self._lock:
            self._ref_count += 1
            self._attached_processes.append(pid)
            self._logger.debug(f"进程 {pid} 附加共享内存 '{self._name}'")

    def detach(self, pid: int) -> None:
        """分离进程"""
        with self._lock:
            self._ref_count -= 1
            if pid in self._attached_processes:
                self._attached_processes.remove(pid)
            self._logger.debug(f"进程 {pid} 分离共享内存 '{self._name}'")

    def read(self, offset: int = 0, size: int = -1) -> bytes:
        """
        读取共享内存

        Args:
            offset: 偏移量
            size: 读取大小，-1表示读取到末尾

        Returns:
            bytes: 读取的数据
        """
        with self._lock:
            if size == -1:
                size = self._size - offset
            return bytes(self._memory[offset:offset + size])

    def write(self, data: bytes, offset: int = 0) -> int:
        """
        写入共享内存

        Args:
            data: 要写入的数据
            offset: 偏移量

        Returns:
            int: 写入的字节数
        """
        with self._lock:
            size = min(len(data), self._size - offset)
            self._memory[offset:offset + size] = data[:size]
            return size

    def clear(self) -> None:
        """清空共享内存"""
        with self._lock:
            self._memory = bytearray(self._size)

    @classmethod
    def unlink(cls, name: str) -> None:
        """删除共享内存段"""
        if name in cls._segments:
            del cls._segments[name]

    @property
    def name(self) -> str:
        return self._name

    @property
    def size(self) -> int:
        return self._size

    def get_stats(self) -> dict:
        return {
            'name': self._name,
            'size': self._size,
            'ref_count': self._ref_count,
            'attached_processes': self._attached_processes.copy()
        }


# ==========================================
# 扩展消息队列
# ==========================================

class Message:
    """消息"""

    def __init__(self, msg_type: int, data: Any, sender_pid: int):
        self.type = msg_type
        self.data = data
        self.sender_pid = sender_pid
        self.timestamp = time.time()


class MessageQueue:
    """
    消息队列

    进程间异步通信的机制。
    """

    _queues: Dict[int, 'MessageQueue'] = {}
    _next_id = 1

    def __init__(self, key: int, max_size: int = 100):
        """
        初始化消息队列

        Args:
            key: 队列键值
            max_size: 最大消息数
        """
        self._id = MessageQueue._next_id
        MessageQueue._next_id += 1
        self._key = key
        self._max_size = max_size
        self._queue: deque = deque()
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
        self._logger = Logger()

        # 权限
        self._permissions = 0o660

    @classmethod
    def get_or_create(cls, key: int, max_size: int = 100) -> 'MessageQueue':
        """获取或创建消息队列"""
        for mq in cls._queues.values():
            if mq._key == key:
                return mq

        mq = MessageQueue(key, max_size)
        cls._queues[mq._id] = mq
        return mq

    def send(self, msg_type: int, data: Any, sender_pid: int,
             timeout: float = None) -> bool:
        """
        发送消息

        Args:
            msg_type: 消息类型
            data: 消息数据
            sender_pid: 发送者PID
            timeout: 超时时间

        Returns:
            bool: 是否成功
        """
        with self._not_full:
            while len(self._queue) >= self._max_size:
                if timeout is not None:
                    if not self._not_full.wait(timeout):
                        return False
                else:
                    self._not_full.wait()

            msg = Message(msg_type, data, sender_pid)
            self._queue.append(msg)
            self._logger.debug(f"消息队列 {self._id} 收到消息，类型={msg_type}")
            self._not_empty.notify()
            return True

    def receive(self, msg_type: int = 0, timeout: float = None) -> Optional[Message]:
        """
        接收消息

        Args:
            msg_type: 接收的消息类型，0表示接收任意类型
            timeout: 超时时间

        Returns:
            Optional[Message]: 接收的消息
        """
        with self._not_empty:
            start = time.time()
            while True:
                # 查找消息
                if msg_type == 0:
                    # 接收任意类型
                    if self._queue:
                        msg = self._queue.popleft()
                        self._not_full.notify()
                        return msg
                else:
                    # 接收特定类型
                    for i, msg in enumerate(self._queue):
                        if msg.type == msg_type:
                            del list(self._queue)[i]
                            self._not_full.notify()
                            return msg

                if timeout is not None:
                    elapsed = time.time() - start
                    if elapsed >= timeout:
                        return None
                    self._not_empty.wait(timeout - elapsed)
                else:
                    self._not_empty.wait()

    @property
    def id(self) -> int:
        return self._id

    @property
    def key(self) -> int:
        return self._key

    def get_stats(self) -> dict:
        return {
            'id': self._id,
            'key': self._key,
            'max_size': self._max_size,
            'current_size': len(self._queue),
            'permissions': oct(self._permissions)
        }

    @classmethod
    def remove(cls, msqid: int) -> None:
        """删除消息队列"""
        if msqid in cls._queues:
            del cls._queues[msqid]


# 使用示例
if __name__ == "__main__":
    print("=== IPC演示 ===\n")

    # 示例1: 匿名管道
    print("1. 匿名管道")
    pipe = Pipe()

    def pipe_writer():
        for i in range(3):
            msg = f"消息{i}".encode()
            pipe.write(msg)
            print(f"  写入: {msg.decode()}")
            time.sleep(0.1)
        pipe.close()

    def pipe_reader():
        time.sleep(0.2)
        while not pipe.is_closed or pipe._buffer:
            data = pipe.read(timeout=0.5)
            if data:
                print(f"  读取: {data.decode()}")

    import threading
    w = threading.Thread(target=pipe_writer)
    r = threading.Thread(target=pipe_reader)
    w.start()
    r.start()
    w.join()
    r.join()

    print(f"  统计: {pipe.get_stats()}")

    # 示例2: 命名管道
    print("\n2. 命名管道")
    fifo = NamedPipe.create("my_fifo")
    print(f"  创建命名管道: {fifo.name}")
    print(f"  统计: {fifo.get_stats()}")
    NamedPipe.unlink("my_fifo")

    # 示例3: 共享内存
    print("\n3. 共享内存")
    shm = SharedMemory.create("my_shm", 1024)
    shm.attach(1)
    shm.write(b"Hello, Shared Memory!")
    data = shm.read()
    print(f"  写入: 'Hello, Shared Memory!'")
    print(f"  读取: {data.decode()}")
    print(f"  统计: {shm.get_stats()}")
    SharedMemory.unlink("my_shm")

    # 示例4: 消息队列
    print("\n4. 消息队列")
    mq = MessageQueue.get_or_create(key=1234)
    mq.send(msg_type=1, data="消息1", sender_pid=1)
    mq.send(msg_type=2, data="消息2", sender_pid=1)
    msg = mq.receive()
    print(f"  接收消息: 类型={msg.type}, 数据={msg.data}")
    print(f"  统计: {mq.get_stats()}")

    print("\n演示完成！")
