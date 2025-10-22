"""Inventory domain contracts for future integrations."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field


class Product(BaseModel):
    """Normalized product model used across the bot."""

    sku: str
    category: str
    name: str
    brand: str
    country: str | None = None
    use: list[str] = Field(default_factory=list)
    pile_type: str | None = None
    backing: str | None = None
    fiber: str | None = None
    composition: str | None = None
    props: list[str] = Field(default_factory=list)
    usage_class: str | None = Field(default=None, alias="class")
    fire_cert: str | None = None
    pile_height: str | None = None
    color: str | None = None
    pattern: str | None = None
    shape: str | None = None
    lock: str | None = None
    pack_step_m2: float | None = None
    image_url: str | None = None
    description: str | None = None

    model_config = {"populate_by_name": True}


class CategoryDescriptor(BaseModel):
    """Basic information about a catalogue category."""

    name: str
    filters: list[str] = Field(default_factory=list)


class InventoryPort(Protocol):
    """Abstraction for integrating different inventory data sources."""

    def categories(self) -> list[CategoryDescriptor]:
        """Return all available categories and their filters."""

    def search(self, category: str, filters: dict[str, Any]) -> list[Product]:
        """Search for products by category and filters."""

    def get(self, sku: str) -> Product | None:
        """Retrieve product by SKU."""

    def stock(self, sku: str) -> float | None:
        """Return available stock in square meters if known."""

    def filter_options(self, category: str, filter_name: str) -> list[str]:
        """Return available options for the given filter within a category."""


__all__ = ["InventoryPort", "Product", "CategoryDescriptor"]
