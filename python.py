import requests
import webbrowser
from bs4 import BeautifulSoup
from urllib.parse import unquote

SEARCH_ENGINES = {
    "DuckDuckGo": "https://duckduckgo.com/html/?q=",
    "Brave": "https://search.brave.com/search?q="
}

# Путь к браузеру Brave, указывай свой путь, если он отличается
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"  # Для Windows

def extract_real_url(redirect_url):
    """ Извлекает реальный URL из редиректа. """
    if "uddg=" in redirect_url:
        return unquote(redirect_url.split('uddg=')[1])  # Извлекаем реальный URL
    return redirect_url

def search_query(query):
    results = {}
    for name, url in SEARCH_ENGINES.items():
        full_url = url + query.replace(" ", "+")
        try:
            headers = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip, deflate"}
            response = requests.get(full_url, headers=headers, timeout=5)
            response.encoding = "utf-8"
            
            soup = BeautifulSoup(response.text, "html.parser")
            links = set(a["href"] for a in soup.find_all("a", href=True) if "http" in a["href"])
            
            # Извлекаем реальные URL из редиректов
            results[name] = [extract_real_url(link) for link in links][:5]
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе к {name}: {e}")
    return results

def open_in_brave(url):
    # Настроим webbrowser для открытия через Brave
    webbrowser.register('brave', None, webbrowser.BackgroundBrowser(BRAVE_PATH))
    webbrowser.get('brave').open(url)

def main():
    while True:
        query = input("Введите запрос (или 'выход' для завершения): ").strip()
        if query.lower() == "выход":
            print("Выход из программы.")
            break

        results = search_query(query)
        for engine, links in results.items():
            print(f"\n{engine} результаты:")
            for link in links:
                print(link)
                open_in_brave(link)  # Открываем каждую ссылку в новой вкладке Brave

if __name__ == "__main__":
    main()
а
