"""
经典同步问题 - 操作系统课程核心案例

==========================================
      经典同步问题深入学习教程
==========================================

本模块实现了操作系统中最经典的四个同步问题：
1. 生产者-消费者问题
2. 读者-写者问题
3. 哲学家就餐问题
4. 睡眠理发师问题

这些问题是理解进程同步、互斥、死锁等概念的最佳实践。
"""

import threading
import time
import random
from typing import Optional, List
from collections import deque

from .semaphore import Semaphore, BinarySemaphore, CountingSemaphore
from .mutex import Mutex
from .condition import ConditionVariable
from utils.logger import Logger


# ==========================================
# 1. 生产者-消费者问题
# ==========================================

class ProducerConsumer:
    """
    生产者-消费者问题

    ==========================================
    问题描述：
    - 生产者生产数据放入缓冲区
    - 消费者从缓冲区取出数据消费
    - 缓冲区大小有限
    - 必须同步生产者和消费者的访问

    同步要求：
    1. 缓冲区满时，生产者必须等待
    2. 缓冲区空时，消费者必须等待
    3. 对缓冲区的访问必须互斥

    解决方案：
    - mutex: 互斥访问缓冲区
    - empty: 计数空闲槽位
    - full: 计数已用槽位
    ==========================================
    """

    def __init__(self, buffer_size: int = 10):
        """
        初始化生产者-消费者

        Args:
            buffer_size: 缓冲区大小
        """
        self._buffer_size = buffer_size
        self._buffer: deque = deque()

        # 同步原语
        self._mutex = Mutex(name="pc_mutex")
        self._empty = CountingSemaphore(max_count=buffer_size, name="empty_slots")
        self._full = CountingSemaphore(max_count=0, name="full_slots")
        # 注意：full初始为0，表示没有物品

        self._logger = Logger()
        self._logger.info(f"生产者-消费者创建，缓冲区大小: {buffer_size}")

        # 统计
        self._produce_count = 0
        self._consume_count = 0

    def produce(self, item, timeout: Optional[float] = None) -> bool:
        """
        生产者：放入物品

        Args:
            item: 要生产的物品
            timeout: 超时时间

        Returns:
            bool: 是否成功
        """
        # 1. 等待空闲槽位
        if not self._empty.acquire(timeout):
            self._logger.warning("生产者等待空闲槽位超时")
            return False

        # 2. 互斥访问缓冲区
        with self._mutex:
            self._buffer.append(item)
            self._produce_count += 1
            self._logger.debug(f"生产物品: {item}, 缓冲区大小: {len(self._buffer)}")

        # 3. 增加已用槽位计数
        self._full.release()

        return True

    def consume(self, timeout: Optional[float] = None):
        """
        消费者：取出物品

        Args:
            timeout: 超时时间

        Returns:
            物品，超时返回None
        """
        # 1. 等待有物品
        if not self._full.acquire(timeout):
            self._logger.warning("消费者等待物品超时")
            return None

        # 2. 互斥访问缓冲区
        with self._mutex:
            item = self._buffer.popleft()
            self._consume_count += 1
            self._logger.debug(f"消费物品: {item}, 缓冲区大小: {len(self._buffer)}")

        # 3. 增加空闲槽位计数
        self._empty.release()

        return item

    @property
    def buffer_size(self) -> int:
        return self._buffer_size

    @property
    def current_size(self) -> int:
        return len(self._buffer)

    def get_stats(self) -> dict:
        return {
            'buffer_size': self._buffer_size,
            'current_items': len(self._buffer),
            'produce_count': self._produce_count,
            'consume_count': self._consume_count
        }


# ==========================================
# 2. 读者-写者问题
# ==========================================

