from datetime import datetime

from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InputMediaPhoto

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import requests as rq
from app.filters import ChatTypeFilter, IsAdmin
from app.utils.paginator import Paginator
from app.handlers.menu_processing import pages
from app import common as cm
from app import keyboards as kb

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


class AddItem(StatesGroup):
    name = State()
    description = State()
    price = State()
    image = State()
    category = State()

    item_for_change = None

    texts = {
        "AddItem:name": "Введите название заново:",
        "AddItem:description": "Введите описание заново:",
        "AddItem:price": "Введите стоимость заново:",
        "AddItem:image": "Отправьте изображение заново:",
    }


class AddBanner(StatesGroup):
    description = State()
    image = State()

    banner_for_change = None


class AddPromocode(StatesGroup):
    name = State()
    discount = State()
    duration = State()


@admin_router.message(Command("admin"))
async def admin_main(message: types.Message):
    await message.answer_photo(
        photo=cm.IMAGE,
        caption="Что хотите сделать?", reply_markup=kb.admin_main)


@admin_router.callback_query(StateFilter(None), F.data == "admin_catalog")
async def admin_catalog(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()

    media = InputMediaPhoto(
        media=cm.IMAGE,
        caption=f"Выберите категорию товаров:")
    await callback.message.edit_media(media=media, reply_markup=await kb.categories(session, admin_back="admin_cancel"))


@admin_router.callback_query(StateFilter(None), F.data.startswith("category_"))
async def admin_items(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    split_cb = callback.data.split("_")
    page = int(split_cb[1])
    category_id = int(split_cb[-1])
    items = await rq.orm_get_items(session, category_id=category_id)

    paginator = Paginator(items, page=page)
    item = paginator.get_page()[0]

    media = InputMediaPhoto(
        media=item.image,
        caption=f"<strong>{item.name}</strong>\n"
                f"{item.description}\nСтоимость: {round(item.price, 2)}\n"
                f"<strong>Товар {paginator.page} из {paginator.pages}</strong>",
    )
    pagination_btns = pages(paginator)

    keyboard = await kb.admin_items_btns(pagination_btns, page, category_id, item.id)

    await callback.message.edit_media(media=media, reply_markup=keyboard)


@admin_router.callback_query(StateFilter(None), F.data == "admin_add")
async def admin_add(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.message.photo:
        await callback.message.edit_caption(
            caption="Введите название товара:", reply_markup=kb.admin_back_cancel
        )
    else:
        await callback.message.edit_text(
            text="Введите название товара:", reply_markup=kb.admin_back_cancel
        )
    await state.set_state(AddItem.name)

@admin_router.callback_query(StateFilter(None), F.data.startswith("admin_banner_"))
async def admin_banner(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()

    page = int(callback.data.split("_")[-1])
    banners = await rq.orm_get_banners(session)

    paginator = Paginator(banners, page=page)
    banner = paginator.get_page()[0]

    media = InputMediaPhoto(
        media=banner.image,
        caption=f"<strong>Название: {banner.name}\n\nОписание:\n</strong>"
                f"{banner.description}\n\n"
                f"<strong>Баннер {paginator.page} из {paginator.pages}</strong>",
    )
    pagination_btns = pages(paginator)

    keyboard = await kb.admin_banners_btns(pagination_btns, page, banner.id)

    await callback.message.edit_media(media=media, reply_markup=keyboard)


@admin_router.callback_query(StateFilter(None), F.data.startswith("admin_change_banner_"))
async def admin_change_banner(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    banner_id = int(callback.data.split("_")[-1])

    banner_for_change = await rq.orm_get_banner_id(session, banner_id)
    print(banner_for_change.id, banner_for_change.name, banner_for_change.description)

    AddBanner.banner_for_change = banner_for_change

    await callback.answer()
    await callback.message.edit_caption(caption="Введите новое описание\nИли точку чтобы оставить прежнее значение",
                                        reply_markup=kb.admin_cancel)

    await state.set_state(AddBanner.description)


@admin_router.message(AddBanner.description, or_f(F.text, F.text == "."))
async def add_banner_description(message: types.Message, state: FSMContext):
    if message.text == "." and AddBanner.banner_for_change:
        await state.update_data(description=AddBanner.banner_for_change.description)
    else:
        await state.update_data(description=message.text)
    await message.answer("Отправьте изображение баннера:", reply_markup=kb.admin_cancel)
    await state.set_state(AddBanner.image)


@admin_router.message(AddBanner.description)
async def add_banner_description2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите текст описания баннера:",
                         reply_markup=kb.admin_cancel)


@admin_router.message(AddBanner.image, or_f(F.photo, F.text == "."))
async def add_banner_image(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text == "." and AddBanner.banner_for_change:
        await state.update_data(image=AddBanner.banner_for_change.image)
    else:
        await state.update_data(image=message.photo[-1].file_id)
    data = await state.get_data()
    print(data["description"])
    print(AddBanner.banner_for_change.id)
    try:
        await rq.orm_update_banner(session, AddBanner.banner_for_change.id, data)
        await message.answer(f"Баннер {AddBanner.banner_for_change.name} изменен:\n"
                                f"description: {AddBanner.banner_for_change.description} -> {data['description']}\n",
                                reply_markup=kb.admin_main)
    except Exception as ex:
        await message.answer(
            f"Ошибка:\n{str(ex)}\nОбратись к программеру",
            reply_markup=kb.admin_main,
        )

    await state.clear()


@admin_router.message(AddBanner.image)
async def add_banner_image2(message: types.Message, state: FSMContext):
    await message.answer("Корректно отправьте фото:", reply_markup=kb.admin_cancel)


@admin_router.message(AddBanner.image)
async def change_banner_image2(message: types.Message, state: FSMContext):
    await message.answer("Корректно отправьте фото баннера", reply_markup=kb.admin_cancel)


@admin_router.callback_query(StateFilter(None), F.data.startswith("admin_change_"))
async def admin_change(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    item_id = callback.data.split("_")[-1]

    item_for_change = await rq.orm_get_item(session, int(item_id))

    AddItem.item_for_change = item_for_change

    await callback.answer()
    media = InputMediaPhoto(
        media=cm.IMAGE,
        caption=f"Введите название товара\nИли точку, чтобы оставить прежнее значение")
    await callback.message.edit_media(media=media, reply_markup=kb.admin_back_cancel)

    await state.set_state(AddItem.name)


@admin_router.callback_query(F.data.startswith("admin_delete_"))
async def admin_delete(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    await callback.message.delete()
    item_id = callback.data.split("_")[-1]
    deleted_item = await rq.orm_get_item(session, int(item_id))
    await rq.orm_delete_item(session, int(item_id))

    await callback.message.answer(f"Товар удален!\n"
                                  f"id: {deleted_item.id}\n"
                                  f"name: {deleted_item.name}\n"
                                  f"description: {deleted_item.description}\n"
                                  f"price: {deleted_item.price}\n"
                                  f"category: {deleted_item.category.name}\n",
                                  reply_markup=kb.admin_main)


@admin_router.callback_query(StateFilter(None), F.data == "admin_cancel")
async def admin_cancel(callback: types.CallbackQuery) -> None:
    media = InputMediaPhoto(
        media=cm.IMAGE,
        caption=f"Что хотите сделать?")

    await callback.message.edit_media(media=media, reply_markup=kb.admin_main)


@admin_router.callback_query(StateFilter('*'), F.data == "admin_cancel")
async def admin_cancel2(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    current_state = await state.get_state()
    if current_state is None:
        return

    media = InputMediaPhoto(
        media=cm.IMAGE,
        caption=f"Действия отменены\n\nЧто хотите сделать?")
    await callback.message.edit_media(media=media, reply_markup=kb.admin_main)
    await state.clear()


@admin_router.callback_query(StateFilter('*'), F.data == "admin_back")
async def admin_back(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    current_state = await state.get_state()
    if current_state == AddItem.name:
        ct = "Предыдущего шага нет.\nВведите название товара или отмените добавление"
        if callback.message.photo and callback.message.caption != ct:
            await callback.message.edit_caption(caption=ct, reply_markup=kb.admin_back_cancel)
            return
        elif callback.message.photo and callback.message.caption == ct:
            return
        elif callback.message.text != ct and not callback.message.photo:
            await callback.message.edit_text(text=ct, reply_markup=kb.admin_back_cancel)
            return
        elif callback.message.text == ct and not callback.message.photo:
            return

    previous = None
    for step in AddItem.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await callback.message.edit_text(f"Вы вернулись к прошлому шагу\n{AddItem.texts[previous.state]}",
                                          reply_markup=kb.admin_back_cancel)
            return
        previous = step


@admin_router.message(AddItem.name, or_f(F.text, F.text == "."))
async def add_name(message: types.Message, state: FSMContext):
    if message.text == "." and AddItem.item_for_change:
        await state.update_data(name=AddItem.item_for_change.name)
    else:
        await state.update_data(name=message.text)
    await message.answer("Введите описание товара:", reply_markup=kb.admin_back_cancel)
    await state.set_state(AddItem.description)


@admin_router.message(AddItem.name)
async def add_name2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите текст названия товара:",
                         reply_markup=kb.admin_back_cancel)


@admin_router.message(AddItem.description, or_f(F.text, F.text == "."))
async def add_description(message: types.Message, state: FSMContext):
    if message.text == "." and AddItem.item_for_change:
        await state.update_data(description=AddItem.item_for_change.description)
    else:
        await state.update_data(description=message.text)
    await message.answer("Введите стоимость товара:", reply_markup=kb.admin_back_cancel)
    await state.set_state(AddItem.price)


@admin_router.message(AddItem.description)
async def add_description2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите текст описания товара:",
                         reply_markup=kb.admin_back_cancel)


@admin_router.message(AddItem.price, or_f(F.text, F.text == "."))
async def add_price(message: types.Message, state: FSMContext):
    if message.text == "." and AddItem.item_for_change:
        await state.update_data(price=AddItem.item_for_change.price)
    else:
        try:
            float(message.text)
        except ValueError:
            await message.answer("Введите корректное значение цены:",
                                 reply_markup=kb.admin_back_cancel)
            return
        await state.update_data(price=message.text)
    await message.answer("Загрузите изображение товара:",
                         reply_markup=kb.admin_back_cancel)
    await state.set_state(AddItem.image)


@admin_router.message(AddItem.price)
async def add_price2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, введите стоимость товара:",
                         reply_markup=kb.admin_back_cancel)


@admin_router.message(AddItem.image, or_f(F.photo, F.text == "."))
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text == "." and AddItem.item_for_change:
        await state.update_data(image=AddItem.item_for_change.image)
    else:
        await state.update_data(image=message.photo[-1].file_id)
    await message.answer("Выберите категорию товара:", reply_markup=await kb.categories(session=session))
    await state.set_state(AddItem.category)


@admin_router.message(AddItem.image)
async def add_image2(message: types.Message, state: FSMContext):
    await message.answer("Корректно отправьте фото:", reply_markup=kb.admin_back_cancel)


@admin_router.callback_query(AddItem.category)
async def add_category(callback: types.CallbackQuery, state: FSMContext , session: AsyncSession):
    if int(callback.data.split("_")[-1]) in [category.id for category in await rq.orm_get_categories(session)]:
        await callback.answer()
        await state.update_data(category=int(callback.data.split("_")[-1]))
    else:
        await callback.message.answer('Выберите катеорию из кнопок:',
                                      reply_markup=await kb.categories(session=session))
        await callback.answer()
    data = await state.get_data()
    try:
        if AddItem.item_for_change:
            prev_cat_name = await rq.orm_get_category(session, AddItem.item_for_change.category_id)
            cur_cat_name = await rq.orm_get_category(session, data["category"])
            await rq.orm_update_item(session, AddItem.item_for_change.id, data)
            await callback.message.edit_text(f"Товар изменен:\n"
                                        f"name: {AddItem.item_for_change.name} -> {data['name']}\n"
                                        f"description: {AddItem.item_for_change.description} -> {data['description']}\n"
                                        f"price: {AddItem.item_for_change.price} -> {data['price']}\n"
                                        f"category: {prev_cat_name.name} -> {cur_cat_name.name}",
                                        reply_markup=kb.admin_main)
        else:
            await rq.orm_add_item(session, data)
            await callback.message.edit_text("Товар добавлен", reply_markup=kb.admin_main)
    except Exception as ex:
        await callback.message.edit_text(
            f"Ошибка:\n{str(ex)}\nОбратись к программеру",
            reply_markup=kb.admin_main,
        )

    await state.clear()

@admin_router.message(AddItem.category)
async def add_category2(message: types.Message, state: FSMContext, session: AsyncSession):
    await message.answer('Выберите катеорию из кнопок:',
                                reply_markup=await kb.categories(session=session))


@admin_router.callback_query(StateFilter(None), F.data == "admin_add_promocode")
async def admin_add_promocode_name(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_caption(
        caption="Введите собственно промокод:", reply_markup=kb.admin_back_cancel
    )
    await state.set_state(AddPromocode.name)


@admin_router.message(AddPromocode.name, F.text)
async def admin_add_promocode_discount(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer('Введите скидку:\nДля ввода процентной скидки используйте "0." (0.53 == 53%).\n'
                         'Для рублёвой введите число больше нуля.',
                         reply_markup=kb.admin_back_cancel)
    await state.set_state(AddPromocode.discount)


@admin_router.message(AddPromocode.discount, F.text)
async def admin_add_promocode_duration(message: types.Message, state: FSMContext):
    await state.update_data(discount=message.text)
    await message.answer('Введите дату в формате "дд.мм.гггг", до которой будет действителен промокод:',
                         reply_markup=kb.admin_back_cancel)
    await state.set_state(AddPromocode.duration)


@admin_router.message(AddPromocode.duration, F.text)
async def admin_add_promocode_duration(message: types.Message, state: FSMContext):
    await state.update_data(duration=message.text)
    data = await state.get_data()
    await message.answer(f'{data}',
                         reply_markup=kb.admin_back_cancel)
    await state.clear()
