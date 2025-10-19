"""Inline keyboards for catalogue interactions."""

from __future__ import annotations

from typing import Iterable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..services.inventory_port import Product


def categories_keyboard(categories: Iterable[str]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"catalog:category:{name}")]
        for name in categories
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="catalog:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def filter_keyboard(filter_name: str, options: Iterable[str]) -> InlineKeyboardMarkup:
    keyboard: list[list[InlineKeyboardButton]] = []
    for option in options:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=option,
                    callback_data=f"catalog:filter:{filter_name}:{option}",
                )
            ]
        )
    keyboard.append(
        [InlineKeyboardButton(text="Пропустить", callback_data=f"catalog:skip:{filter_name}")]
    )
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog:filters:back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def product_actions_keyboard(product: Product) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ В подборку",
                    callback_data=f"selection:add:{product.sku}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📦 Образцы",
                    callback_data=f"selection:samples:{product.sku}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📄 Паспорт",
                    callback_data=f"selection:passport:{product.sku}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✉️ Запрос счёта",
                    callback_data=f"selection:quote:{product.sku}",
                )
            ],
        ]
    )


def selection_manage_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 Очистить", callback_data="selection:clear"),
                InlineKeyboardButton(text="📊 Экспорт XLSX", callback_data="selection:export"),
            ],
            [
                InlineKeyboardButton(text="✉️ Менеджеру", callback_data="selection:send"),
            ],
        ]
    )


__all__ = [
    "categories_keyboard",
    "filter_keyboard",
    "product_actions_keyboard",
    "selection_manage_keyboard",
]

