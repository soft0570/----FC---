import hashlib
import os
import requests
from bs4 import BeautifulSoup

# ----------------- 監視対象ページの設定（ポケモンGO フレンド） -----------------
TARGET_PAGES = [
    ("アラブ首長国連邦 (AE)", "https://pokemongo.gishan.net/friends/codes/ae-ja"),
    ("サウジアラビア (SA)", "https://pokemongo.gishan.net/friends/codes/sa-ja"),
    ("カタール (QA)", "https://pokemongo.gishan.net/friends/codes/qa-ja"),
    ("オマーン (OM)", "https://pokemongo.gishan.net/friends/codes/om-ja"),
    ("クウェート (KW)", "https://pokemongo.gishan.net/friends/codes/kw-ja"),
    ("バーレーン (BH)", "https://pokemongo.gishan.net/friends/codes/bh-ja"),
    ("イスラエル (IL)", "https://pokemongo.gishan.net/friends/codes/il-ja"),
    ("ヨルダン (JO)", "https://pokemongo.gishan.net/friends/codes/jo-ja"),
    ("イラク (IQ)", "https://pokemongo.gishan.net/friends/codes/iq-ja"),
]

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
HASH_FILE = "last_hash_pokemongo.txt"
# ------------------------------------------------------------------------------


def get_page_text(url):
    """指定されたURLの主要テキストを取得する"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.encoding = "utf-8"
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for script in soup(["script", "style", "header", "footer", "nav"]):
                script.extract()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            return "\n".join(chunk for chunk in chunks if chunk)
    except Exception as e:
        print(f"URL取得失敗 ({url}): {e}")
    return ""


def send_discord_notification(message):
    payload = {"content": message}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"Discord通知失敗: {e}")


def main():
    if not DISCORD_WEBHOOK_URL:
        print("エラー: DISCORD_WEBHOOK_URL が設定されていません。")
        return

    # 前回のハッシュ値を読み込む
    last_hashes = {}
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                for item in content.split(","):
                    if ":" in item:
                        name, h = item.split(":", 1)
                        last_hashes[name] = h

    updated_pages = []
    current_hashes_list = []

    for name, url in TARGET_PAGES:
        text = get_page_text(url)
        current_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        current_hashes_list.append(f"{name}:{current_hash}")

        if last_hashes:
            old_hash = last_hashes.get(name, "")
            if old_hash and old_hash != current_hash:
                updated_pages.append((name, url))

    new_hash_string = ",".join(current_hashes_list)

    # 初回実行時
    if not last_hashes:
        print("初回実行：全ページの現在の状態を記憶します。")
        with open(HASH_FILE, "w", encoding="utf-8") as f:
            f.write(new_hash_string)
        return

    # 更新があった場合
    if updated_pages:
        print(f"更新を検知したページ: {[p[0] for p in updated_pages]}")

        for name, url in updated_pages:
            message = (
                f"🎮 **【ポケモンGO フレンド募集更新】** 🎮\n\n"
                f"国・地域: **{name}** のページで新しい更新がありました！\n\n"
                f"🔗 **ページを見に行く**:\n{url}"
            )
            send_discord_notification(message)

        # 新しい状態を保存
        with open(HASH_FILE, "w", encoding="utf-8") as f:
            f.write(new_hash_string)
    else:
        print("すべてのポケモンGOページで更新はありませんでした。")


if __name__ == "__main__":
    main()