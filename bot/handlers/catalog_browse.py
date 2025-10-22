"""Handlers for browsing the catalogue via inline keyboards."""

from __future__ import annotations

from typing import Any
import hashlib

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..context import get_app_context
from ..filters import menu_choice
from ..keyboards.catalog import (
    categories_keyboard,
    filter_keyboard,
    product_actions_keyboard,
)

router = Router(name="catalog")

SESSION_KEY = "catalog_flow"

def _encode_option_key(filter_name: str, option: str) -> str:
    raw = f"{filter_name}:{option}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:10]


@router.message(menu_choice("catalog"))
async def show_catalog_menu(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    categories = [descriptor.name for descriptor in ctx.inventory.categories()]
    await state.update_data(
        {SESSION_KEY: {"filters": {}, "category": None, "step": 0}, "catalog_options": {}}
    )
    intro = ctx.text_library.styles.get(
        "catalog_intro", "Выберите категорию напольного покрытия:"
    )
    await message.answer(intro, reply_markup=categories_keyboard(categories))


@router.callback_query(F.data.startswith("catalog:category:"))
async def pick_category(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    _, _, category = callback.data.partition("catalog:category:")
    await callback.answer()
    catalog_data = {SESSION_KEY: {"filters": {}, "category": category, "step": 0}}
    await state.update_data({**catalog_data, "catalog_options": {}})
    await _ask_next_filter(callback.message, state, category, 0, {})


@router.callback_query(F.data.startswith("catalog:filter:"))
async def apply_filter(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    ctx = get_app_context()
    data = await state.get_data()
    flow: dict[str, Any] = data.get(SESSION_KEY, {})
    category = flow.get("category")
    if not category:
        await callback.message.answer("Сначала выберите категорию.")
        return

    _, _, payload = callback.data.partition("catalog:filter:")
    filter_name, _, option_key = payload.partition(":")
    options_map: dict[str, str] = data.get("catalog_options", {}).get(filter_name, {})
    option = options_map.get(option_key)
    if not option:
        await callback.message.answer("Не удалось обработать выбор. Попробуйте ещё раз.")
        await _ask_next_filter(callback.message, state, category, flow.get("step", 0), flow.get("filters", {}))
        return
    filters: dict[str, str] = dict(flow.get("filters", {}))
    filters[filter_name] = option
    step = flow.get("step", 0) + 1

    await state.update_data(
        {
            SESSION_KEY: {"category": category, "filters": filters, "step": step},
        }
    )

    await _ask_next_filter(callback.message, state, category, step, filters)


@router.callback_query(F.data.startswith("catalog:skip:"))
async def skip_filter(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    flow: dict[str, Any] = data.get(SESSION_KEY, {})
    category = flow.get("category")
    if not category:
        await callback.message.answer("Сначала выберите категорию.")
        return

    step = flow.get("step", 0) + 1
    filters = dict(flow.get("filters", {}))
    await state.update_data({SESSION_KEY: {"category": category, "filters": filters, "step": step}})
    await _ask_next_filter(callback.message, state, category, step, filters)


@router.callback_query(F.data == "catalog:filters:back")
async def back_in_filters(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    flow = data.get(SESSION_KEY, {})
    category = flow.get("category")
    filters = dict(flow.get("filters", {}))
    step = max(flow.get("step", 0) - 1, 0)
    await state.update_data({SESSION_KEY: {"category": category, "filters": filters, "step": step}})
    await _ask_next_filter(callback.message, state, category, step, filters)


@router.callback_query(F.data == "catalog:back")
async def exit_catalog(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data({SESSION_KEY: {"filters": {}, "category": None, "step": 0}})
    ctx = get_app_context()
    text = ctx.text_library.styles.get(
        "catalog_exit", "Готово. Вы всегда можете вернуться к каталогу из меню."
    )
    await callback.message.answer(text)


async def _ask_next_filter(
    message: Message | None,
    state: FSMContext,
    category: str,
    step: int,
    filters: dict[str, str],
) -> None:
    if message is None:
        return

    ctx = get_app_context()
    descriptor = next(
        (item for item in ctx.inventory.categories() if item.name == category),
        None,
    )
    if not descriptor:
        await message.answer("Категория не найдена.")
        return

    if step >= len(descriptor.filters):
        await state.update_data({"catalog_options": {}})
        await _show_results(message, state, category, filters)
        return

    filter_name = descriptor.filters[step]
    options = ctx.inventory.filter_options(category, filter_name)

    if not options:
        await _ask_next_filter(message, state, category, step + 1, filters)
        return

    option_map = {_encode_option_key(filter_name, option): option for option in options}
    data = await state.get_data()
    catalog_options = dict(data.get("catalog_options", {}))
    catalog_options[filter_name] = option_map
    await state.update_data({"catalog_options": catalog_options})

    question_template = ctx.text_library.styles.get(
        "catalog_filter_question",
        "Выберите значение для фильтра «{filter}»:",
    )
    await message.answer(
        question_template.format(filter=filter_name),
        reply_markup=filter_keyboard(filter_name, option_map),
    )


async def _show_results(
    message: Message,
    state: FSMContext,
    category: str,
    filters: dict[str, str],
) -> None:
    ctx = get_app_context()
    products = ctx.inventory.search(category, filters)
    if not products:
        categories = [descriptor.name for descriptor in ctx.inventory.categories()]
        await state.update_data(
            {SESSION_KEY: {"filters": {}, "category": None, "step": 0}, "catalog_options": {}}
        )
        prompt = ctx.text_library.styles.get(
            "catalog_no_results",
            "Не нашёл подходящих позиций. Попробуем ослабить фильтры или выбрать другую категорию?",
        )
        await message.answer(prompt, reply_markup=categories_keyboard(categories))
        return

    intro_template = ctx.text_library.styles.get(
        "catalog_results_intro",
        "Нашли {count} вариантов по заданным условиям:",
    )
    await message.answer(intro_template.format(count=len(products)))

    for product in products[:6]:
        price = ctx.pricing.price(product.sku)
        text = ctx.text_library.render_product_card(product, price=price)
        await message.answer(text, reply_markup=product_actions_keyboard(product))
