from aiogram.types import BotCommand
from aiogram.utils.formatting import Bold, as_list, as_marked_section


ALLOWED_UPDATES = ["message, callback_query"]

IMAGE = "AgACAgIAAxkBAAIMrWdCKtsszBYr50hxUvJV9-bU7_Q2AAKH8DEb8gIRSsYffve9SbwKAQADAgADeAADNgQ"

private = [
    BotCommand(command='menu', description='Меню'),
    BotCommand(command='cart', description='Корзина')
]

descriptions_and_images_for_categories = {
    "headphones": ["Описание наушников", IMAGE],
    "watches": ["Описание часов", IMAGE],
    "fans": ["Описание фенов", IMAGE]
}

descriptions_and_images_for_banners = {
    "main": ["Это бот магазина TOPSTORE", IMAGE],
    "payment": ["Оплата", IMAGE],
    'catalog': ['Категории:', IMAGE],
    'cart': ['В корзине ничего нет!', IMAGE],
    'promocode': ['Введите промокод:', IMAGE],
    'order_name': ['Введите ФИО:', IMAGE]
}

steps = ["хотите", "категорию", "из"]