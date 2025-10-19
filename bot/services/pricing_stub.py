"""Pricing stub that keeps demo data in memory."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .pricing_port import PricingPort, Promo


class PricingStub(PricingPort):
    """Simple pricing stub used for demo environments."""

    def __init__(self, data_path: Path | None = None):
        self.data_path = data_path
        self._price_map: dict[str, float] = {}
        self._promos: list[Promo] = []
        self.reload()

    def reload(self) -> None:
        """Reload stub data from disk or fall back to defaults."""

        self._price_map.clear()
        self._promos.clear()

        if self.data_path and self.data_path.exists():
            content = json.loads(self.data_path.read_text(encoding="utf-8"))
            prices = content.get("prices", {})
            promos = content.get("promos", [])
            self._price_map.update({sku: float(value) for sku, value in prices.items()})
            self._promos.extend(self._parse_promos(promos))
            return

        # Default demo data -------------------------------------------------------
        self._price_map = {
            "CR-AW-001": 1250.0,
            "CR-AW-002": 1320.0,
            "CT-RCT-101": 1380.0,
            "CT-RCT-104": 1425.0,
            "LN-TK-201": 890.0,
            "LVT-FF-301": 1620.0,
        }
        self._promos = [
            Promo(
                code="WELCOME-2025",
                title="-5% при заказе ковровой плитки от 100 м²",
                description="Скидка распространяется на серии RusCarpetTiles. "
                "Действует для дизайнеров и корпоративных клиентов.",
                valid_until=date(date.today().year, 12, 31),
                skus=["CT-RCT-101", "CT-RCT-104"],
            ),
            Promo(
                code="SAMPLE-PACK",
                title="Комплект образцов FineFloor",
                description="При заказе покрытия FineFloor отправим набор образцов бесплатно.",
                valid_until=None,
                skus=["LVT-FF-301"],
            ),
        ]

    # PricingPort implementation ----------------------------------------------------

    def price(self, sku: str) -> float | None:
        return self._price_map.get(sku)

    def promos(self) -> list[Promo]:
        return list(self._promos)

    # Helpers -----------------------------------------------------------------------

    def _parse_promos(self, raw_promos: list[dict[str, Any]]) -> list[Promo]:
        parsed: list[Promo] = []
        for item in raw_promos:
            valid = item.get("valid_until")
            valid_until: date | None = None
            if valid:
                if isinstance(valid, (int, float)):
                    valid_until = datetime.utcfromtimestamp(float(valid)).date()
                else:
                    valid_until = datetime.fromisoformat(str(valid)).date()
            parsed.append(
                Promo(
                    code=item.get("code", ""),
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    valid_until=valid_until,
                    skus=list(item.get("skus", [])),
                )
            )
        return parsed


__all__ = ["PricingStub"]

