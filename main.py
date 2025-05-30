import cloudscraper
from bs4 import BeautifulSoup

def get_stock():
    url = 'https://www.vulcanvalues.com/grow-a-garden/stock'
    scraper = cloudscraper.create_scraper()
    
    print("🌐 Отправка запроса через Cloudscraper...")
    response = scraper.get(url)
    
    print(f"📶 Статус-код ответа: {response.status_code}")
    if response.status_code != 200:
        raise Exception(f"Ошибка: Статус код {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    blocks = soup.find_all('div', class_='stock-block')
    
    print(f"🔍 Найдено блоков с классом 'stock-block': {len(blocks)}")
    
    if not blocks:
        print("⚠️ Блоки не найдены. Проверь HTML-структуру вручную.")
        print("📄 Начало ответа сервера:")
        print(response.text[:500])
        return ""

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
    print("🧪 Тест парсера с Cloudscraper")
    try:
        stock = get_stock()
        if stock:
            print("✅ Получен сток:\n")
            print(stock)
        else:
            print("⚠️ Сток пуст или не найден.")
    except Exception as e:
        print("❌ Ошибка при получении стока:", e)

if __name__ == '__main__':
    main()
    
