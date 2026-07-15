import requests
import hashlib
import os
from bs4 import BeautifulSoup

TARGET_URL = "https://hiccorohee.com/updates"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_page_html():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        return response.text if response.status_code == 200 else None
    except:
        return None

def parse_hiccorohee(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    latest_item = soup.find("li")
    
    category = "INFORMATION"
    title = "新しいアップデートがあります"
    link_url = TARGET_URL

    if latest_item:
        text = latest_item.get_text().strip()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if lines:
            title = lines[0]
            for cat in ["information", "column", "schedule", "goods"]:
                if any(cat in line.lower() for line in lines):
                    category = cat.upper()
                    break

        a_tag = latest_item.find("a")
        if a_tag and a_tag.get("href"):
            href = a_tag.get("href")
            if href.startswith("/"):
                link_url = f"https://hiccorohee.com{href}"
            elif href.startswith("http"):
                link_url = href

    return category, title, link_url

def main():
    if not DISCORD_WEBHOOK_URL:
        return

    html = get_page_html()
    if not html:
        return

    category, title, link_url = parse_hiccorohee(html)
    current_state = f"{category}:::{title}"
    current_hash = hashlib.md5(current_state.encode('utf-8')).hexdigest()

    hash_file = "last_hash_hiccorohee.txt"
    last_hash = ""
    if os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            last_hash = f.read().strip()

    if not last_hash:
        with open(hash_file, "w") as f:
            f.write(current_hash)
        return

    if current_hash != last_hash:
        message = (
            f"🏨 **【hotel hiccorohee 更新！】** 🏨\n"
            f"ヒコロヒー公式サイトの updates が更新されました！\n\n"
            f"🏷️ **ジャンル**: {category}\n"
            f"📌 **タイトル**: {title}\n\n"
            f"🔗 **更新ページを開く**:\n{link_url}"
        )
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
        with open(hash_file, "w") as f:
            f.write(current_hash)

if __name__ == "__main__":
    main()