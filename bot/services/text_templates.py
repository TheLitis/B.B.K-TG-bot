"""Text and template helpers backed by external content files."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, StrictUndefined

from .inventory_port import Product


class TextLibrary:
    """Load styles, copy, and templates from the data directory."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.styles = self._load_yaml("styles.yaml")
        self.company = self._load_json("company.json")
        self.delivery = self._load_text("delivery.md")
        self.faq = self._load_text("faq.md")

        self.env = Environment(undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
        self.env.globals.update({"company": self.company})
        self.env.filters["fallback"] = lambda value, default="—": value if value else default

    # Loading helpers -------------------------------------------------------------

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        path = self.data_dir / filename
        if not path.exists():
            return {}
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def _load_json(self, filename: str) -> dict[str, Any]:
        path = self.data_dir / filename
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _load_text(self, filename: str) -> str:
        path = self.data_dir / filename
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    # Style accessors -------------------------------------------------------------

    def greeting(self) -> str:
        return self.styles.get("greeting", "Здравствуйте!")

    def menu_labels(self) -> dict[str, str]:
        return self.styles.get("menu_labels", {})

    def picker_questions(self) -> dict[str, str]:
        return self.styles.get("picker_questions", {})

    def picker_options(self) -> dict[str, list[str]]:
        return self.styles.get("picker_options", {})

    def consent_text(self) -> str:
        return self.styles.get(
            "consent_text",
            "Отправляя контакты, вы подтверждаете согласие на обработку персональных данных.",
        )

    def manager_prompts(self) -> dict[str, str]:
        return self.styles.get("manager_prompts", {})

    def render_product_card(
        self,
        product: Product,
        price: float | None = None,
        required_m2: float | None = None,
    ) -> str:
        """Render a textual card describing a product."""

        template = self.env.from_string(
            self.styles.get(
                "product_card_template",
                """
{{ product.category }} • {{ product.brand }} • {{ product.name }}
Страна: {{ product.country|fallback }}
Класс: {{ product.primary_class()|fallback }}
Состав: {{ product.composition|fallback(product.fiber|fallback) }}
Свойства: {{ product.props|join(", ") if product.props else "—" }}
Цвет / рисунок: {{ product.color|fallback }} / {{ product.pattern|fallback }}
Рекомендации: {{ product.use|join(", ") if product.use else "—" }}
{% if required_m2 %}Расчёт: {{ "%.2f"|format(required_m2) }} м²{% endif %}
{% if price %}Ориентир по цене: {{ price | round(2) }} ₽/м²{% endif %}
""",
            )
        )
        return template.render(product=product, price=price, required_m2=required_m2)


@lru_cache(maxsize=1)
def get_text_library(data_dir: Path) -> TextLibrary:
    return TextLibrary(data_dir=data_dir)


__all__ = ["TextLibrary", "get_text_library"]

