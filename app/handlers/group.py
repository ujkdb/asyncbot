from aiogram import F, Bot, types, Router
from aiogram.filters import Command

from app.filters import ChatTypeFilter


group_router = Router()
group_router.message.filter(ChatTypeFilter(["group", "supergroup"]))


@group_router.message(Command("admin"))
async def get_admins(message: types.Message, bot: Bot):
    chat_id = message.chat.id
    print("_______________________________")
    print(chat_id)
    admins_list = await bot.get_chat_administrators(chat_id)
    print(admins_list)
    admins_list = [
        member.user.id
        for member in admins_list
        if member.status == "creator" or member.status == "administrator"
    ]
    bot.my_admins_list = admins_list
    if message.from_user.id in admins_list:
        await message.delete()
