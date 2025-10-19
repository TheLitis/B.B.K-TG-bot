"""Context utilities for accessing application singletons inside handlers."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass

from .config import Settings
from .services.inventory_port import InventoryPort
from .services.pricing_port import PricingPort
from .services.selection_store import SelectionStore
from .services.text_templates import TextLibrary


@dataclass(slots=True)
class AppContext:
    """Container with long-lived services."""

    text_library: TextLibrary
    inventory: InventoryPort
    pricing: PricingPort
    selection_store: SelectionStore
    settings: Settings


_context_var: ContextVar[AppContext] = ContextVar("app_context")


def set_app_context(context: AppContext) -> None:
    _context_var.set(context)


def get_app_context() -> AppContext:
    return _context_var.get()


__all__ = ["AppContext", "set_app_context", "get_app_context"]
