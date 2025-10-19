"""Handlers covering samples, manager contacts, and FAQ."""

from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ..context import get_app_context
from ..filters import menu_choice
from ..keyboards.common import consent_keyboard
from ..states import ManagerCallForm, ManagerQuestionForm, SamplesForm

router = Router(name="support")


def samples_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Отправить менеджеру", callback_data="samples:confirm:yes"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отменить", callback_data="samples:confirm:no"
                )
            ],
        ]
    )


def manager_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Перезвоните мне", callback_data="manager:callback"),
            ],
            [
                InlineKeyboardButton(text="Задать вопрос", callback_data="manager:question"),
            ],
            [
                InlineKeyboardButton(
                    text="Оставить отзыв/рекламацию",
                    callback_data="manager:complaint",
                ),
            ],
        ]
    )


@router.message(menu_choice("samples"))
async def samples_start(message: Message, state: FSMContext) -> None:
    ctx = get_app_context()
    prompts = ctx.text_library.styles.get(
        "samples_prompts",
        {
            "full_name": "Как вас зовут?",
            "company": "Компания или проект (если есть).",
        },
    )
    await state.set_state(SamplesForm.full_name)
    await state.update_data(samples_prompts=prompts)
    await message.answer(prompt_text(prompts, "full_name"))


@router.message(SamplesForm.full_name)
async def samples_full_name(message: Message, state: FSMContext) -> None:
    await state.update_data(full_name=message.text.strip())
    data = await state.get_data()
    await state.set_state(SamplesForm.company)
    await message.answer(prompt_text(data["samples_prompts"], "company"))


@router.message(SamplesForm.company)
async def samples_company(message: Message, state: FSMContext) -> None:
    await state.update_data(company=message.text.strip())
    await state.set_state(SamplesForm.phone)
    await message.answer("Телефон для связи:")


@router.message(SamplesForm.phone)
async def samples_phone(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.text.strip())
    await state.set_state(SamplesForm.email)
    await message.answer("Email:")


@router.message(SamplesForm.email)
async def samples_email(message: Message, state: FSMContext) -> None:
    await state.update_data(email=message.text.strip())
    await state.set_state(SamplesForm.address)
    await message.answer("Куда отправить образцы (адрес):")


@router.message(SamplesForm.address)
async def samples_address(message: Message, state: FSMContext) -> None:
    await state.update_data(address=message.text.strip())
    await state.set_state(SamplesForm.comment)
    await message.answer("Комментарий или требуемые позиции (можно оставить пустым):")


@router.message(SamplesForm.comment)
async def samples_comment(message: Message, state: FSMContext) -> None:
    await state.update_data(comment=message.text.strip())
    await state.set_state(SamplesForm.consent)
    ctx = get_app_context()
    await message.answer(ctx.text_library.consent_text(), reply_markup=consent_keyboard())


@router.callback_query(SamplesForm.consent, F.data == "consent_yes")
async def samples_consent_yes(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(SamplesForm.confirmation)
    data = await state.get_data()
    await callback.message.answer(
        build_samples_summary(callback.message.from_user.id if callback.message else 0, data),
        reply_markup=samples_confirm_keyboard(),
    )


@router.callback_query(SamplesForm.consent, F.data == "consent_no")
async def samples_consent_no(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Заявка отменена.")
    await state.clear()


@router.callback_query(SamplesForm.confirmation, F.data == "samples:confirm:yes")
async def samples_confirm_yes(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    data = await state.get_data()
    await state.clear()

    user = callback.from_user
    user_id = user.id if user else 0
    selection_items = ctx.selection_store.to_lines(user_id) if user_id else []

    customer = {
        "Имя": data.get("full_name"),
        "Компания": data.get("company"),
        "Телефон": data.get("phone"),
        "Email": data.get("email"),
        "Адрес": data.get("address"),
        "Комментарий": data.get("comment"),
    }

    from ..services.export import selection_to_workbook

    payload = selection_to_workbook(selection_items, customer=customer, company=ctx.text_library.company)
    document = BufferedInputFile(payload.getvalue(), filename="lgpol_samples.xlsx")

    manager_chat = ctx.settings.manager_chat_id
    await callback.bot.send_message(
        manager_chat,
        f"Запрос образцов от {customer['Имя']} ({customer['Телефон']}).",
    )
    await callback.bot.send_document(manager_chat, document)
    await callback.answer("Заявка отправлена.")
    await callback.message.answer("Заявка отправлена менеджеру. Мы свяжемся с вами.")


@router.callback_query(SamplesForm.confirmation, F.data == "samples:confirm:no")
async def samples_confirm_no(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Заявка отменена.")
    await state.clear()


@router.message(menu_choice("manager"))
async def manager_menu(message: Message) -> None:
    ctx = get_app_context()
    prompt = ctx.text_library.styles.get(
        "manager_intro",
        "Выберите вариант связи с менеджером:",
    )
    await message.answer(prompt, reply_markup=manager_menu_keyboard())


@router.message(menu_choice("contacts"))
async def contacts(message: Message) -> None:
    ctx = get_app_context()
    company = ctx.text_library.company
    text = "\n".join(
        [
            f"{company.get('brand', 'Lgpol / В.В.К.')}",
            f"Телефон: {company.get('phone', '')}",
            f"Email: {company.get('email', '')}",
            f"Адрес: {company.get('address', '')}",
            f"График: {company.get('hours', '')}",
            f"Сайт: {company.get('site', '')}",
        ]
    )
    maps_url = ctx.text_library.styles.get(
        "maps_url",
        "https://yandex.ru/maps/",
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Построить маршрут",
                    url=maps_url,
                )
            ]
        ]
    )
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "manager:callback")
async def manager_callback_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ManagerCallForm.phone)
    await callback.message.answer("Укажите номер телефона для обратного звонка:")


