from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time

visited = set()
results=[]

def scrape_page(page, url):
    page.goto(url,timeout=60000)
    page.wait_for_selector("body")
    time.sleep(5)  # Let JS fully render

    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(separator='\n', strip=True)
    print(f"\n\n========= {url} =========\n{text[:500]}...")  # Preview only

    links = set()
    for a in soup.find_all("a", href=True):
        href = a['href']
        full_url = urljoin(url, href)
        if is_internal_link(url, full_url):
            links.add(full_url)

    return links,text

def is_internal_link(base, link):
    return urlparse(base).netloc == urlparse(link).netloc

def crawl(start_url, max_depth=1):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = context.new_page()
        to_visit = [(start_url, 0)]

        while to_visit:
            current_url, depth = to_visit.pop(0)
            if current_url in visited or depth > max_depth:
                continue
            visited.add(current_url)

            try:
                new_links,text = scrape_page(page, current_url)
                results.append({
                    "url":current_url,
                    "text":text
                })
                to_visit.extend((link, depth+1) for link in new_links if link not in visited)
            except Exception as e:
                print(f"Failed on {current_url}: {e}")
        browser.close()
    return results    

