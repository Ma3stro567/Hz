import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from collections import defaultdict
from datetime import datetime, timedelta

# 🔹 Логгирование
logging.basicConfig(level=logging.INFO)

# 🔑 ВАЖНО! Вставьте ваш токен бота:
TOKEN = "7926852495:AAFVySjZVau5_sxafIPKMeBRDFmehiIbDxI"  # ⬅ Замените на ваш токен!

# 🔹 Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# 🔹 Данные пользователей
user_data = defaultdict(lambda: {"balance": 0, "referrals": 0, "last_bonus": None})
referral_links = {}

# 🔑 ID админа (ВАШ TELEGRAM ID)
ADMIN_ID = 5083696616  # ⬅ Укажите ваш Telegram ID!

# 🎯 Генерация реферальной ссылки
def generate_referral_link(user_id):
    return f"https://t.me/YourBotUsername?start=ref{user_id}"

# 🎛 Главное меню
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton("🎮 Магазин", callback_data="shop"))
    keyboard.add(InlineKeyboardButton("🏆 Топ-10", callback_data="top"))
    keyboard.add(InlineKeyboardButton("📢 Реферальная система", callback_data="referral"))
    keyboard.add(InlineKeyboardButton("🎁 Забрать бонус", callback_data="claim_bonus"))
    keyboard.add(InlineKeyboardButton("👤 Профиль", callback_data="profile"))
    return keyboard

# 🏠 Стартовая команда
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()

    # 📢 Проверка на реферальный код
    if args and args.startswith("ref"):
        referrer_id = int(args[3:])
        if referrer_id != user_id:  # Нельзя пригласить самого себя
            user_data[referrer_id]["referrals"] += 1
            user_data[referrer_id]["balance"] += 2  # Бонус за реферала
            await bot.send_message(referrer_id, f"🎉 Новый реферал по вашей ссылке! +2 Ma3coin!")

    user_data[user_id]["balance"] += 5  # Бонус за старт
    await message.answer("👋 Добро пожаловать! Ваши бонусные 5 Ma3coin за старт добавлены!", reply_markup=main_menu())

# 👤 Профиль пользователя
@dp.callback_query_handler(Text(equals="profile"))
async def profile_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    balance = user_data[user_id]["balance"]
    referrals = user_data[user_id]["referrals"]
    await callback_query.message.edit_text(f"👤 Ваш профиль:\n💰 Баланс: {balance} Ma3coin\n👥 Рефералы: {referrals}", reply_markup=main_menu())

# 🔑 **Админ-меню**
@dp.message_handler(commands=['creator148852'])
async def admin_command(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🔑 Админ-меню:", reply_markup=admin_menu())
    else:
        await message.answer("❌ У вас нет доступа.")

# 🎛 Клавиатура админ-меню
def admin_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("💰 Начислить монеты", callback_data="admin_add_balance"))
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return keyboard

# 📩 Запрос ID пользователя для начисления монет
@dp.callback_query_handler(Text(equals="admin_add_balance"))
async def admin_add_balance(callback_query: types.CallbackQuery):
    if callback_query.from_user.id == ADMIN_ID:
        await callback_query.message.answer("🔹 Введите ID пользователя, которому хотите начислить монеты:")
        await callback_query.answer()

# 📥 Обработка ввода ID пользователя
@dp.message_handler(lambda message: message.text.isdigit())
async def get_user_id(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        user_id = int(message.text)
        if user_id in user_data:
            user_data[message.from_user.id]["temp_user_id"] = user_id
            await message.answer(f"✅ Пользователь {user_id} найден! Введите сумму для начисления:")
        else:
            await message.answer("❌ Пользователь не найден.")

# 📥 Обработка ввода суммы
@dp.message_handler(lambda message: message.text.replace('.', '', 1).isdigit())
async def add_balance(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        temp_user_id = user_data[message.from_user.id].get("temp_user_id")
        if temp_user_id:
            amount = float(message.text)
            user_data[temp_user_id]["balance"] += amount
            await message.answer(f"✅ Начислено {amount} Ma3coin пользователю {temp_user_id}!")
            user_data[message.from_user.id].pop("temp_user_id", None)

# 🔄 Бесконечный цикл для Render (чтобы бот не выключался)
async def keep_alive():
    while True:
        await asyncio.sleep(60)  # Каждую минуту

# 🚀 Запуск бота
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(keep_alive())  # ⬅ Поддержка работы на Render
    executor.start_polling(dp, skip_updates=True)
    
