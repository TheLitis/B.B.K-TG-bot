"""Handlers for managing the user's selection basket."""

from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardMarkup, Message

from ..context import get_app_context
from ..keyboards.catalog import selection_manage_keyboard
from ..services.selection_store import SelectionEntry
from ..services.wizard_memory import wizard_memory
from ..states import SelectionMetrics
from ..utils.formatting import calc_required

router = Router(name="selection")


@router.callback_query(F.data.startswith("selection:add:"))
async def add_to_selection(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    sku = callback.data.split(":")[2]
    user_id = callback.from_user.id if callback.from_user else 0
    if not user_id:
        await callback.answer("Не удаётся определить пользователя.")
        return

    product = ctx.inventory.get(sku)
    if not product:
        await callback.answer("Товар не найден.")
        return

    memory = wizard_memory().get_item(user_id, sku)
    if memory:
        entry = SelectionEntry(
            sku=sku,
            name=product.name,
            category=product.category,
            brand=product.brand,
            area_m2=float(memory.get("area_m2", 0)),
            waste_pct=int(memory.get("waste_pct", 0)),
            total_m2=float(memory.get("total_m2", 0)),
            pack_step=memory.get("pack_step"),
        )
        ctx.selection_store.add(user_id, entry)
        await callback.answer("Добавлено в подборку.")
        summary_text, keyboard = _selection_summary(user_id)
        await callback.message.answer(summary_text, reply_markup=keyboard)
        return

    await callback.answer()
    await state.set_state(SelectionMetrics.sku)
    await state.update_data(pending_sku=sku)
    await callback.message.answer(
        "Введите площадь и запас в формате «площадь запас», например: 120 7"
    )


@router.message(SelectionMetrics.sku)
async def collect_selection_metrics(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    data = await state.get_data()
    sku = data.get("pending_sku")
    if not sku:
        await message.answer("Не удалось определить товар, попробуйте ещё раз.")
        await state.clear()
        return

    parts = (message.text or "").replace(",", ".").split()
    if not parts:
        await message.answer("Пример: 96 5")
        return

    try:
        area = float(parts[0])
        waste = int(parts[1]) if len(parts) > 1 else 5
    except ValueError:
        await message.answer("Не удалось распознать числа. Пример: 140 8")
        return

    product = ctx.inventory.get(sku)
    if not product:
        await message.answer("Товар не найден в каталоге.")
        await state.clear()
        return

    total = calc_required(area, waste, product.pack_step_m2)
    entry = SelectionEntry(
        sku=sku,
        name=product.name,
        category=product.category,
        brand=product.brand,
        area_m2=area,
        waste_pct=waste,
        total_m2=total,
        pack_step=product.pack_step_m2,
    )

    user_id = message.from_user.id if message.from_user else 0
    if user_id:
        ctx.selection_store.add(user_id, entry)
        summary_text, keyboard = _selection_summary(user_id)
        await message.answer(
            "Позиция добавлена в подборку.\n" + summary_text,
            reply_markup=keyboard,
        )
    else:
        await message.answer("Не удалось привязать подборку к пользователю.")

    await state.clear()


@router.callback_query(F.data == "selection:clear")
async def clear_selection(callback: CallbackQuery) -> None:
    ctx = get_app_context()
    user_id = callback.from_user.id if callback.from_user else 0
    if not user_id:
        await callback.answer("Не удалось определить пользователя.")
        return

    ctx.selection_store.clear(user_id)
    await callback.answer("Подборка очищена.")
    await callback.message.answer("Подборка очищена.")


@router.callback_query(F.data == "selection:export")
async def export_selection(callback: CallbackQuery) -> None:
    ctx = get_app_context()
    user_id = callback.from_user.id if callback.from_user else 0
    if not user_id:
        await callback.answer("Не удалось определить пользователя.")
        return

    items = ctx.selection_store.to_lines(user_id)
    if not items:
        await callback.answer("Подборка пуста.")
        return

    customer = {
        "Телеграм": f"@{callback.from_user.username}" if callback.from_user else "",
        "Имя": callback.from_user.full_name if callback.from_user else "",
    }

    from ..services.export import selection_to_workbook

    payload = selection_to_workbook(items, customer=customer, company=ctx.text_library.company)
    document = BufferedInputFile(payload.getvalue(), filename="lgpol_podbor.xlsx")
    await callback.message.answer_document(document, caption="Экспорт подборки готов.")
    await callback.answer("Файл сформирован.")


@router.callback_query(F.data == "selection:send")
async def send_selection_to_manager(callback: CallbackQuery) -> None:
    ctx = get_app_context()
    user = callback.from_user
    user_id = user.id if user else 0
    if not user_id:
        await callback.answer("Не удалось определить пользователя.")
        return

    items = ctx.selection_store.to_lines(user_id)
    if not items:
        await callback.answer("Подборка пуста.")
        return

    from ..utils.formatting import mention_html

    customer = {
        "Имя": user.full_name if user else "",
        "Телеграм": f"@{user.username}" if user and user.username else "",
        "ID": user_id,
    }

    from ..services.export import selection_to_workbook

    payload = selection_to_workbook(items, customer=customer, company=ctx.text_library.company)
    document = BufferedInputFile(payload.getvalue(), filename=f"lgpol_request_{user_id}.xlsx")
    manager_chat = ctx.settings.manager_chat_id
    mention = mention_html(user)
    await callback.bot.send_message(
        manager_chat,
        f"Новая заявка из подборки от {mention}.",
    )
    await callback.bot.send_document(manager_chat, document)
    await callback.answer("Отправили заявку менеджеру.")
    await callback.message.answer("Заявка передана менеджеру. Мы свяжемся с вами отдельно.")


def _selection_summary(user_id: int) -> tuple[str, InlineKeyboardMarkup | None]:
    ctx = get_app_context()
    items = ctx.selection_store.list(user_id)
    if not items:
        return "Подборка пуста.", None

    lines = [
        "Текущая подборка:",
    ]
    total = 0.0
    for entry in items:
        lines.append(
            f"- {entry.name} ({entry.sku}) — {entry.total_m2:.2f} м² с запасом {entry.waste_pct}%"
        )
        total += entry.total_m2

    lines.append(f"Итого: {total:.2f} м²")
    lines.append("Можно экспортировать в Excel или отправить менеджеру.")
    return "\n".join(lines), selection_manage_keyboard()