class ReadersWriters:
    """
    读者-写者问题

    ==========================================
    问题描述：
    - 多个读者可以同时读取数据
    - 写者必须独占访问
    - 读写不能同时进行

    第一类读者-写者问题（读者优先）：
    - 只要有读者在读，新读者可以直接进入
    - 可能导致写者饥饿

    第二类读者-写者问题（写者优先）：
    - 有写者等待时，新读者必须等待
    - 可能导致读者饥饿
    ==========================================
    """

    class Policy:
        READER_PREFERENCE = "reader_preference"
        WRITER_PREFERENCE = "writer_preference"

    def __init__(self, policy: str = Policy.READER_PREFERENCE):
        """
        初始化读者-写者

        Args:
            policy: 策略（读者优先或写者优先）
        """
        self._policy = policy
        self._logger = Logger()

        # 共享数据
        self._data = 0
        self._readers = 0  # 当前读者数量

        # 同步原语
        self._mutex = Mutex(name="rw_mutex")      # 保护 readers 计数
        self._write_lock = Mutex(name="write_lock")  # 写者锁
        self._read_lock = Mutex(name="read_lock")    # 用于写者优先

        # 统计
        self._read_count = 0
        self._write_count = 0

        self._logger.info(f"读者-写者创建，策略: {policy}")

    def read(self) -> int:
        """
        读者：读取数据

        Returns:
            int: 读取的数据
        """
        if self._policy == self.Policy.WRITER_PREFERENCE:
            # 写者优先：先获取 read_lock
            self._read_lock.acquire()

        # 增加读者计数
        self._mutex.acquire()
        if self._readers == 0:
            # 第一个读者获取写锁
            self._write_lock.acquire()
        self._readers += 1
        self._mutex.release()

        if self._policy == self.Policy.WRITER_PREFERENCE:
            self._read_lock.release()

        # 读取数据
        data = self._data
        self._read_count += 1
        self._logger.debug(f"读者读取数据: {data}, 当前读者数: {self._readers}")

        # 减少读者计数
        self._mutex.acquire()
        self._readers -= 1
        if self._readers == 0:
            # 最后一个读者释放写锁
            self._write_lock.release()
        self._mutex.release()

        return data

    def write(self, value: int) -> None:
        """
        写者：写入数据

        Args:
            value: 要写入的值
        """
        if self._policy == self.Policy.WRITER_PREFERENCE:
            # 写者优先：先获取 read_lock 阻止新读者
            self._read_lock.acquire()

        # 获取写锁
        self._write_lock.acquire()

        # 写入数据
        self._data = value
        self._write_count += 1
        self._logger.debug(f"写者写入数据: {value}")

        # 释放写锁
        self._write_lock.release()

        if self._policy == self.Policy.WRITER_PREFERENCE:
            self._read_lock.release()

    def get_stats(self) -> dict:
        return {
            'policy': self._policy,
            'current_data': self._data,
            'read_count': self._read_count,
            'write_count': self._write_count
        }


# ==========================================
# 3. 哲学家就餐问题
# ==========================================

