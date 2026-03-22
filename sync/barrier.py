"""
屏障 (Barrier) - 多线程同步点

==========================================
         屏障深入学习教程
==========================================

🎯 什么是屏障？
--------------
屏障是一种同步原语，让多个线程在某个点等待，
直到所有线程都到达后才一起继续执行。

📚 工作原理
-----------
1. 创建屏障时指定参与的线程数 N
2. 每个线程调用 wait() 到达屏障
3. 当 N 个线程都到达后，所有线程被释放
4. 屏障可以重用（周期性屏障）

💡 应用场景
-----------
1. 并行计算的分阶段处理
2. 多线程初始化同步
3. 迭代算法的同步点
4. 多阶段任务协调

🔧 屏障 vs 其他同步原语
----------------------
| 同步原语   | 作用                     |
|------------|--------------------------|
| 屏障       | 所有线程到达后一起释放   |
| 互斥锁     | 互斥访问临界区           |
| 信号量     | 控制资源访问数量         |
| 条件变量   | 等待条件成立             |

⚠️ 注意事项
-----------
1. 确保所有线程都能到达屏障
2. 处理线程中断和超时
3. 避免死锁（部分线程未到达）
"""

import threading
import time
from typing import Optional, Callable
from utils.logger import Logger


class Barrier:
    """
    屏障实现

    让指定数量的线程在屏障处等待，全部到达后一起释放。
    """

    def __init__(self, count: int, name: str = "",
                 action: Optional[Callable] = None):
        """
        初始化屏障

        Args:
            count: 参与的线程数量
            name: 屏障名称
            action: 屏障释放时执行的动作（只执行一次）
        """
        if count <= 0:
            raise ValueError("线程数量必须大于0")

        self._count = count
        self._name = name or f"barrier_{id(self)}"
        self._action = action
        self._logger = Logger()

        # 状态
        self._lock = threading.Lock()
        self._waiting = 0
        self._generation = 0  # 代数，用于重用屏障
        self._broken = False

        # 统计
        self._total_waits = 0
        self._total_releases = 0

        self._logger.info(f"屏障 '{self._name}' 创建，参与线程数: {count}")

    def wait(self, timeout: Optional[float] = None) -> int:
        """
        等待其他线程

        当所有线程都到达屏障后，一起释放

        Args:
            timeout: 超时时间（秒）

        Returns:
            int: 到达顺序（0表示最后一个，其他表示等待位置）

        Raises:
            BrokenBarrierError: 屏障被破坏
        """
        start_time = time.time()

        with self._lock:
            if self._broken:
                raise BrokenBarrierError("屏障已被破坏")

            generation = self._generation
            self._waiting += 1
            self._total_waits += 1

            # 检查是否是最后一个到达的线程
            if self._waiting == self._count:
                # 执行动作
                if self._action:
                    try:
                        self._action()
                    except Exception as e:
                        self._broken = True
                        raise

                # 重置屏障
                self._waiting = 0
                self._generation += 1
                self._total_releases += 1

                self._logger.info(f"屏障 '{self._name}' 释放，代数: {generation}")
                return 0

            # 不是最后一个，需要等待
            index = self._count - self._waiting

        # 在锁外等待
        while True:
            with self._lock:
                if self._broken:
                    raise BrokenBarrierError("屏障已被破坏")

                if self._generation != generation:
                    # 屏障已释放
                    return index

                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        self._broken = True
                        raise BrokenBarrierError("等待超时")

            time.sleep(0.01)

    def reset(self) -> None:
        """重置屏障"""
        with self._lock:
            self._waiting = 0
            self._generation += 1
            self._broken = False
            self._logger.info(f"屏障 '{self._name}' 已重置")

    def abort(self) -> None:
        """中止屏障"""
        with self._lock:
            self._broken = True
            self._logger.warning(f"屏障 '{self._name}' 已中止")

    @property
    def parties(self) -> int:
        """获取参与线程数"""
        return self._count

    @property
    def waiting(self) -> int:
        """获取当前等待的线程数"""
        with self._lock:
            return self._waiting

    @property
    def is_broken(self) -> bool:
        """检查屏障是否被破坏"""
        with self._lock:
            return self._broken

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            return {
                'name': self._name,
                'parties': self._count,
                'waiting': self._waiting,
                'generation': self._generation,
                'broken': self._broken,
                'total_waits': self._total_waits,
                'total_releases': self._total_releases
            }

    def __str__(self) -> str:
        return (f"Barrier(name='{self._name}', "
                f"waiting={self.waiting}/{self._count})")


