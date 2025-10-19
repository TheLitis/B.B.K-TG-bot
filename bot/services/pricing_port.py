"""Pricing domain contracts."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from pydantic import BaseModel, Field


class Promo(BaseModel):
    """Marketing promo representation."""

    code: str
    title: str
    description: str
    valid_until: date | None = None
    skus: list[str] = Field(default_factory=list)


class PricingPort(Protocol):
    """Abstraction around price and marketing data."""

    def price(self, sku: str) -> float | None:
        """Return price for the requested SKU if available."""

    def promos(self) -> list[Promo]:
        """Return active promo entries."""


__all__ = ["PricingPort", "Promo"]