class DiningPhilosophers:
    """
    哲学家就餐问题

    ==========================================
    问题描述：
    - 5个哲学家围坐在圆桌旁
    - 每两个哲学家之间有一根筷子
    - 哲学家要么思考，要么吃饭
    - 吃饭需要同时拿起左右两根筷子
    - 放下筷子后继续思考

    死锁风险：
    - 如果所有哲学家同时拿起左边的筷子
    - 然后都等待右边的筷子
    - 形成循环等待 -> 死锁

    解决方案：
    1. 资源层次方案：按顺序获取筷子
    2. 限制就餐人数：最多4人同时就餐
    3. 奇偶方案：奇数先左后右，偶数先右后左
    ==========================================
    """

    class Solution:
        HIERARCHY = "hierarchy"      # 资源层次
        LIMIT = "limit"              # 限制人数
        ODD_EVEN = "odd_even"        # 奇偶方案

    def __init__(self, num_philosophers: int = 5,
                 solution: str = Solution.HIERARCHY):
        """
        初始化哲学家就餐问题

        Args:
            num_philosophers: 哲学家数量
            solution: 解决方案
        """
        self._n = num_philosophers
        self._solution = solution
        self._logger = Logger()

        # 筷子（每根筷子一个互斥锁）
        self._chopsticks = [Mutex(name=f"chopstick_{i}")
                           for i in range(num_philosophers)]

        # 限制就餐人数方案
        self._limit_sem = CountingSemaphore(
            max_count=num_philosophers - 1,
            name="dining_limit"
        )

        # 状态
        self._states = ["thinking"] * num_philosophers
        self._meal_counts = [0] * num_philosophers

        self._logger.info(f"哲学家就餐问题创建，人数: {num_philosophers}，方案: {solution}")

    def dine(self, philosopher_id: int, think_time: float = 0.1,
             eat_time: float = 0.1) -> None:
        """
        哲学家就餐循环

        Args:
            philosopher_id: 哲学家ID
            think_time: 思考时间
            eat_time: 吃饭时间
        """
        while True:
            self._think(philosopher_id, think_time)
            self._pickup_chopsticks(philosopher_id)
            self._eat(philosopher_id, eat_time)
            self._putdown_chopsticks(philosopher_id)

    def _think(self, pid: int, duration: float) -> None:
        """思考"""
        self._states[pid] = "thinking"
        self._logger.debug(f"哲学家 {pid} 正在思考...")
        time.sleep(duration)

    def _eat(self, pid: int, duration: float) -> None:
        """吃饭"""
        self._states[pid] = "eating"
        self._meal_counts[pid] += 1
        self._logger.debug(f"哲学家 {pid} 正在吃饭...")
        time.sleep(duration)

    def _pickup_chopsticks(self, pid: int) -> None:
        """拿起筷子"""
        left = pid
        right = (pid + 1) % self._n

        if self._solution == self.Solution.LIMIT:
            # 限制人数方案
            self._limit_sem.acquire()

        if self._solution == self.Solution.HIERARCHY:
            # 资源层次方案：先拿编号小的筷子
            first = min(left, right)
            second = max(left, right)
            self._chopsticks[first].acquire()
            self._chopsticks[second].acquire()

        elif self._solution == self.Solution.ODD_EVEN:
            # 奇偶方案
            if pid % 2 == 0:
                # 偶数：先右后左
                self._chopsticks[right].acquire()
                self._chopsticks[left].acquire()
            else:
                # 奇数：先左后右
                self._chopsticks[left].acquire()
                self._chopsticks[right].acquire()
        else:
            # 默认：先左后右（可能死锁）
            self._chopsticks[left].acquire()
            self._chopsticks[right].acquire()

        self._states[pid] = "hungry"
        self._logger.debug(f"哲学家 {pid} 拿起筷子")

    def _putdown_chopsticks(self, pid: int) -> None:
        """放下筷子"""
        left = pid
        right = (pid + 1) % self._n

        self._chopsticks[left].release()
        self._chopsticks[right].release()

        if self._solution == self.Solution.LIMIT:
            self._limit_sem.release()

        self._logger.debug(f"哲学家 {pid} 放下筷子")

    def get_states(self) -> List[str]:
        """获取所有哲学家状态"""
        return self._states.copy()

    def get_meal_counts(self) -> List[int]:
        """获取就餐次数"""
        return self._meal_counts.copy()


# ==========================================
# 4. 睡眠理发师问题
# ==========================================

class SleepingBarber:
    """
    睡眠理发师问题

    ==========================================
    问题描述：
    - 理发店有一个理发师、一把理发椅、N个等待椅
    - 没有顾客时，理发师在理发椅上睡觉
    - 顾客到来时：
      - 如果理发师在睡觉，唤醒他并理发
      - 如果理发师在理发，有空椅就等待，否则离开
    - 理发师一次只能服务一个顾客

    同步要求：
    1. 理发师等待顾客
    2. 顾客等待理发师
    3. 互斥访问等待椅计数
    ==========================================
    """

    def __init__(self, waiting_chairs: int = 5):
        """
        初始化睡眠理发师

        Args:
            waiting_chairs: 等待椅数量
        """
        self._waiting_chairs = waiting_chairs
        self._logger = Logger()

        # 同步原语
        self._mutex = Mutex(name="barber_mutex")
        self._customers = Semaphore(0, name="customers")  # 等待的顾客
        self._barber = Semaphore(0, name="barber")        # 理发师就绪

        # 状态
        self._waiting = 0  # 等待的顾客数
        self._served = 0   # 已服务顾客数
        self._lost = 0     # 离开的顾客数

        self._logger.info(f"睡眠理发师创建，等待椅: {waiting_chairs}")

    def barber_work(self, haircut_time: float = 0.5) -> None:
        """
        理发师工作循环

        Args:
            haircut_time: 理发时间
        """
        while True:
            # 等待顾客
            self._logger.debug("理发师等待顾客...")
            self._customers.acquire()

            # 获取顾客
            with self._mutex:
                self._waiting -= 1
                self._logger.debug(f"理发师叫号，等待顾客: {self._waiting}")

            # 通知顾客理发师就绪
            self._barber.release()

            # 理发
            self._logger.info("理发师正在理发...")
            time.sleep(haircut_time)
            self._served += 1
            self._logger.info("理发完成！")

    def customer_arrive(self, customer_id: int) -> bool:
        """
        顾客到达

        Args:
            customer_id: 顾客ID

        Returns:
            bool: 是否成功进入等待
        """
        with self._mutex:
            if self._waiting < self._waiting_chairs:
                # 有空椅，坐下等待
                self._waiting += 1
                self._logger.info(f"顾客 {customer_id} 到达，坐下等待")

                # 唤醒理发师
                self._customers.release()
            else:
                # 没有空椅，离开
                self._lost += 1
                self._logger.info(f"顾客 {customer_id} 到达，无空椅，离开")
                return False

        # 等待理发师
        self._barber.acquire()
        self._logger.info(f"顾客 {customer_id} 开始理发")
        return True

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._mutex:
            return {
                'waiting_chairs': self._waiting_chairs,
                'current_waiting': self._waiting,
                'served': self._served,
                'lost': self._lost
            }


