import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import json

RSS_FILE = 'suno_trending.xml'
SEEN_FILE = 'seen.json'

def load_seen():
    try:
        with open(SEEN_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(seen), f, ensure_ascii=False)

def parse_trending():
    url = 'https://suno.com/trending'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return []

    soup = BeautifulSoup(r.text, 'html.parser')
    seen = load_seen()
    new_tracks = []

    rows = soup.find_all('div', attrs={'data-testid': 'song-row'})
    if not rows:
        print("Не найдено строк")
        return []

    for row in rows:
        link_tag = row.find('a', href=lambda h: h and '/song/' in h)
        if not link_tag:
            continue
        link = 'https://suno.com' + link_tag['href']
        if link in seen:
            continue

        title_tag = row.find('span', class_='line-clamp-1')
        title = title_tag.get_text(strip=True) if title_tag else 'Без названия'

        author_tag = row.find('a', href=lambda h: h and '/@' in h)
        author = author_tag.get_text(strip=True) if author_tag else 'Аноним'

        new_tracks.append({
            'title': title,
            'author': author,
            'link': link,
            'date': datetime.utcnow().isoformat()
        })
        seen.add(link)

    save_seen(seen)
    return new_tracks

def generate_rss(tracks):
    if not tracks:
        return
    fg = FeedGenerator()
    fg.title('Новые треки Suno Trending')
    fg.link(href='https://suno.com/trending', rel='alternate')
    fg.description('Авто-лента новых треков с Suno')

    for t in tracks:
        fe = fg.add_entry()
        fe.id(t['link'])
        fe.title(f"{t['title']} — {t['author']}")
        fe.link(href=t['link'], rel='alternate')
        fe.description(f"Автор: {t['author']}<br>Ссылка: <a href='{t['link']}'>Слушать</a><br>Дата: {t['date']}")
        fe.published(t['date'])

    fg.rss_file(RSS_FILE)
    print(f"Добавлено {len(tracks)} новых")

if __name__ == '__main__':
    new_tracks = parse_trending()
    generate_rss(new_tracks)
