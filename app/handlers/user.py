from aiogram import F, Router, Bot
from aiogram.filters import CommandStart, Command, or_f, StateFilter
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from app import keyboards as kb
from app import common as cm
from app.database import requests as rq
from app.handlers import menu_processing as mp
from app.filters import ChatTypeFilter
from app.common import IMAGE


user_router = Router()
user_router.message.filter(ChatTypeFilter(["private"]))


@user_router.message(or_f(CommandStart(), Command('menu')))
async def cmd_start(message: Message, session: AsyncSession):
    media, reply_markup = await mp.get_menu_content(session, level=0, menu_name="main")
    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)


async def add_to_cart(callback: CallbackQuery, callback_data: kb.MenuCallBack, session: AsyncSession):
    user = callback.from_user
    await rq.orm_add_user(
        session,
        user_id=user.id,
        name=user.full_name,
        promocode=None
    )
    await rq.orm_add_cart(session, user_id=user.id, item_id=callback_data.item_id)
    await callback.answer("Товар добавлен в корзину")


@user_router.callback_query(kb.MenuCallBack.filter())
async def user_menu(callback: CallbackQuery, callback_data: kb.MenuCallBack, session: AsyncSession, state: FSMContext):

    if callback_data.menu_name == "add_to_cart":
        await add_to_cart(callback, callback_data, session)
        return

    media, reply_markup = await mp.get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        page=callback_data.page,
        state=state,
        item_id=callback_data.item_id,
        user_id=callback.from_user.id,
    )

    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()


@user_router.message(mp.Order.name, F.text)
async def order_phone(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(mp.Order.phone)
    await message.answer("Введите номер телефона:", reply_markup=await kb.get_order_btns(state=state))


@user_router.message(mp.Order.phone, F.text)
async def order_address(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(mp.Order.address)
    await message.answer("Введите Адрес пункта СДЭК:", reply_markup=await kb.get_order_btns(state=state))


@user_router.message(mp.Order.address, F.text)
async def order_address(message: Message, state: FSMContext, bot: Bot, session: AsyncSession):
    await state.update_data(address=message.text)
    data = await state.get_data()
    await message.answer_photo(photo=IMAGE, caption="Ваш заказ офоролен\nОтправление через 1-2 дня.",
                         reply_markup=await kb.get_user_main_btns(level=1))

    carts = await rq.orm_get_carts(session, message.from_user.id)

    await bot.send_message(chat_id=-1002382524724, text=f"Покупатель: @{message.from_user.username}\nФИО: {data['name']}\n"
                                                        f"Номер: {data['phone']}\nАдрес: {data['address']}\n"
                                                        f"Товар:\n{"\n".join([cart.quantity * (cart.item.name + "\n") for cart in carts if cart.quantity > 1])}"
                                                        f"{"\n".join([cart.item.name for cart in carts if cart.quantity == 1])}")

    await rq.orm_delete_carts(session, message.from_user.id)
    await rq.orm_change_user_promocode(session, message.from_user.id)
    await state.clear()


@user_router.callback_query(mp.Order.phone)
async def order_back_to_name(callback: CallbackQuery, state: FSMContext):
    await state.set_state(mp.Order.name)

    await callback.message.edit_text(text="Введите ФИО:", reply_markup=await kb.get_order_btns(state=state))


@user_router.callback_query(mp.Order.address)
async def order_back_to_phone(callback: CallbackQuery, state: FSMContext):
    await state.set_state(mp.Order.phone)

    await callback.message.edit_text(text="Введите номер телефона:", reply_markup=await kb.get_order_btns(state=state))


@user_router.message(mp.Promocode.promocode, F.text)
async def promocode(message: Message, state: FSMContext, session: AsyncSession):
    promocode = await rq.orm_get_promocode(session=session, name=message.text)
    if promocode:
        await rq.orm_change_user_promocode(session=session, user_id=message.from_user.id, promocode=promocode.id)
        await message.answer_photo(photo=IMAGE, caption="Промокод активирован",
                                   reply_markup=await kb.get_user_main_btns(level=1))
    else:
        await message.answer_photo(photo=IMAGE, caption="Такого промокода не существует или он более не действителен.",
                                   reply_markup=await kb.get_user_main_btns(level=0))

    await state.clear()
