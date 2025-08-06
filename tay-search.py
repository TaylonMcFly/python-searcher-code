import json
import os
import re
import requests
import webbrowser
import random
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote, quote_plus

# Configuration
SAVE_FILE = "search_exclusions.json"
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"  # Windows path
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
]
SEARCH_ENGINES = {
    "Brave": "https://search.brave.com/search?q={query}&source=web",
    "DuckDuckGo": "https://html.duckduckgo.com/html/?q={query}",
    "Yandex": "https://yandex.com/search/?text={query}",
    "Startpage": "https://www.startpage.com/sp/search?query={query}",
    "Qwant": "https://www.qwant.com/?q={query}"
}

def load_exclusions():
    """Load exclusion list from file."""
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("exclude", [])
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_exclusions(exclusions):
    """Save exclusion list to file."""
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump({"exclude": exclusions}, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"Save error: {e}")

def add_exclusion(item):
    """Add domain to exclusions with normalization."""
    domain = re.sub(r"^https?://|/.*$", "", item.strip().lower())
    if not domain:
        return
    
    # Remove www and subdomains
    domain = re.sub(r"^www\.", "", domain)
    
    exclusions = load_exclusions()
    if domain not in exclusions:
        exclusions.append(domain)
        save_exclusions(exclusions)
        print(f"Added exclusion: {domain}")

def is_excluded(url):
    """Check if URL domain is in exclusions with fuzzy matching."""
    try:
        hostname = urlparse(url).hostname or ""
        hostname = re.sub(r"^www\.", "", hostname.lower())
        
        if not hostname:
            return False
        
        exclusions = load_exclusions()
        
        # Check for exact match or keyword inclusion
        for excluded in exclusions:
            # Exact domain match
            if excluded == hostname:
                return True
                
            # Subdomain check
            if hostname.endswith(f".{excluded}"):
                return True
                
            # Fuzzy word matching
            if excluded in hostname:
                pattern = re.compile(rf'\b{re.escape(excluded)}\b')
                if pattern.search(hostname):
                    return True
        
        return False
    except (ValueError, TypeError):
        return False

def extract_real_url(redirect_url):
    """Extract real URL from redirect."""
    if "uddg=" in redirect_url:
        return unquote(redirect_url.split("uddg=")[1].split("&")[0])
    elif "url=" in redirect_url:
        return unquote(redirect_url.split("url=")[1].split("&")[0])
    return redirect_url

