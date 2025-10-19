"""Guided wizard that helps users pick flooring solutions."""

from __future__ import annotations

from typing import Any

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ..context import get_app_context
from ..filters import menu_choice
from ..states import PickerWizard
from ..keyboards.catalog import product_actions_keyboard
from ..services.wizard_memory import wizard_memory
from ..utils.formatting import calc_required

router = Router(name="wizard")


async def _maybe_redirect_menu(message: Message, state: FSMContext) -> bool:
    """If user pressed a main menu button during the wizard, exit wizard and route.

    Returns True if handled.
    """
    text = (message.text or "").strip()
    if not text:
        return False

    ctx = get_app_context()
    labels = ctx.text_library.menu_labels()
    # Build reverse map label->key
    rev = {v: k for k, v in labels.items() if v}
    key = rev.get(text)
    if not key:
        return False

    await state.clear()

    # Lazy imports to avoid circulars
    if key == "pick":
        await start_picker(message, state)
        return True
    elif key == "catalog":
        from .catalog_browse import show_catalog_menu

        await show_catalog_menu(message, state)
        return True
    elif key == "delivery":
        from .delivery_payment import delivery_block

        await delivery_block(message)
        return True
    elif key == "payment":
        from .delivery_payment import payment_block

        await payment_block(message)
        return True
    elif key == "promos":
        from .partners import show_promos

        await show_promos(message)
        return True
    elif key == "samples":
        from .support_feedback import samples_start

        await samples_start(message, state)
        return True
    elif key == "manager":
        from .support_feedback import manager_menu

        await manager_menu(message)
        return True
    elif key == "contacts":
        from .support_feedback import contacts

        await contacts(message)
        return True

    return False

@router.message(menu_choice("pick"))
async def start_picker(message: Message, state: FSMContext) -> None:
    await state.clear()
    ctx = get_app_context()
    questions = ctx.text_library.picker_questions()
    options = ctx.text_library.picker_options().get("application_area", [])
    await state.set_state(PickerWizard.application_area)
    await message.answer(questions.get("application_area", "Для какого объекта ищем покрытие?"))
    if options:
        await message.answer("\n".join(options))


@router.message(PickerWizard.application_area)
async def handle_application_area(message: Message, state: FSMContext) -> None:
    if await _maybe_redirect_menu(message, state):
        return
    await state.update_data(application_area=message.text.strip())
    ctx = get_app_context()
    questions = ctx.text_library.picker_questions()
    options = ctx.text_library.picker_options().get("material_type", [])
    await state.set_state(PickerWizard.material_type)
    await message.answer(questions.get("material_type", "Какой тип материала рассматриваете?"))
    if options:
        await message.answer("\n".join(options))


@router.message(PickerWizard.material_type)
async def handle_material_type(message: Message, state: FSMContext) -> None:
    if await _maybe_redirect_menu(message, state):
        return
    await state.update_data(material_type=message.text.strip())
    ctx = get_app_context()
    questions = ctx.text_library.picker_questions()
    options = ctx.text_library.picker_options().get("usage_class", [])
    await state.set_state(PickerWizard.usage_class)
    await message.answer(
        questions.get("usage_class", "Какой класс эксплуатации требуется (бытовой/коммерческий)?")
    )
    if options:
        await message.answer("\n".join(options))


@router.message(PickerWizard.usage_class)
async def handle_usage_class(message: Message, state: FSMContext) -> None:
    if await _maybe_redirect_menu(message, state):
        return
    await state.update_data(usage_class=message.text.strip())
    ctx = get_app_context()
    questions = ctx.text_library.picker_questions()
    options = ctx.text_library.picker_options().get("design_preferences", [])
    await state.set_state(PickerWizard.design_preferences)
    await message.answer(questions.get("design_preferences", "Есть пожелания по цвету или рисунку?"))
    if options:
        await message.answer("\n".join(options))


@router.message(PickerWizard.design_preferences)
async def handle_design_preferences(message: Message, state: FSMContext) -> None:
    if await _maybe_redirect_menu(message, state):
        return
    await state.update_data(design_preferences=message.text.strip())
    ctx = get_app_context()
    questions = ctx.text_library.picker_questions()
    await state.set_state(PickerWizard.metrics)
    await message.answer(
        questions.get(
            "metrics",
            "Введите площадь и запас на прирезку (например: 120 8).",
        )
    )


@router.message(PickerWizard.metrics)
async def handle_metrics(message: Message, state: FSMContext) -> None:
    if await _maybe_redirect_menu(message, state):
        return
    raw = (message.text or "").replace(",", ".").split()
    if not raw:
        await message.answer("Укажите площадь в квадратных метрах и запас, например: 120 8")
        return

    try:
        area = float(raw[0])
        waste = int(raw[1]) if len(raw) > 1 else 5
    except ValueError:
        await message.answer("Не удалось распознать числа. Пример: 150 7")
        return

    await state.update_data(area_m2=area, waste_pct=waste)
    ctx = get_app_context()
    questions = ctx.text_library.picker_questions()
    await state.set_state(PickerWizard.budget)
    await message.answer(
        questions.get("budget", "Какой ориентировочный бюджет на м² (например 1200)?")
    )


@router.message(PickerWizard.budget)
async def handle_budget(message: Message, state: FSMContext) -> None:
    if await _maybe_redirect_menu(message, state):
        return
    budget_value = None
    budget_text = (message.text or "").strip().replace(" ", "")
    if budget_text:
        try:
            budget_value = float(budget_text.replace(",", "."))
        except ValueError:
            await message.answer("Пример бюджета: 1250")
            return

    await state.update_data(budget=budget_value)
    state_data = await state.get_data()
    await state.clear()
    await _provide_recommendations(message, state_data)


async def _provide_recommendations(message: Message, answers: dict[str, Any]) -> None:
    ctx = get_app_context()
    category = answers.get("material_type") or "Ковровая плитка"
    filters: dict[str, Any] = {}
    area = float(answers.get("area_m2", 0) or 0)
    waste = int(answers.get("waste_pct", 0) or 0)
    budget = answers.get("budget")

    application_area = answers.get("application_area")
    if application_area:
        filters["Область применения"] = application_area

    usage_class = answers.get("usage_class")
    if usage_class:
        filters["Класс"] = usage_class

    design_pref = answers.get("design_preferences")
    if design_pref:
        filters["Цвет"] = design_pref

    products = ctx.inventory.search(category, filters)
    if budget:
        products = [
            product
            for product in products
            if ctx.pricing.price(product.sku) is None or ctx.pricing.price(product.sku) <= budget
        ]

    if not products:
        await message.answer(
            "Не нашёл подходящих позиций. Попробуем ослабить ограничения или посмотреть каталог?"
        )
        return

    await message.answer(
        ctx.text_library.styles.get(
            "picker_summary_intro",
            "Нашёл варианты под вашу задачу. Сохранить в подборку и получить смету в Excel?",
        )
    )

    recommendations: dict[str, Any] = {}
    for product in products[:6]:
        total_required = calc_required(area, waste, product.pack_step_m2)
        price = ctx.pricing.price(product.sku)
        text = ctx.text_library.render_product_card(
            product, price=price, required_m2=total_required
        )
        await message.answer(text, reply_markup=product_actions_keyboard(product))
        recommendations[product.sku] = {
            "area_m2": area,
            "waste_pct": waste,
            "total_m2": total_required,
            "category": product.category,
            "name": product.name,
            "brand": product.brand,
            "pack_step": product.pack_step_m2,
        }

    user_id = message.from_user.id if message.from_user else 0
    if user_id:
        wizard_memory().remember(user_id, recommendations)
