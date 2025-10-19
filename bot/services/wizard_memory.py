"""Temporary memory for wizard recommendations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class WizardMemory:
    """Store the latest wizard calculations per user."""

    _storage: dict[int, dict[str, Any]] = field(default_factory=dict)

    def remember(self, user_id: int, data: dict[str, Any]) -> None:
        self._storage[user_id] = data

    def get_item(self, user_id: int, sku: str) -> dict[str, Any] | None:
        entries = self._storage.get(user_id, {})
        return entries.get(sku)

    def all_for(self, user_id: int) -> dict[str, Any]:
        return self._storage.get(user_id, {})


_instance = WizardMemory()


def wizard_memory() -> WizardMemory:
    return _instance


__all__ = ["wizard_memory", "WizardMemory"]
