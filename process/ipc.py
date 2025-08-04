"""Simple inter-process communication primitives."""

from __future__ import annotations

import threading
from collections import deque
from typing import Any


class MessageQueue:
    """A thread-safe message queue for process communication.

    Processes can send and receive messages through this queue. The
    implementation uses a FIFO buffer protected by a lock and condition
    variable to ensure safe access between producers and consumers.
    """

    def __init__(self) -> None:
        self._queue: deque[Any] = deque()
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)

    def send(self, message: Any) -> None:
        """Send a message to the queue.

        Args:
            message: Arbitrary data to enqueue.
        """
        with self._lock:
            self._queue.append(message)
            self._not_empty.notify()

    def receive(self) -> Any:
        """Receive a message from the queue.

        Blocks until a message is available and returns it.
        """
        with self._not_empty:
            while not self._queue:
                self._not_empty.wait()
            return self._queue.popleft()
