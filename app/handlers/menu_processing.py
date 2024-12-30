from aiogram.types import InputMediaPhoto
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.paginator import Paginator
from app.database import requests as rq
from app import keyboards as kb


class Order(StatesGroup):
    name = State()
    phone = State()
    address = State()


class Promocode(StatesGroup):
    promocode = State()


async def main_menu(session, level, menu_name):
    banner = await rq.orm_get_banner_page(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    kbds = await kb.get_user_main_btns(level=level)

    return image, kbds


async def catalog(session, level, menu_name):
    banner = await rq.orm_get_banner_page(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    categories = await rq.orm_get_categories(session)
    kbds = await kb.get_user_catalog_btns(level=level, categories=categories)

    return image, kbds


def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns["◀ Пред."] = "previous"

    if paginator.has_next():
        btns["След. ▶"] = "next"

    return btns


"""async def items(session, level, category, page):
    items = await rq.orm_get_items(session, category_id=category)

    paginator = Paginator(items, page=page)
    item = paginator.get_page()[0]

    image = InputMediaPhoto(
        media=item.image,
        caption=f"<strong>{item.name}\
                </strong>\n{item.description}\nСтоимость: {round(item.price, 2)}\n\
                <strong>Товар {paginator.page} из {paginator.pages}</strong>",
    )

    pagination_btns = pages(paginator)

    kbds = await kb.get_items_btns(
        level=level,
        category=category,
        page=page,
        pagination_btns=pagination_btns,
        item_id=item.id,
    )

    return image, kbds"""


async def items(session, level, category_id):
    items = await rq.orm_get_items(session, category_id=category_id)
    category = await rq.orm_get_category(session, category_id=category_id)
    image = InputMediaPhoto(
        media=category.image,
        caption=f"<strong>{category.name}</strong>\n\n"
                f"<strong>{category.description}</strong>\n")


    kbds = await kb.get_items_btns(
        level=level,
        items=items,
        category=category_id
    )

    return image, kbds


async def item(session, level, item_id, category):
    item = await rq.orm_get_item(session, item_id=item_id)

    image = InputMediaPhoto(
        media=item.image,
        caption=f"<strong>{item.name}</strong>\n\n"
                f"<strong>{item.description}</strong>\n\n"
                f"<strong>{item.color}</strong>\n\n"
                f"<strong>{item.price}</strong>"
    )

    kbds = await kb.get_item_btns(
        level=level,
        item_id=item_id,
        category=category
    )

    return image, kbds


async def carts(session, level, menu_name, page, user_id, item_id):
    if menu_name == "delete":
        await rq.orm_delete_cart(session, user_id, item_id)
        if page > 1:
            page -= 1
    elif menu_name == "decrement":
        is_cart = await rq.orm_reduce_item_in_cart(session, user_id, item_id)
        if page > 1 and not is_cart:
            page -= 1
    elif menu_name == "increment":
        await rq.orm_add_cart(session, user_id, item_id)

    carts = await rq.orm_get_carts(session, user_id)

    if not carts:
        banner = await rq.orm_get_banner_page(session, "cart")
        image = InputMediaPhoto(
            media=banner.image, caption=f"<strong>{banner.description}</strong>"
        )

        kbds = await kb.get_user_cart(
            level=level,
            page=None,
            pagination_btns=None,
            item_id=None,
        )

    else:
        paginator = Paginator(carts, page=page)

        cart = paginator.get_page()[0]

        cart_price = round(cart.quantity * cart.item.price, 2)
        total_price = round(
            sum(cart.quantity * cart.item.price for cart in carts), 2
        )
        image = InputMediaPhoto(
            media=cart.item.image,
            caption=f"<strong>{cart.item.name}</strong>\n{cart.item.price}$ x {cart.quantity} = {cart_price}$\
                    \nТовар {paginator.page} из {paginator.pages} в корзине.\nОбщая стоимость товаров в корзине {total_price}",
        )

        pagination_btns = pages(paginator)

        kbds = await kb.get_user_cart(
            level=level,
            page=page,
            pagination_btns=pagination_btns,
            item_id=cart.item.id,
        )

    return image, kbds


async def order(session, menu_name, state: FSMContext):
    banner = await rq.orm_get_banner_page(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    await state.set_state(Order.name)

    kbds = await kb.get_order_btns(state=state)

    return image, kbds


async def promocode(session, menu_name, state: FSMContext):
    banner = await rq.orm_get_banner_page(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    await state.set_state(Promocode.promocode)

    kbds = await kb.get_order_btns(state=state)

    return image, kbds


async def get_menu_content(
    session: AsyncSession,
    level: int,
    menu_name: str,
    category: int | None = None,
    page: int | None = None,
    state: FSMContext | None = None,
    item_id: int | None = None,
    user_id: int | None = None,
):
    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 1:
        return await catalog(session, level, menu_name)
    elif level == 2:
        return await items(session, level, category)
    elif level == 3:
        return await item(session, level, item_id, category)
    elif level == 4:
        return await carts(session, level, menu_name, page, user_id, item_id)
    elif level == 5:
        return await order(session, menu_name, state)
    elif level == 6:
        return await promocode(session, menu_name, state)
