"""Handlers for promotions and partner programs."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..context import get_app_context
from ..filters import menu_choice

router = Router(name="partners")


def _promo_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🤝 Партнёрство", callback_data="partners:info"
                )
            ]
        ]
    )


@router.message(menu_choice("promos"))
async def show_promos(message: Message) -> None:
    ctx = get_app_context()
    promos = ctx.pricing.promos()
    if promos:
        lines = ["🎯 Актуальные акции:"]
        for promo in promos:
            until = f"до {promo.valid_until.strftime('%d.%m.%Y')}" if promo.valid_until else "без срока"
            lines.append(f"• {promo.title} ({until})\n  {promo.description}")
    else:
        lines = ["Пока нет активных акций. Мы сообщим, когда появятся новинки."]
    await message.answer("\n".join(lines), reply_markup=_promo_keyboard())


@router.callback_query(F.data == "partners:info")
async def partner_info(callback: CallbackQuery) -> None:
    ctx = get_app_context()
    partner_text = ctx.text_library.styles.get(
        "partners_intro",
        "Работаем с дизайнерами, дилерами, подрядчиками и оптовыми клиентами. "
        "Предлагаем персональные условия, образцы и быстрые поставки.",
    )
    await callback.answer()
    await callback.message.answer(partner_text)
