import json
import os
import re
import requests
import webbrowser
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote

# Конфигурация
SAVE_FILE = "search_exclusions.json"
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"  # Путь для Windows
SEARCH_ENGINES = {
    "Brave": "https://search.brave.com/search?q=",
    "DuckDuckGo": "https://duckduckgo.com/html/?q="
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

def load_exclusions():
    """Загружает список исключений из файла."""
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("exclude", [])
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_exclusions(exclusions):
    """Сохраняет список исключений в файл."""
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump({"exclude": exclusions}, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"Ошибка сохранения: {e}")

def add_exclusion(item):
    """Добавляет домен в исключения с нормализацией."""
    domain = re.sub(r"^https?://|/.*$", "", item.strip().lower())
    if not domain:
        return
    
    # Удаляем www и другие субдомены
    domain = re.sub(r"^www\.", "", domain)
    
    exclusions = load_exclusions()
    if domain not in exclusions:
        exclusions.append(domain)
        save_exclusions(exclusions)
        print(f"Добавлено исключение: {domain}")

def is_excluded(url):
    """Проверяет, содержится ли домен URL в исключениях с учетом похожих слов."""
    try:
        hostname = urlparse(url).hostname or ""
        hostname = re.sub(r"^www\.", "", hostname.lower())
        
        # Если URL пустой или невалидный
        if not hostname:
            return False
        
        exclusions = load_exclusions()
        
        # Проверяем точное соответствие или вхождение ключевых слов
        for excluded in exclusions:
            # Точное соответствие домена
            if excluded == hostname:
                return True
                
            # Проверка поддоменов
            if hostname.endswith(f".{excluded}"):
                return True
                
            # Проверка похожих слов (fuzzy match)
            if excluded in hostname:
                # Проверяем, что исключение не является частью другого слова
                pattern = re.compile(rf'\b{re.escape(excluded)}\b')
                if pattern.search(hostname):
                    return True
        
        return False
    except (ValueError, TypeError):
        return False

def extract_real_url(redirect_url):
    """Извлекает настоящий URL из редиректа."""
    if "uddg=" in redirect_url:
        return unquote(redirect_url.split("uddg=")[1].split("&")[0])
    return redirect_url

def search_query(query, max_links=7):
    """Выполняет поиск по нескольким движкам с обработкой исключений."""
    all_links = []
    
    # Разбираем запрос на поисковые слова и исключения
    search_terms = []
    exclusions = []
    
    for term in query.split():
        if term.startswith("-"):
            domain = term[1:].lower()
            add_exclusion(domain)
            exclusions.append(domain)
        else:
            search_terms.append(term)
    
    if not search_terms:
        print("Нет поисковых терминов!")
        return []
    
    clean_query = " ".join(search_terms)
    
    print(f"\nПоиск: {clean_query}")
    if exclusions:
        print(f"Исключения: {', '.join(exclusions)}")
    
    for name, base_url in SEARCH_ENGINES.items():
        try:
            full_url = base_url + clean_query.replace(" ", "+")
            response = requests.get(full_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            response.encoding = "utf-8"

            soup = BeautifulSoup(response.text, "html.parser")
            links = []
            
            # Для Brave
            if name == "Brave":
                for a in soup.select("a.result-header"):
                    href = a.get("href", "")
                    if href.startswith("http"):
                        real_url = extract_real_url(href)
                        links.append(real_url)
            
            # Для DuckDuckGo
            elif name == "DuckDuckGo":
                for a in soup.select("a.result__url"):
                    href = a.get("href", "")
                    if href.startswith("http"):
                        real_url = extract_real_url(href)
                        links.append(real_url)
            
            # Фильтрация исключений
            filtered_links = [link for link in links if not is_excluded(link)]
            
            print(f"\n{name} найдено: {len(links)} ссылок")
            print(f"После фильтрации: {len(filtered_links)} ссылок")
            
            all_links.extend(filtered_links[:max_links])
            
        except requests.RequestException as e:
            print(f"Ошибка {name}: {e}")
    
    # Удаляем дубликаты
    unique_links = []
    for link in all_links:
        if link not in unique_links:
            unique_links.append(link)
    
    return unique_links[:max_links]

def open_in_brave(urls):
    """Открывает ссылки в браузере Brave."""
    try:
        webbrowser.register('brave', None, webbrowser.BackgroundBrowser(BRAVE_PATH))
        browser = webbrowser.get('brave')
        
        print("\nОткрываю в Brave:")
        for i, url in enumerate(urls, 1):
            print(f"{i}. {url}")
            browser.open_new_tab(url)
    except Exception as e:
        print(f"Ошибка открытия Brave: {e}")
        # Попробуем стандартный браузер
        for url in urls:
            webbrowser.open_new_tab(url)

def main():
    """Основной цикл программы."""
    # Инициализация
    print("Расширенный поиск с системой исключений")
    print("Используйте '-' перед доменом для исключения (пример: -youtube)")
    print("Введите 'выход' для завершения\n")
    
    # Загружаем существующие исключения
    exclusions = load_exclusions()
    if exclusions:
        print(f"Текущие исключения: {', '.join(exclusions)}")
    
    while True:
        try:
            query = input("\nПоисковый запрос: ").strip()
            if query.lower() in ["выход", "exit", "quit"]:
                break
                
            if not query:
                continue
                
            results = search_query(query)
            
            if results:
                open_in_brave(results)
            else:
                print("Нет результатов для отображения")
                
        except KeyboardInterrupt:
            print("\nЗавершение работы...")
            break
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
