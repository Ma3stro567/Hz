import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from collections import defaultdict
import os
from datetime import datetime, timedelta

# Логгирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота
TOKEN = os.getenv("BOT_TOKEN")  # Токен из переменной окружения
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Данные
user_data = defaultdict(lambda: {"balance": 0, "referrals": 0, "last_bonus": None})
referral_links = {}
top_referrals = []
top_balances = []

# Генерация реферальной ссылки
def generate_referral_link(user_id):
    return f"https://t.me/YourBotUsername?start=ref{user_id}"

# Главная клавиатура
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton("🎮 Магазин", callback_data="shop"))
    keyboard.add(InlineKeyboardButton("🏆 Топ-10", callback_data="top"))
    keyboard.add(InlineKeyboardButton("📢 Реферальная система", callback_data="referral"))
    keyboard.add(InlineKeyboardButton("🎁 Забрать бонус", callback_data="claim_bonus"))
    return keyboard

# Магазин
def shop_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton("⚙️ Товар 1 - 10 Ma3coin", callback_data="buy_item_1"))
    keyboard.add(InlineKeyboardButton("⚙️ Товар 2 - 20 Ma3coin", callback_data="buy_item_2"))
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return keyboard

# Реферальная система
def referral_menu(user_id):
    keyboard = InlineKeyboardMarkup()
    referral_link = generate_referral_link(user_id)
    keyboard.add(InlineKeyboardButton("📤 Отправить ссылку", switch_inline_query=referral_link))
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return keyboard

# Топ-10
def top_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton("🏆 Топ рефералов", callback_data="top_referrals"))
    keyboard.add(InlineKeyboardButton("💰 Топ по коинам", callback_data="top_balances"))
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return keyboard

# Проверка на бонус
def can_claim_bonus(user_id):
    last_bonus = user_data[user_id]["last_bonus"]
    if last_bonus is None:
        return True
    return datetime.now() - last_bonus >= timedelta(hours=6)

# Стартовое сообщение
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()

    # Проверка на реферальный код
    if args and args.startswith("ref"):
        referrer_id = int(args[3:])
        if referrer_id != user_id:  # Нельзя пригласить самого себя
            user_data[referrer_id]["referrals"] += 1
            user_data[referrer_id]["balance"] += 2  # Бонус за реферала
            await bot.send_message(referrer_id, f"🎉 Новый реферал по вашей ссылке! +2 Ma3coin!")

    user_data[user_id]["balance"] += 5  # Бонус за старт
    await message.answer("👋 Добро пожаловать! Ваши бонусные 5 Ma3coin за старт добавлены!", reply_markup=main_menu())

# Обработка инлайн-кнопок
@dp.callback_query_handler(Text(startswith="back_"))
async def back_handler(callback_query: types.CallbackQuery):
    if callback_query.data == "back_main":
        await callback_query.message.edit_text("🏠 Главное меню", reply_markup=main_menu())

@dp.callback_query_handler(Text(equals="shop"))
async def shop_handler(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text("🛒 Добро пожаловать в магазин!", reply_markup=shop_menu())

@dp.callback_query_handler(Text(equals="referral"))
async def referral_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.message.edit_text("📢 Ваша реферальная система", reply_markup=referral_menu(user_id))

@dp.callback_query_handler(Text(equals="top"))
async def top_handler(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text("🏆 Выберите топ-лист", reply_markup=top_menu())

@dp.callback_query_handler(Text(equals="top_referrals"))
async def top_referrals_handler(callback_query: types.CallbackQuery):
    sorted_refs = sorted(user_data.items(), key=lambda x: x[1]["referrals"], reverse=True)[:10]
    text = "🏆 Топ-10 по рефералам:\n" + "\n".join([f"{i+1}. {user} - {data['referrals']} рефералов" for i, (user, data) in enumerate(sorted_refs)])
    await callback_query.message.edit_text(text, reply_markup=top_menu())

@dp.callback_query_handler(Text(equals="top_balances"))
async def top_balances_handler(callback_query: types.CallbackQuery):
    sorted_balances = sorted(user_data.items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
    text = "💰 Топ-10 по коинам:\n" + "\n".join([f"{i+1}. {user} - {data['balance']} Ma3coin" for i, (user, data) in enumerate(sorted_balances)])
    await callback_query.message.edit_text(text, reply_markup=top_menu())

@dp.callback_query_handler(Text(equals="claim_bonus"))
async def claim_bonus_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if can_claim_bonus(user_id):
        user_data[user_id]["balance"] += 3  # Бонус
        user_data[user_id]["last_bonus"] = datetime.now()
        await callback_query.message.edit_text("🎁 Вы успешно забрали бонус в 3 Ma3coin!", reply_markup=main_menu())
    else:
        await callback_query.message.edit_text("❌ Вы уже забирали бонус! Приходите позже.", reply_markup=main_menu())

@dp.callback_query_handler(Text(startswith="buy_item_"))
async def buy_item_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    item_id = int(callback_query.data.split("_")[-1])
    item_prices = {1: 10, 2: 20}
    price = item_prices.get(item_id, 0)

    if user_data[user_id]["balance"] >= price:
        user_data[user_id]["balance"] -= price
        await callback_query.message.edit_text(f"🎉 Вы успешно купили товар {item_id} за {price} Ma3coin!", reply_markup=shop_menu())
    else:
        await callback_query.message.edit_text("❌ У вас недостаточно средств для покупки.", reply_markup=shop_menu())

# Бесконечный цикл для Render
async def keep_alive():
    while True:
        await asyncio.sleep(60)

# Основной запуск
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(keep_alive())
    executor.start_polling(dp, skip_updates=True)
  
