from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import requests as rq


class MenuCallBack(CallbackData, prefix="menu"):
    level: int
    menu_name: str
    category: int | None = None
    page: int = 1
    item_id: int | None = None


inline_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Каталог", callback_data="catalog"), InlineKeyboardButton(text="Информация",
                                                                        url="https://telegra.ph/Informaciya-11-12-10")],
    [InlineKeyboardButton(text="Надо чат с отзывами", callback_data="review"),
     InlineKeyboardButton(text="Тут на манагера надо ссылку", url="https://t.me/Topstoreamo_bot")],
    [InlineKeyboardButton(text="Ввести промо-код", callback_data="promo")]
])

admin_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Добавить товар", callback_data="admin_add"),
     InlineKeyboardButton(text="Ассортимент", callback_data="admin_catalog")],
    [InlineKeyboardButton(text="Добавить промокод", callback_data="admin_add_promocode"),
     InlineKeyboardButton(text="Изменить баннер", callback_data="admin_banner_1")],
])

admin_cancel = InlineKeyboardMarkup(inline_keyboard=[
     [InlineKeyboardButton(text="Отмена", callback_data="admin_cancel")]
])

admin_back_cancel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Назад", callback_data="admin_back"),
     InlineKeyboardButton(text="Отмена", callback_data="admin_cancel")]
])


async def admin_change_delete(item_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Изменить", callback_data=f"admin_change_{item_id}"))
    keyboard.add(InlineKeyboardButton(text="Удалить", callback_data=f"admin_delete_{item_id}"))
    return keyboard.adjust(2).as_markup()


async def admin_items_btns(pagination_btns, page, category_id, item_id):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text="Изменить", callback_data=f"admin_change_{item_id}"))
    keyboard.add(InlineKeyboardButton(text="Удалить", callback_data=f"admin_delete_{item_id}"))

    keyboard.adjust(2)

    row = []
    for text, menu_name in pagination_btns.items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                                              callback_data=f"category_{page + 1}_{category_id}"))

        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                                              callback_data=f"category_{page - 1}_{category_id}"))

    keyboard.row(*row)

    row = [InlineKeyboardButton(text="Назад", callback_data="admin_catalog"),
            InlineKeyboardButton(text="Отмена", callback_data="admin_cancel")]

    return keyboard.row(*row).as_markup()


async def admin_banners_btns(pagination_btns, page, banner_id):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text="Изменить", callback_data=f"admin_change_banner_{banner_id}"))

    keyboard.adjust(1)

    row = []
    for text, menu_name in pagination_btns.items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                                              callback_data=f"admin_banner_{page + 1}"))

        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                                              callback_data=f"admin_banner_{page - 1}"))

    keyboard.row(*row)

    row = [InlineKeyboardButton(text="Назад", callback_data="admin_cancel"),
            InlineKeyboardButton(text="Отмена", callback_data="admin_cancel")]

    return keyboard.row(*row).as_markup()


async def categories(session: AsyncSession, admin_back="admin_back"):
    all_categories = await rq.orm_get_categories(session=session)
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name, callback_data=f"category_1_{category.id}"))

    keyboard.adjust(2)

    row = [InlineKeyboardButton(text="Назад", callback_data=admin_back),
           InlineKeyboardButton(text="Отмена", callback_data="admin_cancel")]

    return keyboard.row(*row).as_markup()



async def get_user_main_btns(*, level: int, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    btns = {
        "Товары 🍕": "catalog",
        "Корзина 🛒": "cart",
        "О нас ℹ️": "about",
        "Оплата 💰": "payment",
        "Ввести промокод: ⛵": "promocode",
    }
    for text, menu_name in btns.items():
        if menu_name == 'catalog':
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=level + 1, menu_name=menu_name).pack()))
        elif menu_name == 'cart':
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=4, menu_name=menu_name).pack()))
        elif menu_name == 'promocode':
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=6, menu_name=menu_name).pack()))
        else:
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=level, menu_name=menu_name).pack()))

    return keyboard.adjust(*sizes).as_markup()


