import os
import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor

# Токен бота вставлен напрямую (небезопасно для production-окружения)
API_TOKEN = "7667087861:AAHF20MiMg0BrR_Fd3nlXFTsniqbxHd3JZc"
ADMIN_PASSWORD = "popopo12"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Словари для хранения информации о пользователях, автозадачах и админ-сессиях
users = {}
auto_tasks = {}
admin_sessions = {}

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
            'autoclick': 0
        }
        if ref.isdigit() and int(ref) in users and int(ref) != user_id:
            users[int(ref)]['clicks'] += 100
            users[int(ref)]['referrals'] += 1
            await bot.send_message(int(ref), f"🎉 Новый реферал! +100 кликов!")

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
        if callback.from_user.id not in auto_tasks:
            auto_tasks[callback.from_user.id] = asyncio.create_task(start_autoclick(callback.from_user.id))
        await callback.answer("✅ Автоклик куплен!")
    else:
        await callback.answer("❌ Недостаточно кликов!")
    await shop_handler(callback)

@dp.callback_query_handler(lambda c: c.data == 'upgrade_autoclick')
async def upgrade_autoclick(callback: types.CallbackQuery):
    user = users[callback.from_user.id]
    level = user.get('autoclick', 0)
    price = 200 * (2 ** level)
    if user['clicks'] >= price:
        user['clicks'] -= price
        user['autoclick'] += 1
        await callback.answer(f"✅ Автоклик улучшен до {user['autoclick']}!")
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
    link = f"https://t.me/{clicker767}?start={user_id}"
    text = f"🎁 Приглашай друзей по ссылке:\n{link}\n\nЗа каждого друга — 100 кликов!"
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == 'back_main')
async def back_main(callback: types.CallbackQuery):
    await update_main_menu(callback, callback.from_user.id)

# ----- Админ-панель -----
@dp.message_handler(commands=['adminpanel'])
async def admin_panel(message: types.Message):
    await message.answer("🔐 Введите пароль:")
    admin_sessions[message.from_user.id] = {'stage': 'await_password'}

@dp.message_handler()
async def admin_logic(message: types.Message):
    uid = message.from_user.id
    if uid not in admin_sessions:
        return
    session = admin_sessions[uid]
    if session['stage'] == 'await_password':
        if message.text == ADMIN_PASSWORD:
            session['stage'] = 'await_action'
            kb = InlineKeyboardMarkup()
            # Формируем кнопки для всех пользователей (даже если у них нет username)
            for uid_, data in users.items():
                chat = await bot.get_chat(uid_)
                name = f"@{chat.username}" if chat.username else f"{chat.full_name} ({uid_})"
                kb.add(InlineKeyboardButton(name, callback_data=f"admin_add:{uid_}"))
            kb.add(InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"))
            await message.answer("🛠 Админ-панель:", reply_markup=kb)
        else:
            await message.answer("❌ Неверный пароль")
            del admin_sessions[uid]
    elif session['stage'] == 'await_amount':
        try:
            amount = int(message.text)
            target_id = int(session['target'])
            if target_id in users:
                users[target_id]['clicks'] += amount
                target_chat = await bot.get_chat(target_id)
                name = f"@{target_chat.username}" if target_chat.username else target_chat.full_name
                await message.answer(f"✅ {name} получил {amount} кликов.")
            else:
                await message.answer("❌ Пользователь не найден.")
            del admin_sessions[uid]
        except Exception as e:
            await message.answer("❗ Введите число кликов")
    elif session['stage'] == 'broadcast':
        text = message.text
        for uid_ in users:
            try:
                await bot.send_message(uid_, text)
            except Exception as e:
                continue
        await message.answer("✅ Рассылка завершена.")
        del admin_sessions[uid]

@dp.callback_query_handler(lambda c: c.data.startswith("admin_add:") or c.data == "admin_broadcast")
async def admin_buttons(callback: types.CallbackQuery):
    uid = callback.from_user.id
    if uid not in admin_sessions:
        return
    if callback.data.startswith("admin_add:"):
        target_id = callback.data.split("admin_add:")[1]
        admin_sessions[uid] = {'stage': 'await_amount', 'target': target_id}
        target_chat = await bot.get_chat(int(target_id))
        name = f"@{target_chat.username}" if target_chat.username else target_chat.full_name
        await callback.message.edit_text(f"Введите сколько кликов добавить для {name}.")
    elif callback.data == "admin_broadcast":
        admin_sessions[uid] = {'stage': 'broadcast'}
        await callback.message.edit_text("Введите текст рассылки:")

# ----- Фоновая задача: бесконечный цикл -----
async def keep_alive():
    while True:
        await asyncio.sleep(3600)  # Засыпаем на 1 час

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # Запускаем фоновую задачу, которая будет работать бесконечно
    loop.create_task(keep_alive())
    # Запуск бота через polling (опрос обновлений)
    executor.start_polling(dp, skip_updates=True)
