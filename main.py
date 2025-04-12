import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor

API_TOKEN = '7667087861:AAGloScjJqqaby3eklIzKDiEldeAaJRxoDE'  # Вставь сюда токен
ADMIN_PASSWORD = "popopo12"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

users = {}
admin_sessions = {}

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
            'in_pause': False
        }

        if ref.isdigit() and int(ref) in users and int(ref) != user_id:
            users[int(ref)]['clicks'] += 100
            users[int(ref)]['referrals'] += 1
            await bot.send_message(int(ref), f"🎉 Новый реферал! +100 кликов!")

    await message.answer("Добро пожаловать в кликер-бот! 🐹", reply_markup=get_main_kb())


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

    await callback.message.edit_text(f"🖱️ Ты накликал: {user['clicks']} кликов", reply_markup=get_main_kb())


@dp.callback_query_handler(lambda c: c.data == 'shop')
async def shop_handler(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("💪 Улучшить клик (+1) — 100", callback_data="upgrade_click")],
        [InlineKeyboardButton("⚡ Уменьшить задержку — 3000", callback_data="reduce_cd")],
        [InlineKeyboardButton("🎲 Секретный бокс — 400", callback_data="secret_box")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_main")]
    ])
    await callback.message.edit_text("🛒 Магазин улучшений:", reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data == 'upgrade_click')
async def upgrade_click(callback: types.CallbackQuery):
    user = users[callback.from_user.id]
    if user['clicks'] >= 100:
        user['clicks'] -= 100
        user['upgrades'] += 1
        await callback.answer("✅ Клик улучшен!")
    else:
        await callback.answer("❌ Недостаточно кликов!")
    await shop_handler(callback)


@dp.callback_query_handler(lambda c: c.data == 'reduce_cd')
async def reduce_cd(callback: types.CallbackQuery):
    user = users[callback.from_user.id]
    if user['clicks'] >= 3000:
        user['clicks'] -= 3000
        user['cooldown'] = max(0, user['cooldown'] - 1)
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


@dp.callback_query_handler(lambda c: c.data == 'tops')
async def tops_handler(callback: types.CallbackQuery):
    top_clicks = sorted(users.items(), key=lambda x: x[1]['clicks'], reverse=True)[:5]
    top_refs = sorted(users.items(), key=lambda x: x[1]['referrals'], reverse=True)[:5]

    text = "🏆 Топ по кликам:\n"
    for i, (uid, data) in enumerate(top_clicks, start=1):
        user = await bot.get_chat(uid)
        name = f"@{user.username}" if user.username else user.full_name
        text += f"{i}. {name} — {data['clicks']} кликов\n"

    text += "\n👥 Топ по рефералам:\n"
    for i, (uid, data) in enumerate(top_refs, start=1):
        user = await bot.get_chat(uid)
        name = f"@{user.username}" if user.username else user.full_name
        text += f"{i}. {name} — {data['referrals']} рефералов\n"

    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    await callback.message.edit_text(text, reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data == 'referral')
async def referral_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    link = f"https://t.me/clicker767bot?start={user_id}"  # Вставь юзернейм своего бота
    text = f"🎁 Приглашай друзей по ссылке:\n{link}\n\nЗа каждого друга — 100 кликов!"
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    await callback.message.edit_text(text, reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data == 'back_main')
async def back_main(callback: types.CallbackQuery):
    await callback.message.edit_text("Вы вернулись в главное меню 🏠", reply_markup=get_main_kb())


# ---------- Админка ----------

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
            session['stage'] = 'await_username'
            await message.answer("✅ Пароль верный!\nВведите @юзернейм пользователя, которому хотите выдать клики:")
        else:
            del admin_sessions[uid]
            await message.answer("❌ Неверный пароль!")

    elif session['stage'] == 'await_username':
        if message.text.startswith("@"):
            session['username'] = message.text[1:]
            session['stage'] = 'await_amount'
            await message.answer(f"Сколько кликов выдать @{session['username']}?")
        else:
            await message.answer("❗ Введите юзернейм с @")

    elif session['stage'] == 'await_amount':
        try:
            amount = int(message.text)
            session['amount'] = amount

            # ищем по юзернейму
            for uid_, data in users.items():
                chat = await bot.get_chat(uid_)
                if chat.username == session['username']:
                    users[uid_]['clicks'] += amount
                    await message.answer(f"✅ Выдано {amount} кликов пользователю @{session['username']}")
                    break
            else:
                await message.answer("❌ Пользователь не найден.")

            del admin_sessions[uid]
        except ValueError:
            await message.answer("Введите число кликов.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
