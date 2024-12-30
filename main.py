import asyncio
import logging
import os
from email.policy import default

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

from app.middlewares.db import DataBaseSession

from app.database.engine import drop_db, create_db, async_session
from app.handlers.user import user_router
from app.handlers.admin import admin_router
from app.handlers.group import group_router
from app.common import ALLOWED_UPDATES

bot = Bot(token=os.getenv("TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
bot.my_admins_list = []

dp = Dispatcher()


async def on_startup():

    # await drop_db()

    await create_db()


async def main():
    dp.startup.register(on_startup)
    dp.update.middleware(DataBaseSession(session_pool=async_session))
    dp.include_routers(user_router, admin_router, group_router)
    # await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
