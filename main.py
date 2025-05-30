import cloudscraper
from bs4 import BeautifulSoup
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from datetime import datetime
import logging

# ========== НАСТРОЙКИ ==========
TOKEN = '7707125232:AAHEv3B271Vzcif1iypqzKHAIqQqDU4F58A'
AUTHORIZED_USERS = set()

# ========== ЛОГГЕР ==========
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ========== СТОК ==========
def get_stock():
    scraper = cloudscraper.create_scraper()
    url = 'https://www.vulcanvalues.com/grow-a-garden/stock'
    res = scraper.get(url)

    soup = BeautifulSoup(res.text, 'html.parser')
    blocks = soup.find_all('div', class_='stock-block')

    all_stock = []
    for block in blocks:
        title = block.find('h2')
        items = block.find_all('li')
        if title and items:
            item_list = [f"• {li.get_text(strip=True)}" for li in items]
            all_stock.append(f"🛒 {title.get_text(strip=True)}:\n" + "\n".join(item_list))

    return "\n\n".join(all_stock) if all_stock else "❗ Сток не найден."

# ========== ОБРАБОТЧИКИ ==========
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    AUTHORIZED_USERS.add(user_id)
    update.message.reply_text("✅ Ты подписан на уведомления о стоке.")

def stop(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    AUTHORIZED_USERS.discard(user_id)
    update.message.reply_text("❌ Ты отписался от уведомлений.")

def send_stock(context: CallbackContext):
    now = datetime.now().strftime("%H:%M")
    stock = get_stock()
    message = f"🕒 {now} — Текущий сток:\n\n{stock}"
    for uid in AUTHORIZED_USERS:
        context.bot.send_message(chat_id=uid, text=message)

# ========== MAIN ==========
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stop", stop))

    # Расписание каждые 5 минут
    job_queue = updater.job_queue
    job_queue.run_repeating(send_stock, interval=300, first=0)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
    
