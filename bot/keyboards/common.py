"""Common keyboard factories."""

from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def build_main_menu(labels: dict[str, str]) -> ReplyKeyboardMarkup:
    """Create the main reply keyboard from non-empty labels.

    Hide a menu item by setting its label to an empty string in styles.yaml.
    Layout: 2 buttons per row.
    """

    order = [
        "pick",
        "catalog",
        "delivery",
        "payment",
        "promos",
        "samples",
        "manager",
        "contacts",
    ]

    buttons: list[KeyboardButton] = []
    for key in order:
        text = labels.get(key)
        if text and text.strip():
            buttons.append(KeyboardButton(text=text))

    rows: list[list[KeyboardButton]] = []
    for i in range(0, len(buttons), 2):
        rows.append(buttons[i : i + 2])

    if not rows:
        rows = [[KeyboardButton(text="🧭 Подбор")]]

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def yes_no_keyboard(yes_text: str = "Да", no_text: str = "Нет") -> InlineKeyboardMarkup:
    """Common inline keyboard for confirmation prompts."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=yes_text, callback_data="yes")],
            [InlineKeyboardButton(text=no_text, callback_data="no")],
        ]
    )


def consent_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard button to capture consent for personal data processing."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Согласен",
                    callback_data="consent_yes",
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="consent_no",
                ),
            ]
        ]
    )


def back_to_menu_button(text: str = "⬅️ В меню") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data="back_to_menu")]]
    )


__all__ = [
    "build_main_menu",
    "yes_no_keyboard",
    "consent_keyboard",
    "back_to_menu_button",
]
