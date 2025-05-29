import requests
from bs4 import BeautifulSoup
from telegram import Bot
from datetime import datetime
import time

# ==== НАСТРОЙКИ ====
TELEGRAM_BOT_TOKEN = '7707125232:AAETPJkoA5RwFyYV5edq-nO11cR0hrJA4Sk'
TELEGRAM_CHAT_IDS = [
    '5083696616',  # сюда добавляй ID других пользователей, если надо
    # '123456789',
    # '987654321',
]
CHECK_INTERVAL_SECONDS = 1  # каждую секунду проверяет время

# ==== ФУНКЦИИ ====

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

def send_telegram_message(text):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Ошибка при отправке в чат {chat_id}: {e}")

def wait_for_exact_5_minute_mark():
    while True:
        now = datetime.now()
        if now.minute % 5 == 0 and now.second == 0:
            break
        time.sleep(CHECK_INTERVAL_SECONDS)

# ==== ОСНОВНОЙ ЦИКЛ ====

def main():
    print("✅ Бот запущен.")
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
    
