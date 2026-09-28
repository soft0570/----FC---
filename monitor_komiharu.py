import difflib
import os
import requests
from bs4 import BeautifulSoup

# ----------------- 監視対象ページの設定 -----------------
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
TEXT_DIR = "last_texts_komiharu"  # 前回のテキスト保存先フォルダ
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


def get_text_diff(old_text, new_text):
    """前後のテキスト差分（追加行・削除行）を取得する"""
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    diff = difflib.unified_diff(old_lines, new_lines, lineterm="")
    added = []
    removed = []

    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            content = line[1:].strip()
            if content:
                added.append(content)
        elif line.startswith("-") and not line.startswith("---"):
            content = line[1:].strip()
            if content:
                removed.append(content)

    return added, removed


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

    # テキスト保存用フォルダの作成
    os.makedirs(TEXT_DIR, exist_ok=True)

    is_first_run = False
    updated_info = []  # (ページ名, URL, 追加行, 削除行)

    for name, url in TARGET_PAGES:
        current_text = get_page_text(url)
        if not current_text:
            continue

        # 各ページ専用のファイルパス
        file_path = os.path.join(TEXT_DIR, f"{name}.txt")

        if not os.path.exists(file_path):
            # 初回保存
            is_first_run = True
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(current_text)
        else:
            # 前回テキスト読み込みと差分チェック
            with open(file_path, "r", encoding="utf-8") as f:
                old_text = f.read()

            added, removed = get_text_diff(old_text, current_text)

            if added or removed:
                updated_info.append((name, url, added, removed))
                # 最新状態へ更新保存
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(current_text)

    if is_first_run and not updated_info:
        print("初回実行：全ページの現在のテキスト状態を保存しました。")
        return

    if updated_info:
        print(f"更新を検知したページ: {[info[0] for info in updated_info]}")

        for name, url, added, removed in updated_info:
            diff_msg = f"🔔 **【こみはるオフィシャルサイト更新！】** 🔔\n"
            diff_msg += f"対象ページ: **{name}**\n🔗 {url}\n\n"

            if added:
                diff_msg += "🟢 **追加された要素:**\n```\n"
                diff_msg += "\n".join(added[:10])  # 文字数オーバー防止のため最大10行
                diff_msg += "\n```\n"

            if removed:
                diff_msg += "🔴 **削除された要素:**\n```\n"
                diff_msg += "\n".join(removed[:10])
                diff_msg += "\n```\n"

            send_discord_notification(diff_msg)
    else:
        print("すべてのページで更新はありませんでした。")


if __name__ == "__main__":
    main()