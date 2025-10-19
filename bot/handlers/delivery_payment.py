"""Handlers for delivery and payment sections."""

from __future__ import annotations

from aiogram import Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..context import get_app_context
from ..filters import menu_choice

router = Router(name="delivery_payment")


def _logistics_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Задать вопрос", callback_data="manager:question")],
            [
                InlineKeyboardButton(
                    text="Рассчитать логистику",
                    callback_data="manager:logistics",
                )
            ],
        ]
    )


@router.message(menu_choice("delivery"))
async def delivery_block(message: Message) -> None:
    ctx = get_app_context()
    await message.answer(ctx.text_library.delivery, reply_markup=_logistics_keyboard())


@router.message(menu_choice("payment"))
async def payment_block(message: Message) -> None:
    ctx = get_app_context()
    excerpt = ctx.text_library.styles.get(
        "payment_intro",
        "Принимаем оплату наличными, по безналичному расчёту и банковскими картами.",
    )
    await message.answer(excerpt, reply_markup=_logistics_keyboard())
