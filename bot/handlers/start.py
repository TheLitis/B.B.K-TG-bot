"""Start and generic menu handlers."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from ..context import get_app_context
from ..keyboards.common import build_main_menu

router = Router(name="start")


@router.message(CommandStart())
async def start(message: Message) -> None:
    ctx = get_app_context()
    labels = ctx.text_library.menu_labels()
    greeting = ctx.text_library.greeting()
    await message.answer(greeting, reply_markup=build_main_menu(labels))


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    ctx = get_app_context()
    labels = ctx.text_library.menu_labels()
    help_lines = [
        "Доступные разделы:",
        labels.get("pick", "🧭 Подбор"),
        labels.get("catalog", "🛍 Каталог"),
        labels.get("delivery", "🚚 Доставка"),
        labels.get("payment", "💳 Оплата"),
        labels.get("promos", "🎯 Акции"),
        labels.get("samples", "📦 Образцы"),
        labels.get("manager", "👤 Менеджер"),
        labels.get("contacts", "📞 Контакты"),
    ]
    await message.answer("\n".join(help_lines), reply_markup=build_main_menu(labels))


@router.message(Command("faq"))
async def faq_command(message: Message) -> None:
    ctx = get_app_context()
    await message.answer(ctx.text_library.faq)
