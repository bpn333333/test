"""音声を複数の接続へ配る仕組み。

音の取り込み口(スピーカー出力)は 1 つしか開けないため、取り込みは 1 本にまとめ、
聞いているクライアントそれぞれの待ち行列へ配る。誰も聞いていない間は
取り込み自体を止めて、CPU と権限の占有を避ける。
"""

from __future__ import annotations

import asyncio
import logging

from .audio import AudioUnavailable, LoopbackCapture

logger = logging.getLogger("rdcontrol.audio")

# 各クライアントの待ち行列の長さ。詰まったら古い分から捨てる(音は遅れるより飛ばす)
QUEUE_SIZE = 8


class AudioHub:
    def __init__(self, factory=LoopbackCapture) -> None:
        self._factory = factory
        self._capture = None
        self._task: asyncio.Task | None = None
        self._queues: set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    @property
    def listeners(self) -> int:
        return len(self._queues)

    async def subscribe(self) -> asyncio.Queue:
        """音声の受け取りを開始する。取り込めない場合は AudioUnavailable。"""
        async with self._lock:
            if self._capture is None:
                # デバイスを開く処理は待たされることがあるので別スレッドで行う
                self._capture = await asyncio.to_thread(self._factory)
            queue: asyncio.Queue = asyncio.Queue(maxsize=QUEUE_SIZE)
            self._queues.add(queue)
            if self._task is None or self._task.done():
                self._task = asyncio.create_task(self._pump())
            return queue

    async def unsubscribe(self, queue: asyncio.Queue) -> None:
        async with self._lock:
            self._queues.discard(queue)
            if self._queues:
                return
            await self._shutdown()

    async def aclose(self) -> None:
        async with self._lock:
            self._queues.clear()
            await self._shutdown()

    async def _shutdown(self) -> None:
        task, self._task = self._task, None
        if task is not None:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        capture, self._capture = self._capture, None
        if capture is not None:
            await asyncio.to_thread(capture.close)

    async def _pump(self) -> None:
        """取り込んだ音を、聞いている全員へ配り続ける。"""
        while True:
            capture = self._capture
            if capture is None:
                return
            try:
                chunk = await asyncio.to_thread(capture.read)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("音声の取り込みが止まりました: %s", exc)
                for queue in list(self._queues):
                    _offer(queue, None)   # 終了を伝える
                return
            for queue in list(self._queues):
                _offer(queue, chunk)


def _offer(queue: asyncio.Queue, item) -> None:
    """待ち行列へ入れる。詰まっていたら古いものを捨てて入れ直す。"""
    try:
        queue.put_nowait(item)
    except asyncio.QueueFull:
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
        try:
            queue.put_nowait(item)
        except asyncio.QueueFull:
            pass


__all__ = ["AudioHub", "AudioUnavailable"]
