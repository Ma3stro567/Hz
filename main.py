# Готовый файл main.py для Telegram-бота со стоком и мультиюзером (совместим с Termux и python-telegram-bot 13.15)
import requests
from bs4 import BeautifulSoup
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from datetime import datetime
import time
import cloudscraper

# ==== НАСТРОЙКИ ====
TELEGRAM_BOT_TOKEN = '7707125232:AAEwvQmsDCl-qxxKbz1xwnNWEOlY6NRs7gs'  # ← ВСТАВЬ СВОЙ ТОКЕН ОТ BotFather
AUTHORIZED_USERS = set()  # Множество для хранения ID подписанных пользователей

# ==== ФУНКЦИИ ====

def get_stock():
    """Парсит сток с vulkanvalues.com"""
    try:
        url = 'https://www.vulcanvalues.com/grow-a-garden/stock'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        blocks = soup.find_all('div', class_='stock-block')
        stock_text = []

        for block in blocks:
            title = block.find('h2')
            items = block.find_all('li')
            if title and items:
                title_text = title.get_text(strip=True)
                item_lines = [f"• {li.get_text(strip=True)}" for li in items]
                block_text = f"🛒 {title_text}:\n" + "\\n".join(item_lines)
                stock_text.append(block_text)

        return "\\n\\n".join(stock_text)
    except Exception as e:
        return f"⚠️ Ошибка при получении стока: {e}"

def send_stock_to_users(context: CallbackContext):
    """Отправляет сток всем подписанным пользователям"""
    stock = get_stock()
    now = datetime.now().strftime("%H:%M")
    message = f"🕒 {now} — Обновлённый сток Grow a Garden:\\n\\n{stock}"
    for user_id in AUTHORIZED_USERS:
        context.bot.send_message(chat_id=user_id, text=message)

def start(update: Update, context: CallbackContext):
    """/start — подписка"""
    user_id = update.effective_user.id
    AUTHORIZED_USERS.add(user_id)
    update.message.reply_text("✅ Ты подписан на обновления стока Grow a Garden.")

def stop(update: Update, context: CallbackContext):
    """/stop — отписка"""
    user_id = update.effective_user.id
    AUTHORIZED_USERS.discard(user_id)
    update.message.reply_text("❌ Ты отписался от обновлений.")

def status(update: Update, context: CallbackContext):
    """/status — показать текущий сток"""
    stock = get_stock()
    now = datetime.now().strftime("%H:%M")
    update.message.reply_text(f"🕒 {now} — Текущий сток:\\n\\n{stock}")

# ==== ЗАПУСК ====

def main():
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Команды
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stop", stop))
    dispatcher.add_handler(CommandHandler("status", status))

    updater.start_polling()

    # Задача каждые 5 минут
    job_queue = updater.job_queue
    job_queue.set_dispatcher(dispatcher)
    job_queue.start()
    job_queue.run_repeating(send_stock_to_users, interval=300, first=0)

    updater.idle()

if __name__ == '__main__':
    main()
    