class BrokenBarrierError(Exception):
    """屏障被破坏异常"""
    pass


class CyclicBarrier(Barrier):
    """
    循环屏障

    与普通屏障相同，但强调可重用性。
    每次所有线程到达后自动重置，可用于多轮同步。
    """

    def __init__(self, count: int, name: str = "",
                 action: Optional[Callable] = None):
        super().__init__(count, name, action)
        self._round = 0

    def wait(self, timeout: Optional[float] = None) -> int:
        """等待并返回当前轮次"""
        result = super().wait(timeout)
        if result == 0:
            self._round += 1
        return result

    @property
    def round(self) -> int:
        """获取当前轮次"""
        return self._round


class Phaser:
    """
    分阶段器

    更灵活的同步原语，支持：
    - 动态注册/注销参与线程
    - 多阶段同步
    - 每阶段执行动作
    """

    def __init__(self, parties: int = 0, name: str = ""):
        """
        初始化分阶段器

        Args:
            parties: 初始参与线程数
            name: 名称
        """
        self._name = name or f"phaser_{id(self)}"
        self._lock = threading.Lock()
        self._parties = parties
        self._waiting = 0
        self._phase = 0
        self._logger = Logger()

    def register(self, count: int = 1) -> int:
        """
        注册参与线程

        Args:
            count: 注册数量

        Returns:
            int: 当前阶段号
        """
        with self._lock:
            self._parties += count
            return self._phase

    def arrive(self) -> int:
        """
        到达但不等待

        Returns:
            int: 当前阶段号
        """
        with self._lock:
            self._waiting += 1
            if self._waiting == self._parties:
                self._advance()
            return self._phase

    def arrive_and_wait(self) -> int:
        """
        到达并等待

        Returns:
            int: 当前阶段号
        """
        with self._lock:
            phase = self._phase
            self._waiting += 1

            if self._waiting == self._parties:
                self._advance()
                return self._phase

        # 等待阶段推进
        while True:
            with self._lock:
                if self._phase != phase:
                    return self._phase
            time.sleep(0.01)

    def arrive_and_deregister(self) -> int:
        """
        到达并注销

        Returns:
            int: 当前阶段号
        """
        with self._lock:
            self._waiting += 1
            self._parties -= 1

            if self._waiting == self._parties:
                self._advance()
            return self._phase

    def _advance(self):
        """推进到下一阶段"""
        self._waiting = 0
        self._phase += 1
        self._logger.info(f"分阶段器 '{self._name}' 推进到阶段 {self._phase}")

    @property
    def phase(self) -> int:
        """获取当前阶段"""
        return self._phase

    @property
    def registered_parties(self) -> int:
        """获取注册的参与线程数"""
        return self._parties


# 使用示例
if __name__ == "__main__":
    print("=== 屏障使用示例 ===\n")

    # 示例1: 基本屏障
    print("1. 基本屏障 - 多线程同步")
    barrier = Barrier(count=3, name="sync_point")

    def worker(wid):
        print(f"  线程{wid} 开始工作...")
        time.sleep(0.5 * (wid + 1))
        print(f"  线程{wid} 到达屏障")
        barrier.wait()
        print(f"  线程{wid} 继续执行")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"\n  统计: {barrier.get_stats()}")

    # 示例2: 循环屏障
    print("\n2. 循环屏障 - 多轮同步")
    cyclic = CyclicBarrier(count=2, name="cyclic")

    def cyclic_worker(wid):
        for r in range(3):
            print(f"  线程{wid} 第{r}轮工作...")
            time.sleep(0.2)
            cyclic.wait()
            print(f"  线程{wid} 第{r}轮完成")

    threads = [threading.Thread(target=cyclic_worker, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"\n  完成轮次: {cyclic.round}")

    # 示例3: 屏障动作
    print("\n3. 屏障动作 - 释放时执行函数")

    def on_release():
        print("  >>> 所有线程到达，执行屏障动作 <<<")

    barrier_with_action = Barrier(count=2, name="action_barrier", action=on_release)

    def action_worker(wid):
        print(f"  线程{wid} 到达")
        barrier_with_action.wait()
        print(f"  线程{wid} 继续")

    threads = [threading.Thread(target=action_worker, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
