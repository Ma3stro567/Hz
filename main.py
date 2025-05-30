import requests
from bs4 import BeautifulSoup

def get_stock():
    url = 'https://www.vulcanvalues.com/grow-a-garden/stock'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Сайт вернул статус {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    blocks = soup.find_all('div', class_='stock-block')

    if not blocks:
        raise Exception("Не найдены блоки с классом 'stock-block'. Вероятно, сайт изменился.")

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

def main():
    print("🔍 Тест парсера запущен...")
    try:
        stock = get_stock()
        if stock:
            print("\n✅ Получен сток:\n")
            print(stock)
        else:
            print("⚠️ Ничего не найдено. Вероятно, структура сайта изменилась.")
    except Exception as e:
        print("❌ Ошибка при получении стока:", e)

if __name__ == '__main__':
    main()
    