async def get_user_catalog_btns(*, level: int, categories: list, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for c in categories:
        keyboard.add(InlineKeyboardButton(text=c.name,
                                          callback_data=MenuCallBack(level=level + 1, menu_name=c.name,
                                                                     category=c.id).pack()))

    keyboard.adjust(*sizes)

    row = [InlineKeyboardButton(text='Корзина 🛒',
                                callback_data=MenuCallBack(level=4, menu_name='cart').pack()),
           InlineKeyboardButton(text='Меню',
                                callback_data=MenuCallBack(level=level - 1, menu_name='main').pack())]

    return keyboard.row(*row).as_markup()


"""async def get_items_btns(
        *,
        level: int,
        category: int,
        page: int,
        pagination_btns: dict,
        item_id: int,
        sizes: tuple[int] = (2, 1)
):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='Назад',
                                      callback_data=MenuCallBack(level=level - 1, menu_name='catalog').pack()))
    keyboard.add(InlineKeyboardButton(text='Корзина 🛒',
                                      callback_data=MenuCallBack(level=3, menu_name='cart').pack()))
    keyboard.add(InlineKeyboardButton(text='Купить 💵',
                                      callback_data=MenuCallBack(level=level, menu_name='add_to_cart',
                                                                 item_id=item_id).pack()))

    keyboard.adjust(*sizes)

    row = []
    for text, menu_name in pagination_btns.items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                                            callback_data=MenuCallBack(
                                                level=level,
                                                menu_name=menu_name,
                                                category=category,
                                                page=page + 1).pack()))

        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                                            callback_data=MenuCallBack(
                                                level=level,
                                                menu_name=menu_name,
                                                category=category,
                                                page=page - 1).pack()))

    return keyboard.row(*row).as_markup()"""


async def get_items_btns(
        *,
        level: int,
        items: list,
        category: int,
):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='Назад',
                                      callback_data=MenuCallBack(level=level - 1, menu_name='catalog').pack()))
    keyboard.add(InlineKeyboardButton(text='Корзина 🛒',
                                      callback_data=MenuCallBack(level=4, menu_name='cart').pack()))

    keyboard.adjust(2)

    row = []
    for item in items:
        row.append(InlineKeyboardButton(text=item.name,
                                            callback_data=MenuCallBack(
                                            level=level + 1,
                                            menu_name="item",
                                            item_id=item.id,
                                            category=category).pack()))

    return keyboard.row(*row).as_markup()


async def get_item_btns(
        *,
        level: int,
        item_id: int,
        category: int
):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='Назад',
                                      callback_data=MenuCallBack(level=level - 1, menu_name="catalog",
                                                                 category=category).pack()))
    keyboard.add(InlineKeyboardButton(text='Корзина 🛒',
                                      callback_data=MenuCallBack(level=4, menu_name='cart').pack()))
    keyboard.add(InlineKeyboardButton(text='Купить 💵',
                                      callback_data=MenuCallBack(level=level, menu_name='add_to_cart',
                                                                 item_id=item_id).pack()))

    return keyboard.adjust(2).as_markup()


async def get_user_cart(
        *,
        level: int,
        page: int | None,
        pagination_btns: dict | None,
        item_id: int | None,
        sizes: tuple[int] = (3,)
):
    keyboard = InlineKeyboardBuilder()
    if page:
        keyboard.add(InlineKeyboardButton(text='Удалить',
                                          callback_data=MenuCallBack(level=level, menu_name='delete',
                                                                     item_id=item_id, page=page).pack()))
        keyboard.add(InlineKeyboardButton(text='-1',
                                          callback_data=MenuCallBack(level=level, menu_name='decrement',
                                                                     item_id=item_id, page=page).pack()))
        keyboard.add(InlineKeyboardButton(text='+1',
                                          callback_data=MenuCallBack(level=level, menu_name='increment',
                                                                     item_id=item_id, page=page).pack()))

        keyboard.adjust(*sizes)

        row = []
        for text, menu_name in pagination_btns.items():
            if menu_name == "next":
                row.append(InlineKeyboardButton(text=text,
                                                callback_data=MenuCallBack(level=level, menu_name=menu_name,
                                                                           page=page + 1).pack()))
            elif menu_name == "previous":
                row.append(InlineKeyboardButton(text=text,
                                                callback_data=MenuCallBack(level=level, menu_name=menu_name,
                                                                           page=page - 1).pack()))

        keyboard.row(*row)

        row2 = [
            InlineKeyboardButton(text='На главную 🏠',
                                 callback_data=MenuCallBack(level=0, menu_name='main').pack()),
            InlineKeyboardButton(text='Заказать',
                                 callback_data=MenuCallBack(level=level+1, menu_name='order_name').pack()),
        ]
        return keyboard.row(*row2).as_markup()
    else:
        keyboard.add(
            InlineKeyboardButton(text='На главную 🏠',
                                 callback_data=MenuCallBack(level=0, menu_name='main').pack()))

        return keyboard.adjust(*sizes).as_markup()


async def get_order_btns(state: FSMContext):
    keyboard = InlineKeyboardBuilder()
    row = []
    if await state.get_state() == "Order:phone":
        row.append(InlineKeyboardButton(text='Назад',
                                        callback_data="order_back_to_name"))
    elif await state.get_state() == "Order:address":
        keyboard.row(InlineKeyboardButton(text="Ближайшие пункты выдачи",
                                        url="https://www.cdek.ru/ru/offices/"))
        row.append(InlineKeyboardButton(text='Назад',
                                        callback_data="order_back_to_phone"))
    row.append(InlineKeyboardButton(text='Отмена',
                                 callback_data=MenuCallBack(level=4, menu_name='cart').pack()))
    keyboard.row(*row)

    return keyboard.as_markup()
