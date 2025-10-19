"""Aggregate all routers for import convenience."""

from . import (
    cart_like_selection,
    catalog_browse,
    delivery_payment,
    partners,
    start,
    support_feedback,
    wizard_picker,
)

__all__ = [
    "start",
    "wizard_picker",
    "catalog_browse",
    "cart_like_selection",
    "delivery_payment",
    "partners",
    "support_feedback",
]

