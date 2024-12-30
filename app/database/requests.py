from datetime import datetime

from app.database.models import User, Category, Item, Banner, Cart, Promocode
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload


async def orm_add_user(
    session: AsyncSession,
    user_id: int,
    name: str,
    promocode: str
):
    query = select(User).where(User.tg_id == user_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            User(tg_id=user_id, name=name, promocode=promocode)
        )
        await session.commit()


async def orm_change_user_promocode(
    session: AsyncSession,
    user_id: int,
    promocode=None,
):
    query = update(User).where(User.tg_id == user_id).values(promocode=promocode)
    await session.execute(query)
    await session.commit()


async def orm_get_categories(session: AsyncSession):
    query = select(Category)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_category(session: AsyncSession, category_id: int):
    query = select(Category).where(Category.id == category_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_create_categories(session: AsyncSession, descriptions_and_images_for_categories: dict):
    query = select(Category)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Category(name=key, description=value[0], image=value[1])
                     for key, value in descriptions_and_images_for_categories.items()])
    await session.commit()


async def orm_add_item(session: AsyncSession, data: dict):
    obj = Item(
        name=data["name"],
        description=data["description"],
        price=float(data["price"]),
        image=data["image"],
        category_id=int(data["category"])
    )
    session.add(obj)
    await session.commit()


async def orm_add_cart(session: AsyncSession, user_id: int, item_id: int):
    query = select(Cart).where(Cart.user_id == user_id, Cart.item_id == item_id)
    cart = await session.execute(query)
    cart = cart.scalar()
    if cart:
        cart.quantity += 1
        await session.commit()
        return cart
    else:
        session.add(Cart(user_id=user_id, item_id=item_id, quantity=1))
        await session.commit()


async def orm_get_carts(session: AsyncSession, user_id):
    query = select(Cart).filter(Cart.user_id == user_id).options(joinedload(Cart.item))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_delete_cart(session: AsyncSession, user_id: int, item_id: int):
    query = delete(Cart).where(Cart.user_id == user_id, Cart.item_id == item_id)
    await session.execute(query)
    await session.commit()


async def orm_delete_carts(session: AsyncSession, user_id: int):
    query = delete(Cart).where(Cart.user_id == user_id)
    await session.execute(query)
    await session.commit()


async def orm_reduce_item_in_cart(session: AsyncSession, user_id: int, item_id: int):
    query = select(Cart).where(Cart.user_id == user_id, Cart.item_id == item_id)
    cart = await session.execute(query)
    cart = cart.scalar()

    if not cart:
        return
    if cart.quantity > 1:
        cart.quantity -= 1
        await session.commit()
        return True
    else:
        await orm_delete_cart(session, user_id, item_id)
        await session.commit()
        return False


async def orm_get_items(session: AsyncSession, category_id: int):
    query = select(Item).where(Item.category_id == category_id)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_item(session: AsyncSession, item_id: int):
    query = select(Item).where(Item.id == item_id).options(joinedload(Item.category))
    result = await session.execute(query)
    return result.scalar()


async def orm_delete_item(session: AsyncSession, item_id: int):
    query = delete(Item).where(Item.id == item_id)
    await session.execute(query)
    await session.commit()


async def orm_update_item(session: AsyncSession, item_id, data):
    query = update(Item).where(Item.id == item_id).values(
        name=data["name"],
        description=data["description"],
        price=float(data["price"]),
        image=data["image"],
        category_id=int(data["category"]),
)
    await session.execute(query)
    await session.commit()


async def orm_add_banner(session: AsyncSession, data: dict):
    query = select(Banner)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Banner(name=name, image=desc[1], description=desc[0]) for name, desc in data.items()])
    await session.commit()


async def orm_get_banners(session: AsyncSession):
    query = select(Banner)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_change_banner_image(session: AsyncSession, name: str, image: str):
    query = update(Banner).where(Banner.name == name).values(image=image)
    await session.execute(query)
    await session.commit()


async def orm_get_banner_page(session: AsyncSession, page: str):
    query = select(Banner).where(Banner.name == page)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_banner_id(session: AsyncSession, banner_id: int):
    query = select(Banner).where(Banner.id == banner_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_banner(session: AsyncSession, banner_id: int, data):
    query = update(Banner).where(Banner.id == banner_id).values(
        description=data["description"],
        image=data["image"]
)
    await session.execute(query)
    await session.commit()


async def orm_add_promocode(session: AsyncSession, name: str, discount: float, duration: datetime):
    obj = Promocode(
        name=name,
        discount=discount,
        duration=duration)

    session.add(obj)
    await session.commit()

async def orm_get_promocode(session: AsyncSession, name: str):
    query = select(Promocode).where(Promocode.name == name)
    result = await session.execute(query)
    return result.scalar()
