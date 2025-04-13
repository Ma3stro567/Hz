import os
import asyncio
import random
from datetime import date
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.dispatcher.middlewares import BaseMiddleware

# Вставляем токен напрямую (в production рекомендуется использовать переменные окружения)
API_TOKEN = "7667087861:AAGloScjJqqaby3eklIzKDiEldeAaJRxoDE"
ADMIN_PASSWORD = "popopo12"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Глобальные словари и переменные
users = {}          # данные пользователей
auto_tasks = {}     # задачи автоклика
admin_sessions = {} # сессии админа

# Переменные для подсчёта сообщений за текущий день
messages_today = 0
current_day = date.today()

# Middleware для подсчёта сообщений
class MessageCounterMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        global messages_today, current_day
        today = date.today()
        if today != current_day:
            current_day = today
            messages_today = 0
        messages_today += 1

dp.middleware.setup(MessageCounterMiddleware())

# Основная клавиатура для пользователей
def get_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🖱️ Клик", callback_data="click")],
        [InlineKeyboardButton("🛒 Магазин", callback_data="shop")],
        [InlineKeyboardButton("🏆 Топы", callback_data="tops")],
        [InlineKeyboardButton("🎁 Рефералка", callback_data="referral")]
    ])

# ----- Обработчик команды /start -----
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    ref = message.get_args()
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {
            'clicks': 0,
            'upgrades': 1,
            'cooldown': 0,
            'clicks_in_row': 0,
            'referrals': 0,
            'in_pause': False,
            'autoclick': 0,         # пока автоклик не куплен
            'autoclick_level': 0,   # уровень улучшения автоклика
            'username': message.from_user.username or "",
            'full_name': message.from_user.full_name
        }
        if ref.isdigit() and int(ref) in users and int(ref) != user_id:
            users[int(ref)]['clicks'] += 100
            users[int(ref)]['referrals'] += 1
            await bot.send_message(int(ref), "🎉 Новый реферал! +100 кликов!")
    await message.answer("Добро пожаловать в кликер-бот! 🐹", reply_markup=get_main_kb())

async def update_main_menu(callback, user_id):
    user = users[user_id]
    msg = (
        f"🖱️ Ты накликал: {user['clicks']} кликов\n"
        f"💥 Сила клика: {user['upgrades']}\n"
        f"🤖 Автоклик: {user.get('autoclick', 0)}"
    )
    await callback.message.edit_text(msg, reply_markup=get_main_kb())

# ----- Обработчик кнопки "Клик" -----
@dp.callback_query_handler(lambda c: c.data == 'click')
async def click_handler(callback: types.CallbackQuery):
    user = users[callback.from_user.id]
    if user.get('in_pause'):
        await callback.answer("⌛ Подожди немного...")
        return
    user['clicks'] += user['upgrades']
    user['clicks_in_row'] += 1
    if user['clicks_in_row'] >= 10:
        user['in_pause'] = True
        await callback.answer("⏳ Пауза 3 секунды...")
        await asyncio.sleep(3)
        user['clicks_in_row'] = 0
        user['in_pause'] = False
    await update_main_menu(callback, callback.from_user.id)

# ----- Магазин -----
@dp.callback_query_handler(lambda c: c.data == 'shop')
async def shop_handler(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("💪 Улучшить клик", callback_data="upgrade_click")],
        [InlineKeyboardButton("⚡ Уменьшить задержку — 3000", callback_data="reduce_cd")],
        [InlineKeyboardButton("🎲 Секретный бокс — 400", callback_data="secret_box")],
        [InlineKeyboardButton("🤖 Автоклик — 200", callback_data="buy_autoclick")],
        [InlineKeyboardButton("🔁 Улучшить автоклик x2", callback_data="upgrade_autoclick")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_main")]
    ])
    await callback.message.edit_text("🛒 Магазин улучшений:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == 'upgrade_click')
async def upgrade_click(callback: types.CallbackQuery):
    user = users[callback.from_user.id]
    upgrade_prices = [100, 200, 300, 500, 700, 1000]
    current_level = user['upgrades'] - 1
    if current_level >= len(upgrade_prices):
        await callback.answer("🔝 Максимальный уровень клика!")
        return
    price = upgrade_prices[current_level]
    if user['clicks'] >= price:
        user['clicks'] -= price
        user['upgrades'] += 1
        await callback.answer(f"✅ К
