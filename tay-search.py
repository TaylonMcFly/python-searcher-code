import requests
import webbrowser
from bs4 import BeautifulSoup
from urllib.parse import unquote

SEARCH_ENGINES = {
    "DuckDuckGo": "https://duckduckgo.com/html/?q=",
    "Brave": "https://search.brave.com/search?q="
}

BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"  # Windows

def extract_real_url(redirect_url):
    if "uddg=" in redirect_url:
        return unquote(redirect_url.split("uddg=")[1].split("&")[0])
    return redirect_url

def search_query(query, max_links=5):
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip, deflate"}
    results = {}
    for name, base_url in SEARCH_ENGINES.items():
        try:
            full_url = base_url + query.replace(" ", "+")
            response = requests.get(full_url, headers=headers, timeout=5)
            response.encoding = "utf-8"

            soup = BeautifulSoup(response.text, "html.parser")
            anchors = soup.find_all("a", href=True)
            links = []
            for a in anchors:
                href = a["href"]
                if href.startswith("http"):
                    real_url = extract_real_url(href)
                    if real_url not in links:
                        links.append(real_url)
                if len(links) >= max_links:
                    break

            results[name] = links
        except requests.RequestException as e:
            print(f"Ошибка при запросе к {name}: {e}")
            results[name] = []
    return results

def open_in_brave(urls):
    webbrowser.register('brave', None, webbrowser.BackgroundBrowser(BRAVE_PATH))
    browser = webbrowser.get('brave')
    for url in urls:
        browser.open_new_tab(url)

def main():
    while True:
        query = input("Введите запрос (или 'выход' для завершения): ").strip()
        if query.lower() == "выход":
            break

        results = search_query(query)
        for engine, links in results.items():
            print(f"\n{engine} результаты:")
            for link in links:
                print(link)
            if links:
                open_in_brave(links)

if __name__ == "__main__":
    main()
