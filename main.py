import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from collections import defaultdict
from datetime import datetime, timedelta

# Логгирование
logging.basicConfig(level=logging.INFO)

# ВСТАВЬТЕ ВАШ ТОКЕН ЗДЕСЬ
TOKEN = "7926852495:AAFVySjZVau5_sxafIPKMeBRDFmehiIbDxI"  # Замените на токен вашего бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Данные
user_data = defaultdict(lambda: {"balance": 0, "referrals": 0, "last_bonus": None})
admin_ids = [5083696616]  # Замените на ваш Telegram ID

# Главная клавиатура
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🎮 Магазин", callback_data="shop"),
        InlineKeyboardButton("🏆 Топ-10", callback_data="top"),
        InlineKeyboardButton("📢 Реферальная система", callback_data="referral"),
        InlineKeyboardButton("🎁 Забрать бонус", callback_data="claim_bonus"),
        InlineKeyboardButton("👤 Профиль", callback_data="profile")
    )
    return keyboard

# Клавиатура профиля
def profile_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("поддержать разработку", url="https://t.me/xrocket?start=inv_GhSTKJGeBcaVcHg"),  # Ссылка на оплату
        InlineKeyboardButton("🎮 Перейти в магазин", callback_data="shop"),   # Кнопка для перехода в магазин
        InlineKeyboardButton("🔙 Назад", callback_data="back_main")
    )
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

# Обработка профиля
@dp.callback_query_handler(Text(equals="profile"))
async def profile_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    balance = user_data[user_id]["balance"]
    referrals = user_data[user_id]["referrals"]
    await callback_query.message.edit_text(
        f"👤 Ваш профиль:\n"
        f"💰 Баланс: {balance} Ma3coin\n"
        f"👥 Количество рефералов: {referrals}\n",
        reply_markup=profile_menu()
    )

# Обработка перехода в магазин
@dp.callback_query_handler(Text(equals="shop"))
async def shop_handler(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text("🛒 Добро пожаловать в магазин!", reply_markup=main_menu())

# Начисление бонусов
@dp.callback_query_handler(Text(equals="claim_bonus"))
async def claim_bonus_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if can_claim_bonus(user_id):
        user_data[user_id]["balance"] += 3  # Бонус
        user_data[user_id]["last_bonus"] = datetime.now()
        await callback_query.message.edit_text("🎁 Вы успешно забрали бонус в 3 Ma3coin!", reply_markup=main_menu())
    else:
        await callback_query.message.edit_text("❌ Вы уже забирали бонус! Приходите позже.", reply_markup=main_menu())

# Админ меню
@dp.message_handler(commands=['creator148852'])
async def admin_command(message: types.Message):
    if message.from_user.id in admin_ids:
        await message.answer("🔑 Админ-меню:", reply_markup=admin_menu())
    else:
        await message.answer("❌ У вас нет прав для доступа к этому меню.")

# Клавиатура админ меню
def admin_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💰 Начислить монеты", callback_data="admin_add_coins"),
        InlineKeyboardButton("🔙 Назад", callback_data="back_main")
    )
    return keyboard

# Начисление монет (админ)
@dp.callback_query_handler(Text(equals="admin_add_coins"))
async def admin_add_coins(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text("💰 Введите ID пользователя, которому хотите начислить монеты:")
    await AdminStates.waiting_for_user_id.set()

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_amount = State()

@dp.message_handler(state=AdminStates.waiting_for_user_id)
async def process_user_id(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    if user_id.isdigit():
        user_id = int(user_id)
        if user_id in user_data:
            await state.update_data(user_id=user_id)
            await message.answer("✅ Пользователь найден! Введите сумму для начисления:")
            await AdminStates.waiting_for_amount.set()
        else:
            await message.answer("❌ Пользователь не найден. Попробуйте снова:")
    else:
        await message.answer("❌ Неверный ID. Попробуйте снова:")

@dp.message_handler(state=AdminStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    amount = message.text.strip()
    if amount.isdigit():
        amount = int(amount)
        data = await state.get_data()
        user_id = data['user_id']
        user_data[user_id]["balance"] += amount
        await message.answer(f"✅ Успешно начислено {amount} Ma3coin пользователю {user_id}.", reply_markup=main_menu())
        await state.finish()
    else:
        await message.answer("❌ Неверная сумма. Попробуйте снова:")

# Бесконечный цикл
async def keep_alive():
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(keep_alive())  # Бесконечный цикл
    executor.start_polling(dp, skip_updates=True)
