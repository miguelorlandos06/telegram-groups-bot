import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from bot import config, db
from bot.handlers import setup_routers

logging.basicConfig(level=logging.INFO)


async def on_startup(bot: Bot):
    await db.init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(
        f"{config.WEBHOOK_URL}{config.WEBHOOK_PATH}",
        secret_token=config.WEBHOOK_SECRET,
        drop_pending_updates=True
    )
    logging.info("Webhook configurado")


async def on_shutdown(bot: Bot):
    await db.close_db()
    logging.info("Bot detenido")


def main():
    bot = Bot(config.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(setup_routers())
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    handler = SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=config.WEBHOOK_SECRET)
    handler.register(app, path=config.WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host="0.0.0.0", port=config.PORT)


if __name__ == "__main__":
    main()
