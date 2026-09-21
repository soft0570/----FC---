import hashlib
import os
import requests
from bs4 import BeautifulSoup

# ----------------- 設定 -----------------
TARGET_URL = "https://ticketdive.com/artist/ezaITEnPrW6rg8gewAfe"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
HASH_FILE = "last_hash_ticketdive.txt"
# ----------------------------------------


def get_page_html():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.encoding = "utf-8"
        if response.status_code == 200:
            return response.text
        return None
    except requests.RequestException as e:
        print(f"通信エラー: {e}")
        return None


def parse_latest_info(html_content):
    """TicketDiveのページから本文テキスト全体を抽出する."""
    soup = BeautifulSoup(html_content, "html.parser")

    # スクリプトやスタイルなどの不要タグを完全排除
    for script in soup(["script", "style", "header", "footer", "nav"]):
        script.extract()

    # ページ内の文字をすべて取り出し、改行やスペースをきれいに整形
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    clean_text = "\n".join(chunk for chunk in chunks if chunk)

    return clean_text


def send_discord_notification(message):
    payload = {"content": message}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"Notification failed: {e}")


def main():
    if not DISCORD_WEBHOOK_URL:
        print("エラー: DiscordのWebhook URLが設定されていません。")
        return

    html_content = get_page_html()
    if not html_content:
        print("ページの取得に失敗しました。")
        return

    latest_text = parse_latest_info(html_content)
    if not latest_text.strip():
        print("テキストの抽出に失敗しました。")
        return

    current_hash = hashlib.md5(latest_text.encode("utf-8")).hexdigest()

    last_hash = ""
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            last_hash = f.read().strip()

    if not last_hash:
        print("初回実行：TicketDiveの現在の状態を保存します。")
        with open(HASH_FILE, "w", encoding="utf-8") as f:
            f.write(current_hash)
        return

    if current_hash != last_hash:
        print("TicketDiveの更新を検知！")

        message = (
            f"🎫 **【TicketDive 更新検知！】** 🎫\n"
            f"アーティストページでイベント情報やチケットの更新が検出されました！\n\n"
            f"🔗 **チケットページを開く**:\n{TARGET_URL}"
        )

        send_discord_notification(message)

        with open(HASH_FILE, "w", encoding="utf-8") as f:
            f.write(current_hash)
    else:
        print("TicketDiveに更新はありませんでした。")


if __name__ == "__main__":
    main()