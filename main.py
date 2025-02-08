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

# 🔹 Включаем логирование
logging.basicConfig(level=logging.INFO)

# ✅ ВАЖНО! ВСТАВЬТЕ ВАШ ТОКЕН ОТ BOTFATHER:
TOKEN = "7926852495:AAFVySjZVau5_sxafIPKMeBRDFmehiIbDxI"  # ⬅ СЮДА ВСТАВЬТЕ ТОКЕН!

# ⛔ Если бот на Render, лучше использовать переменную окружения:
# TOKEN = os.getenv("BOT_TOKEN")  # ⬅ Используйте ЭТО на Render!

# 🔹 Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# 🔹 Данные пользователей
user_data = defaultdict(lambda: {"balance": 0, "referrals": 0, "last_bonus": None})
referral_links = {}

# 🔑 ID админа (ВАШ TELEGRAM ID)
ADMIN_ID = 5083696616  # ⬅ Замените на ваш Telegram ID!

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
    return keyboard

# 🎁 Проверка на бонус
def can_claim_bonus(user_id):
    last_bonus = user_data[user_id]["last_bonus"]
    return last_bonus is None or datetime.now() - last_bonus >= timedelta(hours=6)

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

# 🛠 **АДМИН-МЕНЮ**
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
            await message.answer(f"✅ Пользователь найден! Введите сумму для начисления:")
            user_data[user_id]["waiting_for_amount"] = True  # Флаг ожидания суммы
            user_data[user_id]["temp_user_id"] = user_id
        else:
            await message.answer("❌ Пользователь не найден.")

# 📥 Обработка ввода суммы
@dp.message_handler(lambda message: message.text.replace('.', '', 1).isdigit())
async def add_balance(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        user_id = user_data[message.from_user.id].get("temp_user_id")
        if user_id:
            amount = float(message.text)
            user_data[user_id]["balance"] += amount
            await message.answer(f"✅ Начислено {amount} Ma3coin пользователю {user_id}!")
            user_data[user_id].pop("waiting_for_amount", None)
            user_data[user_id].pop("temp_user_id", None)

# 🔄 Бесконечный цикл для Render (чтобы бот не выключался)
async def keep_alive():
    while True:
        await asyncio.sleep(60)  # Каждую минуту

# 🚀 Запуск бота
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(keep_alive())  # ⬅ Поддержка работы на Render
    executor.start_polling(dp, skip_updates=True)
    