def get_random_headers():
    """Return random headers to bypass blocks."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.google.com/",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "TE": "trailers"
    }

def search_rare_sites(query, max_links=10):
    """Search for rare sites with unusual URL characters."""
    # Generate special queries for finding rare sites
    special_queries = [
        f'"{query}" site:*.onion',
        f'"{query}" inurl:特殊字符',
        f'"{query}" intitle:深网',
        f'"{query}" filetype:onion',
        f'"{query}" site:*.i2p',
        f'"{query}" "hidden wiki"',
        f'"{query}" "uncensored directory"',
        f'"{query}" "deep web links"',
        f'"{query}" "rare sites"',
        f'"{query}" "unusual domains"'
    ]
    
    all_links = []
    for special_query in special_queries:
        try:
            # Search different engines
            for engine, base_url in SEARCH_ENGINES.items():
                full_url = base_url.format(query=quote_plus(special_query))
                
                # Delay to avoid blocking
                time.sleep(random.uniform(1, 3))
                
                response = requests.get(
                    full_url, 
                    headers=get_random_headers(),
                    timeout=15
                )
                response.encoding = "utf-8"
                
                # Parse results based on search engine
                soup = BeautifulSoup(response.text, "html.parser")
                links = []
                
                # Brave
                if engine == "Brave":
                    for a in soup.select("a.result-header"):
                        href = a.get("href", "")
                        if href.startswith("http"):
                            real_url = extract_real_url(href)
                            links.append(real_url)
                
                # DuckDuckGo
                elif engine == "DuckDuckGo":
                    for a in soup.select("a.result__url"):
                        href = a.get("href", "")
                        if href.startswith("http"):
                            real_url = extract_real_url(href)
                            links.append(real_url)
                
                # Yandex
                elif engine == "Yandex":
                    for a in soup.select("a.Link.OrganicTitle-Link"):
                        href = a.get("href", "")
                        if href.startswith("/"):
                            href = "https://yandex.com" + href
                        if href.startswith("http"):
                            real_url = extract_real_url(href)
                            links.append(real_url)
                
                # Startpage
                elif engine == "Startpage":
                    for a in soup.select("a.w-gl__result-title"):
                        href = a.get("href", "")
                        if href.startswith("http"):
                            links.append(href)
                
                # Qwant
                elif engine == "Qwant":
                    for a in soup.select("a.result-title"):
                        href = a.get("href", "")
                        if href.startswith("http"):
                            links.append(href)
                
                # Filter and add unique links
                for link in links:
                    if (link not in all_links and 
                        not is_excluded(link) and
                        re.search(r'[^\w\-\.:/]', link)):
                        all_links.append(link)
                        if len(all_links) >= max_links:
                            return all_links
                
        except Exception as e:
            print(f"Error searching '{special_query}': {e}")
    
    return all_links[:max_links]

def search_query(query, max_links=15):
    """Search multiple engines with exclusion handling."""
    all_links = []
    search_terms = []
    exclusions = []
    
    # Handle special commands
    if query.startswith("!rare "):
        return search_rare_sites(query[6:], max_links)
    
    # Parse query for search terms and exclusions
    for term in query.split():
        if term.startswith("-"):
            domain = term[1:].lower()
            add_exclusion(domain)
            exclusions.append(domain)
        else:
            search_terms.append(term)
    
    if not search_terms:
        print("No search terms!")
        return []
    
    clean_query = " ".join(search_terms)
    
    print(f"\nSearching: {clean_query}")
    if exclusions:
        print(f"Exclusions: {', '.join(exclusions)}")
    
    # Search different engines
    for engine, base_url in SEARCH_ENGINES.items():
        try:
            full_url = base_url.format(query=quote_plus(clean_query))
            
            # Delay to avoid blocking
            time.sleep(random.uniform(1, 3))
            
            response = requests.get(
                full_url, 
                headers=get_random_headers(),
                timeout=15
            )
            response.encoding = "utf-8"

            # Parse results
            soup = BeautifulSoup(response.text, "html.parser")
            links = []
            
            # Brave
            if engine == "Brave":
                for a in soup.select("a.result-header"):
                    href = a.get("href", "")
                    if href.startswith("http"):
                        real_url = extract_real_url(href)
                        links.append(real_url)
            
            # DuckDuckGo
            elif engine == "DuckDuckGo":
                for a in soup.select("a.result__url"):
                    href = a.get("href", "")
                    if href.startswith("http"):
                        real_url = extract_real_url(href)
                        links.append(real_url)
            
            # Yandex
            elif engine == "Yandex":
                for a in soup.select("a.Link.OrganicTitle-Link"):
                    href = a.get("href", "")
                    if href.startswith("/"):
                        href = "https://yandex.com" + href
                    if href.startswith("http"):
                        real_url = extract_real_url(href)
                        links.append(real_url)
            
            # Startpage
            elif engine == "Startpage":
                for a in soup.select("a.w-gl__result-title"):
                    href = a.get("href", "")
                    if href.startswith("http"):
                        links.append(href)
            
            # Qwant
            elif engine == "Qwant":
                for a in soup.select("a.result-title"):
                    href = a.get("href", "")
                    if href.startswith("http"):
                        links.append(href)
            
            # Exclusion filtering
            filtered_links = [link for link in links if not is_excluded(link)]
            
            print(f"\n{engine} found: {len(links)} links")
            print(f"After filtering: {len(filtered_links)} links")
            
            # Add unique links
            for link in filtered_links:
                if link not in all_links:
                    all_links.append(link)
                    if len(all_links) >= max_links:
                        break
            
            if len(all_links) >= max_links:
                break
                
        except Exception as e:
            print(f"{engine} error: {e}")
    
    return all_links[:max_links]

def open_in_brave(urls):
    """Open links in Brave browser."""
    try:
        webbrowser.register('brave', None, webbrowser.BackgroundBrowser(BRAVE_PATH))
        browser = webbrowser.get('brave')
        
        print("\nOpening in Brave:")
        for i, url in enumerate(urls, 1):
            print(f"{i}. {url}")
            browser.open_new_tab(url)
    except Exception as e:
        print(f"Brave open error: {e}")
        # Fallback to default browser
        for url in urls:
            webbrowser.open_new_tab(url)

def main():
    """Main program loop."""
    # Initialization
    print("🔥 DeepFinder Search Engine 🔥")
    print("🔍 Finds hidden and rare websites")
    print("✋ Use '-' prefix to exclude domains (e.g., -youtube)")
    print("💎 Search rare sites with: !rare your_query")
    print("🚫 Current exclusions:", ", ".join(load_exclusions()) or "none")
    
    while True:
        try:
            query = input("\n🌐 Enter search query: ").strip()
            if query.lower() in ["exit", "quit"]:
                break
                
            if not query:
                continue
                
            # Special rare site search
            if query.startswith("!rare"):
                results = search_rare_sites(query[6:])
                print(f"\n🔎 Found {len(results)} rare sites:")
            else:
                results = search_query(query)
                print(f"\n🔎 Found {len(results)} results:")
                
            for i, url in enumerate(results, 1):
                print(f"{i}. {url}")
                
            if results:
                open_in_brave(results)
            else:
                print("😢 No results found")
                
        except KeyboardInterrupt:
            print("\n🛑 Exiting...")
            break
        except Exception as e:
            print(f"🚨 Critical error: {e}")

if __name__ == "__main__":
    main()
