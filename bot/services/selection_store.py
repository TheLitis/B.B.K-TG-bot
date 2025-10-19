"""Simple in-memory selection storage with JSON autosave."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .export import SelectionLine


@dataclass(slots=True)
class SelectionEntry:
    """Selection entry stored for a user."""

    sku: str
    name: str
    category: str
    brand: str
    area_m2: float
    waste_pct: int
    total_m2: float
    pack_step: float | None = None
    notes: str | None = None

    def to_line(self) -> SelectionLine:
        return SelectionLine(
            sku=self.sku,
            name=self.name,
            category=self.category,
            brand=self.brand,
            area_m2=self.area_m2,
            waste_pct=self.waste_pct,
            total_m2=self.total_m2,
            pack_step=self.pack_step,
            notes=self.notes,
        )


class SelectionStore:
    """In-memory selection storage with optional autosave to disk."""

    def __init__(self, tmp_dir: Path, autosave: bool = True):
        self.tmp_dir = tmp_dir
        self.autosave = autosave
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self._data: dict[int, list[SelectionEntry]] = {}
        self._load_existing()

    # Public API -----------------------------------------------------------------

    def list(self, user_id: int) -> list[SelectionEntry]:
        return list(self._data.get(user_id, []))

    def add(self, user_id: int, entry: SelectionEntry) -> None:
        entries = self._data.setdefault(user_id, [])
        # Replace existing SKU if present
        entries = [item for item in entries if item.sku != entry.sku]
        entries.append(entry)
        self._data[user_id] = entries
        self._persist(user_id)

    def remove(self, user_id: int, sku: str) -> bool:
        entries = self._data.get(user_id, [])
        new_entries = [item for item in entries if item.sku != sku]
        if len(new_entries) == len(entries):
            return False
        self._data[user_id] = new_entries
        self._persist(user_id)
        return True

    def clear(self, user_id: int) -> None:
        self._data.pop(user_id, None)
        self._persist(user_id)

    def to_lines(self, user_id: int) -> list[SelectionLine]:
        return [entry.to_line() for entry in self.list(user_id)]

    # Internal helpers -----------------------------------------------------------

    def _persist(self, user_id: int) -> None:
        if not self.autosave:
            return
        path = self._user_file(user_id)
        entries = [asdict(entry) for entry in self._data.get(user_id, [])]
        if entries:
            path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
        elif path.exists():
            path.unlink()

    def _load_existing(self) -> None:
        if not self.autosave:
            return
        for path in self.tmp_dir.glob("selection_*.json"):
            try:
                user_id = int(path.stem.split("_")[1])
            except (IndexError, ValueError):
                continue
            raw_entries = json.loads(path.read_text(encoding="utf-8"))
            entries: list[SelectionEntry] = []
            for item in raw_entries:
                entries.append(
                    SelectionEntry(
                        sku=item["sku"],
                        name=item.get("name", ""),
                        category=item.get("category", ""),
                        brand=item.get("brand", ""),
                        area_m2=float(item.get("area_m2", 0)),
                        waste_pct=int(item.get("waste_pct", 0)),
                        total_m2=float(item.get("total_m2", 0)),
                        pack_step=item.get("pack_step"),
                        notes=item.get("notes"),
                    )
                )
            if entries:
                self._data[user_id] = entries

    def _user_file(self, user_id: int) -> Path:
        return self.tmp_dir / f"selection_{user_id}.json"


__all__ = ["SelectionStore", "SelectionEntry"]