# ==========================================
# 使用示例
# ==========================================

if __name__ == "__main__":
    print("=" * 60)
    print("经典同步问题演示")
    print("=" * 60)

    # 演示生产者-消费者
    print("\n【生产者-消费者问题】")
    pc = ProducerConsumer(buffer_size=3)

    def producer(pid):
        for i in range(3):
            item = f"P{pid}-item{i}"
            pc.produce(item)
            print(f"  生产者{pid}: 生产 {item}")
            time.sleep(random.uniform(0.1, 0.3))

    def consumer(cid):
        for _ in range(3):
            item = pc.consume(timeout=2)
            if item:
                print(f"  消费者{cid}: 消费 {item}")
            time.sleep(random.uniform(0.1, 0.3))

    threads = []
    threads.extend([threading.Thread(target=producer, args=(i,)) for i in range(2)])
    threads.extend([threading.Thread(target=consumer, args=(i,)) for i in range(2)])

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"  统计: {pc.get_stats()}")

    # 演示读者-写者
    print("\n【读者-写者问题】")
    rw = ReadersWriters(policy=ReadersWriters.Policy.READER_PREFERENCE)

    def reader(rid):
        for _ in range(2):
            data = rw.read()
            print(f"  读者{rid}: 读取 {data}")
            time.sleep(0.1)

    def writer(wid):
        for i in range(2):
            value = wid * 100 + i
            rw.write(value)
            print(f"  写者{wid}: 写入 {value}")
            time.sleep(0.2)

    threads = []
    threads.extend([threading.Thread(target=reader, args=(i,)) for i in range(3)])
    threads.extend([threading.Thread(target=writer, args=(i,)) for i in range(1)])

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"  统计: {rw.get_stats()}")

    # 演示哲学家就餐
    print("\n【哲学家就餐问题】")
    dp = DiningPhilosophers(num_philosophers=5, solution=DiningPhilosophers.Solution.HIERARCHY)

    def philosopher_dine(pid, rounds):
        for _ in range(rounds):
            dp._think(pid, 0.1)
            dp._pickup_chopsticks(pid)
            dp._eat(pid, 0.1)
            dp._putdown_chopsticks(pid)

    threads = [threading.Thread(target=philosopher_dine, args=(i, 2)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"  就餐次数: {dp.get_meal_counts()}")

    # 演示睡眠理发师
    print("\n【睡眠理发师问题】")
    sb = SleepingBarber(waiting_chairs=3)

    def barber_thread():
        for _ in range(5):
            sb.barber_work(0.3)

    def customer_thread(cid):
        time.sleep(random.uniform(0, 0.5))
        sb.customer_arrive(cid)

    barber_t = threading.Thread(target=barber_thread)
    customer_threads = [threading.Thread(target=customer_thread, args=(i,)) for i in range(6)]

    barber_t.start()
    for t in customer_threads:
        t.start()

    for t in customer_threads:
        t.join()
    time.sleep(0.5)

    print(f"  统计: {sb.get_stats()}")
