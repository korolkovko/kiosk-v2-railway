# app/websockets/event_bus.py
# Мини-шина событий в памяти для одного процесса приложения.
# Поддерживает несколько подписчиков на один канал (kiosk_username).
# Используется сейчас SSE, позже можно теми же методами кормить WebSocket.

import asyncio
from collections import defaultdict
from typing import AsyncIterator, Dict, Set

class EventBus:
    def __init__(self, per_queue_max: int = 100) -> None:
        # channel -> set of queues
        self._subs: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self._per_queue_max = per_queue_max

    async def subscribe(self, channel: str) -> AsyncIterator[dict]:
        """
        Подписка на канал (например, kiosk_username).
        Возвращает асинхронный итератор событий (dict).
        """
        q: asyncio.Queue = asyncio.Queue(self._per_queue_max)
        async with self._lock:
            self._subs[channel].add(q)
            print(f"🔔 EVENT BUS: New subscription to channel '{channel}'. Total subscribers: {len(self._subs[channel])}")
        try:
            while True:
                event = await q.get()
                print(f"🎯 EVENT BUS: Delivering event to subscriber on channel '{channel}': {event}")
                yield event
        finally:
            async with self._lock:
                self._subs[channel].discard(q)
                remaining = len(self._subs[channel])
                if not self._subs[channel]:
                    self._subs.pop(channel, None)
                print(f"🔕 EVENT BUS: Subscription ended for channel '{channel}'. Remaining subscribers: {remaining}")

    async def publish(self, channel: str, event: dict) -> None:
        """
        Публикация события в канал. Не блокирует обработчики.
        При переполнении локальной очереди — вытесняет самый старый элемент.
        """
        qs = list(self._subs.get(channel, ()))
        print(f"📢 EVENT BUS: Publishing to channel '{channel}' with {len(qs)} subscribers")
        for q in qs:
            try:
                q.put_nowait(event)
                print(f"✅ EVENT BUS: Event queued successfully")
            except asyncio.QueueFull:
                # держим «последние» события: вытесним oldest и положим новое
                print(f"⚠️ EVENT BUS: Queue full, evicting oldest event")
                try:
                    _ = q.get_nowait()
                except Exception:
                    pass
                await q.put(event)

# Глобальный экземпляр на процесс приложения
bus = EventBus()