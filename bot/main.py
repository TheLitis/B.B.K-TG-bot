"""Entry point for the Lgpol flooring assistant bot."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from .config import Settings, get_settings
from .context import AppContext, set_app_context
from .handlers import (
    cart_like_selection,
    catalog_browse,
    delivery_payment,
    partners,
    start,
    support_feedback,
    wizard_picker,
)
from .middlewares.rate_limit import RateLimitMiddleware
from .services.inventory_stub import InventoryStub
from .services.pricing_stub import PricingStub
from .services.selection_store import SelectionStore
from .services.text_templates import get_text_library

logger = logging.getLogger(__name__)


async def start_bot(settings: Settings) -> None:
    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.message.middleware(RateLimitMiddleware(interval=0.6))
    dp.callback_query.middleware(RateLimitMiddleware(interval=0.4))

    text_library = get_text_library(settings.data_dir)
    inventory = InventoryStub(settings.data_dir / "catalog.json")
    pricing = PricingStub()
    selection_store = SelectionStore(settings.tmp_dir, autosave=settings.autosave_selection)

    set_app_context(
        AppContext(
            text_library=text_library,
            inventory=inventory,
            pricing=pricing,
            selection_store=selection_store,
            settings=settings,
        )
    )

    dp.include_router(start.router)
    dp.include_router(wizard_picker.router)
    dp.include_router(catalog_browse.router)
    dp.include_router(cart_like_selection.router)
    dp.include_router(delivery_payment.router)
    dp.include_router(partners.router)
    dp.include_router(support_feedback.router)

    if settings.use_webhook and settings.webhook_url:
        logger.info("Starting bot in webhook mode")
        await bot.set_webhook(url=settings.webhook_url, drop_pending_updates=True)
        await dp.start_webhook(
            bot=bot,
            webhook_path="/",
            host=settings.webapp_host or "0.0.0.0",
            port=settings.webapp_port or 8080,
        )
    else:
        logger.info("Starting bot in long-polling mode")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def init_event_loop() -> None:
    with suppress(ImportError):
        import uvloop

        uvloop.install()


async def main() -> None:
    configure_logging()
    init_event_loop()
    settings = get_settings()
    await start_bot(settings)


if __name__ == "__main__":
    asyncio.run(main())
