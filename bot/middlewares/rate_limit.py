"""Simple rate limiting middleware to mitigate flooding."""

from __future__ import annotations

import time
from typing import Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware


class RateLimitMiddleware(BaseMiddleware):
    """Throttle events from the same user within a given interval."""

    def __init__(self, interval: float = 0.6) -> None:
        super().__init__()
        self.interval = interval
        self._last_event_at: Dict[int, float] = {}

    async def __call__(  # type: ignore[override]
        self,
        handler: Callable[[dict, dict], Awaitable],
        event: object,
        data: dict,
    ):
        from_user = getattr(event, "from_user", None)
        if from_user is not None:
            now = time.monotonic()
            last = self._last_event_at.get(from_user.id)
            if last is not None and now - last < self.interval:
                return None
            self._last_event_at[from_user.id] = now
        return await handler(event, data)


__all__ = ["RateLimitMiddleware"]
