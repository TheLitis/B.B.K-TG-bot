"""Reusable filters for aiogram routers."""

from __future__ import annotations

from typing import Callable

from aiogram.types import Message

from .context import get_app_context


def menu_choice(key: str) -> Callable[[Message], bool]:
    """Return a filter that matches message text against menu label."""

    async def _predicate(message: Message) -> bool:
        ctx = get_app_context()
        labels = ctx.text_library.menu_labels()
        expected = labels.get(key)
        if not expected:
            return False
        return (message.text or "").strip().lower() == expected.strip().lower()

    return _predicate


__all__ = ["menu_choice"]

