import hashlib
import os
import requests
from bs4 import BeautifulSoup

# ----------------- 監視対象ページの設定 -----------------
# (識別用ラベル, URL) のリスト
TARGET_PAGES = [
    ("トップページ", "https://komiyamaharuka-fc.jp/"),
    ("NEWS", "https://komiyamaharuka-fc.jp/news/all/pages/1"),
    ("SCHEDULE", "https://komiyamaharuka-fc.jp/calendars/2026/9"),
    ("MOVIE", "https://komiyamaharuka-fc.jp/movies/all/pages/1"),
    ("PHOTO", "https://komiyamaharuka-fc.jp/photos/all/pages/1"),
    ("BLOG", "https://komiyamaharuka-fc.jp/blogs/all/pages/1"),
    ("TICKET", "https://komiyamaharuka-fc.jp/tickets/all/pages/1"),
    ("STORE (公式通販)", "https://official-ec.shop/collections/komiyamaharuka-official-store"),
    ("PROFILE", "https://komiyamaharuka-fc.jp/page/6jlWE95pVGZbMeCmWO8N1e"),
]

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
HASH_FILE = "last_hash_komiharu.txt"
# --------------------------------------------------------


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

    # 前回のハッシュ値（各ページぶん）を読み込む
    # 形式: "トップページ:hash1,NEWS:hash2,..."
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

    # 全ページを順番に読み込んでチェック
    for name, url in TARGET_PAGES:
        text = get_page_text(url)
        current_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        current_hashes_list.append(f"{name}:{current_hash}")

        # 前回の記憶がある場合のみ、変化したか比較
        if last_hashes:
            old_hash = last_hashes.get(name, "")
            if old_hash and old_hash != current_hash:
                updated_pages.append((name, url))

    # ハッシュ保存用文字列の作成
    new_hash_string = ",".join(current_hashes_list)

    # 初回実行時
    if not last_hashes:
        print("初回実行：全ページの現在の状態を個別に記憶します。")
        with open(HASH_FILE, "w", encoding="utf-8") as f:
            f.write(new_hash_string)
        return

    # 更新があった場合
    if updated_pages:
        print(f"更新を検知したページ: {[p[0] for p in updated_pages]}")

        # 更新されたページ名を箇条書きにする
        page_list_str = "\n".join([f"・**{name}**" for name, url in updated_pages])
        
        # 1番目に更新されたページのURL（ボタン用）
        first_url = updated_pages[0][1]

        message = (
            f"🔔 **【こみはるオフィシャルサイト更新！】** 🔔\n\n"
            f"以下のページで新しい更新がありました！\n"
            f"{page_list_str}\n\n"
            f"🔗 **更新ページを見に行く**:\n{first_url}"
        )

        send_discord_notification(message)

        # 新しい状態を保存
        with open(HASH_FILE, "w", encoding="utf-8") as f:
            f.write(new_hash_string)
    else:
        print("すべてのページで更新はありませんでした。")


if __name__ == "__main__":
    main()