@router.message(ManagerCallForm.phone)
async def manager_callback_phone(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.text.strip())
    await state.set_state(ManagerCallForm.preferred_time)
    await message.answer("Когда удобно позвонить?")


@router.message(ManagerCallForm.preferred_time)
async def manager_callback_time(message: Message, state: FSMContext) -> None:
    await state.update_data(preferred_time=message.text.strip())
    await state.set_state(ManagerCallForm.consent)
    ctx = get_app_context()
    await message.answer(ctx.text_library.consent_text(), reply_markup=consent_keyboard())


@router.callback_query(ManagerCallForm.consent, F.data == "consent_yes")
async def manager_callback_consent_yes(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ManagerCallForm.confirmation)
    data = await state.get_data()
    summary = (
        f"Перезвонить: {data.get('phone')}\n"
        f"Время: {data.get('preferred_time')}"
    )
    await callback.message.answer(summary, reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Отправить менеджеру",
                    callback_data="manager:callback:confirm",
                )
            ],
            [
                InlineKeyboardButton(text="Отменить", callback_data="manager:callback:cancel")
            ],
        ]
    ))


@router.callback_query(ManagerCallForm.consent, F.data == "consent_no")
async def manager_callback_consent_no(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Запрос отменён.")
    await state.clear()


@router.callback_query(ManagerCallForm.confirmation, F.data == "manager:callback:confirm")
async def manager_callback_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    data = await state.get_data()
    await state.clear()
    user = callback.from_user
    await callback.bot.send_message(
        ctx.settings.manager_chat_id,
        f"Запрос перезвонить от {user.full_name if user else 'клиента'} "
        f"({user.id if user else ''}).\n"
        f"Телефон: {data.get('phone')}\n"
        f"Время: {data.get('preferred_time')}",
    )
    await callback.answer("Передали менеджеру.")
    await callback.message.answer("Передал запрос перезвонить.")


@router.callback_query(ManagerCallForm.confirmation, F.data == "manager:callback:cancel")
async def manager_callback_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Отменено.")
    await state.clear()


@router.callback_query(F.data.in_(("manager:question", "manager:logistics", "manager:complaint")))
async def manager_question_start(callback: CallbackQuery, state: FSMContext) -> None:
    subject_map = {
        "manager:question": "Введите ваш вопрос:",
        "manager:logistics": "Опишите задачу по доставке/логистике:",
        "manager:complaint": "Оставьте отзыв или рекламацию:",
    }
    await callback.answer()
    await state.update_data(context=callback.data)
    await state.set_state(ManagerQuestionForm.question)
    await callback.message.answer(subject_map.get(callback.data, "Введите сообщение:"))


@router.message(ManagerQuestionForm.question)
async def manager_question_collect_question(message: Message, state: FSMContext) -> None:
    await state.update_data(question=message.text.strip())
    await state.set_state(ManagerQuestionForm.contact)
    await message.answer("Как с вами связаться? (телефон/email)")


@router.message(ManagerQuestionForm.contact)
async def manager_question_collect_contact(message: Message, state: FSMContext) -> None:
    await state.update_data(contact=message.text.strip())
    await state.set_state(ManagerQuestionForm.consent)
    ctx = get_app_context()
    await message.answer(ctx.text_library.consent_text(), reply_markup=consent_keyboard())


@router.callback_query(ManagerQuestionForm.consent, F.data == "consent_yes")
async def manager_question_consent_yes(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ManagerQuestionForm.confirmation)
    data = await state.get_data()
    summary = (
        f"Сообщение: {data.get('question')}\n"
        f"Контакты: {data.get('contact')}"
    )
    await callback.message.answer(
        summary,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Отправить менеджеру",
                        callback_data="manager:question:confirm",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Отменить",
                        callback_data="manager:question:cancel",
                    )
                ],
            ]
        ),
    )


@router.callback_query(ManagerQuestionForm.consent, F.data == "consent_no")
async def manager_question_consent_no(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Запрос отменён.")
    await state.clear()


@router.callback_query(ManagerQuestionForm.confirmation, F.data == "manager:question:confirm")
async def manager_question_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    ctx = get_app_context()
    data = await state.get_data()
    await state.clear()
    user = callback.from_user
    await callback.bot.send_message(
        ctx.settings.manager_chat_id,
        f"Сообщение от {user.full_name if user else 'клиента'} ({user.id if user else ''}).\n"
        f"Контакты: {data.get('contact')}\n"
        f"Тема: {data.get('question')}",
    )
    await callback.answer("Сообщение отправлено.")
    await callback.message.answer("Передал менеджеру. Скоро свяжемся.")


@router.callback_query(ManagerQuestionForm.confirmation, F.data == "manager:question:cancel")
async def manager_question_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Отменено.")
    await state.clear()


def prompt_text(prompts: dict[str, str], key: str) -> str:
    return prompts.get(key, "")


def build_samples_summary(user_id: int, data: dict[str, Any]) -> str:
    ctx = get_app_context()
    items = ctx.selection_store.list(user_id) if user_id else []
    lines = [
        "Проверим данные заявки:",
        f"Имя: {data.get('full_name')}",
        f"Компания: {data.get('company')}",
        f"Телефон: {data.get('phone')}",
        f"Email: {data.get('email')}",
        f"Адрес: {data.get('address')}",
        f"Комментарий: {data.get('comment')}",
    ]
    if items:
        lines.append("Подборка:")
        for entry in items:
            lines.append(
                f"- {entry.name} ({entry.sku}) — {entry.total_m2:.1f} м²"
            )
    else:
        lines.append("Подборка пока пустая — добавьте позиции или уточните в комментарии.")
    return "\n".join(lines)
