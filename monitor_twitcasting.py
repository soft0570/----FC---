import hashlib
import os
import requests
from bs4 import BeautifulSoup

# ----------------- 設定 -----------------
TARGET_URL = "https://twitcasting.tv/912_komiharu/shop"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
HASH_FILE = "last_hash_twitcasting.txt"
# ----------------------------------------


def get_page_text():
    """ツイキャスショップページの主要テキストを取得する"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        res = requests.get(TARGET_URL, headers=headers, timeout=15)
        res.encoding = "utf-8"
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")

            # 不要なスクリプト、スタイル、ヘッダー・フッターを除外
            for script in soup(["script", "style", "header", "footer", "nav"]):
                script.extract()

            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (
                phrase.strip()
                for line in lines
                for phrase in line.split("  ")
            )
            return "\n".join(chunk for chunk in chunks if chunk)
    except Exception as e:
        print(f"URL取得失敗 ({TARGET_URL}): {e}")
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

    # 最新テキストを取得
    current_text = get_page_text()
    if not current_text.strip():
        print("ツイキャスショップのテキスト取得に失敗しました。")
        return

    current_hash = hashlib.md5(current_text.encode("utf-8")).hexdigest()

    # 前回のハッシュ値を読み込み
    last_hash = ""
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            last_hash = f.read().strip()

    # 初回実行時
    if not last_hash:
        print(
            "初回実行：ツイキャスショップの現在の状態を記憶します。"
        )
        with open(HASH_FILE, "w", encoding="utf-8") as f:
            f.write(current_hash)
        return

    # 更新があった場合
    if current_hash != last_hash:
        print("ツイキャスショップで更新を検知！")

        message = (
            f"📹 **【込山榛香 ツイキャスショップ更新！】** 📹\n"
            f"キャスマーケットで新しい配信イベントやチケットの更新が検知されました！\n\n"
            f"🔗 **ショップページを開く**:\n{TARGET_URL}"
        )

        send_discord_notification(message)

        # 新しい状態を保存
        with open(HASH_FILE, "w", encoding="utf-8") as f:
            f.write(current_hash)
    else:
        print("ツイキャスショップに更新はありませんでした。")


if __name__ == "__main__":
    main()