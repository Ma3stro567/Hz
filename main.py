import requests
from bs4 import BeautifulSoup
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from datetime import datetime
import time
import threading

# ==== НАСТРОЙКИ ====
TELEGRAM_BOT_TOKEN = '7707125232:AAGbQ21HnQg3DKd3pRjvaoStBt9Azlql6XE'  # ← вставь свой токен от BotFather
AUTHORIZED_USERS = set()  # Множество для хранения ID авторизованных пользователей

# ==== ФУНКЦИИ ====

def get_stock():
    """Парсит сток с vulkanvalues.com"""
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

def send_stock_to_users(context: CallbackContext):
    """Отправляет сток всем авторизованным пользователям"""
    stock = get_stock()
    now = datetime.now().strftime("%H:%M")
    message = f"🕒 {now} — Обновлённый сток Grow a Garden:\n\n{stock}"
    for user_id in AUTHORIZED_USERS:
        context.bot.send_message(chat_id=user_id, text=message)

def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    AUTHORIZED_USERS.add(user_id)
    update.message.reply_text("Привет! Ты подписан на обновления стока Grow a Garden.")

def stop(update: Update, context: CallbackContext):
    """Обработчик команды /stop"""
    user_id = update.effective_user.id
    AUTHORIZED_USERS.discard(user_id)
    update.message.reply_text("Ты отписался от обновлений стока.")

def main():
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Обработчики команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stop", stop))

    # Запуск бота
    updater.start_polling()

    # Запуск задачи по расписанию
    job_queue = updater.job_queue
    job_queue.run_repeating(send_stock_to_users, interval=300, first=0)  # Каждые 5 минут

    updater.idle()

if __name__ == '__main__':
    main()
    
