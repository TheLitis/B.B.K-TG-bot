"""Finite state machine definitions for conversational flows."""

from aiogram.fsm.state import State, StatesGroup


class PickerWizard(StatesGroup):
    """Master wizard flow for flooring selection."""

    application_area = State()
    material_type = State()
    usage_class = State()
    design_preferences = State()
    metrics = State()
    budget = State()


class SamplesForm(StatesGroup):
    """Form for requesting physical samples."""

    full_name = State()
    company = State()
    phone = State()
    email = State()
    address = State()
    comment = State()
    consent = State()
    confirmation = State()


class ManagerCallForm(StatesGroup):
    """Form collecting callback requests for a manager."""

    phone = State()
    preferred_time = State()
    consent = State()
    confirmation = State()


class ManagerQuestionForm(StatesGroup):
    """Form capturing a free-form question for the team."""

    question = State()
    contact = State()
    consent = State()
    confirmation = State()


class SelectionMetrics(StatesGroup):
    """Auxiliary state for collecting metrics before adding to selection."""

    sku = State()
