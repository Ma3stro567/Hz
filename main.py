import os
import asyncio
import random
from datetime import date
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiohttp import web  # <-- добавлено для пинг-сервера

API_TOKEN = "7667087861:AAHeg4MpbgJ_pMZ6kc4YcuOiqqsY6u3Bpuw"
ADMIN_PASSWORD = "popopo12"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

users = {}
auto_tasks = {}
admin_sessions = {}

messages_today = 0
current_day = date.today()

class MessageCounterMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        global messages_today, current_day
        today = date.today()
        if today != current_day:
            current_day = today
            messages_today = 0
        messages_today += 1

dp.middleware.setup(MessageCounterMiddleware())

def get_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🖱️ Клик", callback_data="click")],
        [InlineKeyboardButton("🛒 Магазин", callback_data="shop")],
        [InlineKeyboardButton("🏆 Топы", callback_data="tops")],
        [InlineKeyboardButton("🎁 Рефералка", callback_data="referral")]
    ])

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
            'autoclick': 0,
            'autoclick_level': 0,
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
        await callback.answer(f"✅ Клик улучшен до уровня {user['upgrades']}!")
    else:
        await callback.answer(f"❌ Не хватает кликов! Нужно {price}.")
    await shop_handler(callback)

@dp.callback_query_handler(lambda c: c.data == 'reduce_cd')
async def reduce_cd(callback: types.CallbackQuery):
    user = users[callback.from_user.id]
    if user['clicks'] >= 3000:
        user['clicks'] -= 3000
        user['cooldown'] = max(0.1, user['cooldown'] - 1)
        await callback.answer("✅ Задержка уменьшена!")
    else:
        await callback.answer("❌ Недостаточно кликов!")
    await shop_handler(callback)

@dp.callback_query_handler(lambda c: c.data == 'secret_box')
async def secret_box(callback: types.CallbackQuery):
    user = users[callback.from_user.id]
    if user['clicks'] >= 400:
        user['clicks'] -= 400
        reward = random.randint(1, 1000)
        user['clicks'] += reward
        await callback.answer(f"🎁 Бокс выдал тебе {reward} кликов!")
    else:
        await callback.answer("❌ Недостаточно кликов!")
    await shop_handler(callback)

@dp.callback_query_handler(lambda c: c.data == 'buy_autoclick')
async def buy_autoclick(callback: types.CallbackQuery):
    user = users[callback.from_user.id]
    if user['clicks'] >= 200:
        user['clicks'] -= 200
        user['autoclick'] = 1
        user['autoclick_level'] = 1
        if callback.from_user.id not in auto_tasks:
            auto_tasks[callback.from_user.id] = asyncio.create_task(start_autoclick(callback.from_user.id))
        await callback.answer("✅ Автоклик куплен!")
    else:
        await callback.answer("❌ Недостаточно кликов!")
    await shop_handler(callback)

@dp.callback_query_handler(lambda c: c.data == 'upgrade_autoclick')
async def upgrade_autoclick(callback: types.CallbackQuery):
    user = users[callback.from_user.id]
    if user.get('autoclick', 0) == 0:
        await callback.answer("❌ Сначала купите автоклик!")
        return
    if user['autoclick_level'] >= 15:
        await callback.answer("❌ Достигнут лимит улучшения автоклика (15).")
        return
    level = user['autoclick_level']
    fixed_prices = [200, 400, 600, 800, 1000]
    if level <= len(fixed_prices):
        price = fixed_prices[level - 1]
    else:
        price = 1000 + (level - 5) * 200
    if user['clicks'] >= price:
        user['clicks'] -= price
        user['autoclick'] *= 2
        user['autoclick_level'] += 1
        await callback.answer(f"✅ Автоклик улучшен до x{user['autoclick']} (уровень {user['autoclick_level']}).")
    else:
        await callback.answer("❌ Не хватает кликов!")
    await shop_handler(callback)

async def start_autoclick(user_id):
    while True:
        await asyncio.sleep(30)
        if user_id in users and users[user_id].get('autoclick', 0) > 0:
            users[user_id]['clicks'] += users[user_id]['autoclick']

@dp.callback_query_handler(lambda c: c.data == 'tops')
async def tops_handler(callback: types.CallbackQuery):
    top_clicks = sorted(users.items(), key=lambda x: x[1]['clicks'], reverse=True)[:5]
    top_refs = sorted(users.items(), key=lambda x: x[1]['referrals'], reverse=True)[:5]
    text = "🏆 Топ по кликам:\n"
    for i, (uid, data) in enumerate(top_clicks, start=1):
        chat = await bot.get_chat(uid)
        name = f"@{chat.username}" if chat.username else chat.full_name
        text += f"{i}. {name} — {data['clicks']} кликов\n"
    text += "\n👥 Топ по рефералам:\n"
    for i, (uid, data) in enumerate(top_refs, start=1):
        chat = await bot.get_chat(uid)
        name = f"@{chat.username}" if chat.username else chat.full_name
        text += f"{i}. {name} — {data['referrals']} рефералов\n"
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == 'referral')
async def referral_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    username = bot_info.username
    link = f"https://t.me/{username}?start={user_id}"
    text = (
        f"🎁 Приглашай друзей по ссылке:\n{link}\n\n"
        "За каждого друга — 100 кликов!"
    )
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == 'back_main')
async def back_main(callback: types.CallbackQuery):
    await update_main_menu(callback, callback.from_user.id)

# ==== ПИНГ-СЕРВЕР ДЛЯ RENDER ====
async def handle_ping(request):
    return web.Response(text="Bot is alive!")

app = web.Application()
app.router.add_get("/", handle_ping)

async def start_web_server():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()

# ==== ПОДДЕРЖИВАЕМ ЖИЗНЬ ====
async def keep_alive():
    while True:
        await asyncio.sleep(3600)

# ==== СТАРТ БОТА ====
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())  # Веб-сервер для Render
    loop.create_task(keep_alive())
    executor.start_polling(dp, skip_updates=True)
