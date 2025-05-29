import requests
from bs4 import BeautifulSoup
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from datetime import datetime
import time
import os

# ==== НАСТРОЙКИ ====
TELEGRAM_BOT_TOKEN = '7707125232:AAETPJkoA5RwFyYV5edq-nO11cR0hrJA4Sk'
CHECK_INTERVAL_SECONDS = 1
USERS_FILE = "users.txt"

# ==== ХРАНЕНИЕ ПОЛЬЗОВАТЕЛЕЙ ====
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return set(map(int, f.read().splitlines()))
    except:
        return set()

def save_users(users):
    with open(USERS_FILE, "w") as f:
        for user_id in users:
            f.write(str(user_id) + "\n")

users = load_users()

# ==== ОБРАБОТЧИК /start ====
def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id not in users:
        users.add(chat_id)
        save_users(users)
        print(f"➕ Новый пользователь: {chat_id}")
    context.bot.send_message(chat_id=chat_id, text="✅ Вы подписались на уведомления!")

# ==== ПАРСИНГ ====
def get_stock():
    url = 'https://www.vulcanvalues.com/grow-a-garden/stock'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    blocks = soup.find_all('div', class_='stock-block')
    stock_text = []

    for block in blocks:
        title = block.find('h2')
        items = block.find_all('li')
        if title and items:
            title_text = title.get_text(strip=True)
            item_lines = [f"• {li.get_text(strip=True)}" for li in items]
            block_text = f"🛒 {title_text}:\n" + "\n".join(item_lines)
            stock_text.append(block_text)

    return "\n\n".join(stock_text)

# ==== ОТПРАВКА СООБЩЕНИЙ ====
def send_telegram_message(text):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    for user_id in users:
        try:
            bot.send_message(chat_id=user_id, text=text)
            print(f"✅ Сообщение отправлено: {user_id}")
        except Exception as e:
            print(f"❌ Ошибка отправки пользователю {user_id}: {e}")

# ==== ОЖИДАНИЕ ВРЕМЕНИ ====
def wait_for_exact_5_minute_mark():
    while True:
        now = datetime.now()
        if now.minute % 5 == 0 and now.second == 0:
            break
        time.sleep(CHECK_INTERVAL_SECONDS)

# ==== ОСНОВНОЙ ЦИКЛ ====
def main():
    global users
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.start_polling()
    print("🤖 Бот запущен.")
    
    last_sent = ""

    while True:
        wait_for_exact_5_minute_mark()
        try:
            stock = get_stock()
            if stock and stock != last_sent:
                now = datetime.now().strftime("%H:%M")
                send_telegram_message(f"🕒 {now} — Обновлённый сток Grow a Garden:\n\n{stock}")
                last_sent = stock
        except Exception as e:
            print("❌ Ошибка:", e)

        time.sleep(1)

if __name__ == '__main__':
    main()
    
