"""Local JSON-backed inventory stub implementation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .inventory_port import CategoryDescriptor, InventoryPort, Product

FILTER_KEY_MAP: dict[str, str] = {
    "Производитель": "brand",
    "Страна": "country",
    "Область применения": "use",
    "Тип ворса": "pile_type",
    "Основа": "backing",
    "Состав ворса": "fiber",
    "Состав": "composition",
    "Класс": "usage_class",
    "Высота ворса": "pile_height",
    "Пожарный сертификат": "fire_cert",
    "Цвет": "color",
    "Тип рисунка": "pattern",
    "Свойства": "props",
    "Тип соединения": "lock",
    "Форма": "shape",
}


@dataclass(slots=True)
class CatalogNode:
    """Helper container for category data."""

    descriptor: CategoryDescriptor
    products: list[Product]


class InventoryStub(InventoryPort):
    """Simple inventory provider that reads catalogue data from JSON files."""

    def __init__(self, data_path: Path):
        self.data_path = data_path
        self._catalog: dict[str, CatalogNode] = {}
        self._products_index: dict[str, Product] = {}
        self.reload()

    def reload(self) -> None:
        """Reload catalogue data from disk."""

        if not self.data_path.exists():
            raise FileNotFoundError(f"Catalog file not found: {self.data_path}")

        content = json.loads(self.data_path.read_text(encoding="utf-8"))
        catalog: dict[str, CatalogNode] = {}
        index: dict[str, Product] = {}

        for category_name, payload in content.items():
            filters = payload.get("filters", [])
            descriptor = CategoryDescriptor(name=category_name, filters=filters)

            products_block = payload.get("products", [])
            products: list[Product] = []
            for raw in products_block:
                raw_copy = dict(raw)
                raw_copy["category"] = category_name
                try:
                    product = Product.model_validate(raw_copy)
                except ValidationError as exc:
                    raise ValueError(f"Invalid product entry for {category_name}: {raw}") from exc

                products.append(product)
                index[product.sku] = product

            catalog[category_name] = CatalogNode(descriptor=descriptor, products=products)

        self._catalog = catalog
        self._products_index = index

    # InventoryPort implementation -------------------------------------------------

    def categories(self) -> list[CategoryDescriptor]:
        return [node.descriptor for node in self._catalog.values()]

    def search(self, category: str, filters: dict[str, Any]) -> list[Product]:
        node = self._catalog.get(category)
        if not node:
            return []

        if not filters:
            return list(node.products)

        matched = []
        for product in node.products:
            if self._matches(product, filters):
                matched.append(product)

        return matched

    def get(self, sku: str) -> Product | None:
        return self._products_index.get(sku)

    def stock(self, sku: str) -> float | None:  # noqa: D401 - compatibility placeholder
        """Return stock information if present (stub always returns None)."""

        return None

    def filter_options(self, category: str, filter_name: str) -> list[str]:
        node = self._catalog.get(category)
        if not node:
            return []

        attr_name = FILTER_KEY_MAP.get(filter_name, filter_name)
        options: set[str] = set()

        for product in node.products:
            value = getattr(product, attr_name, None)
            if isinstance(value, list):
                options.update(str(item) for item in value if item is not None)
            elif value is not None:
                options.add(str(value))

        return sorted(options)

    # Helpers ---------------------------------------------------------------------

    def _matches(self, product: Product, filters: dict[str, Any]) -> bool:
        for filter_name, filter_value in filters.items():
            attr_name = FILTER_KEY_MAP.get(filter_name, filter_name)
            if not hasattr(product, attr_name):
                continue

            product_value = getattr(product, attr_name)
            if product_value is None:
                return False

            if isinstance(product_value, list):
                if isinstance(filter_value, (list, tuple, set)):
                    if not any(self._value_match(item, product_value) for item in filter_value):
                        return False
                else:
                    if not self._value_match(filter_value, product_value):
                        return False
            else:
                if isinstance(filter_value, (list, tuple, set)):
                    if not any(self._value_match(value, product_value) for value in filter_value):
                        return False
                else:
                    if not self._value_match(filter_value, product_value):
                        return False

        return True

    @staticmethod
    def _value_match(expected: Any, actual: Any) -> bool:
        if isinstance(actual, list):
            return any(InventoryStub._value_match(expected, item) for item in actual)

        if expected is None:
            return True

        expected_str = str(expected).strip().lower()
        actual_str = str(actual).strip().lower()
        return expected_str == actual_str


__all__ = ["InventoryStub", "FILTER_KEY_MAP"]
