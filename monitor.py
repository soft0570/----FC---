import requests
import hashlib
import os

# ----------------- 設定 -----------------
TARGET_URL = "https://komiyamaharuka-fc.jp/"
# DiscordのURLはGitHubの「Secrets（秘密変数）」から安全に読み込みます
DISCORD_WEBHOOK_URL = os.environ.get("https://discord.com/api/webhooks/1527007643724415169/DJLwNtD5reQ9DQUDqsxM2LBBXzvd8URtNO8V5HBQq3Npk5zP7H7oXR7CQ5KyzzTEsav6")
# ----------------------------------------

def get_page_html():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.text
        return None
    except:
        return None

def send_discord_notification(message):
    payload = {"content": message}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Notification failed: {e}")

def main():
    if not DISCORD_WEBHOOK_URL:
        print("エラー: DiscordのWebhook URLが設定されていません。")
        return

    new_html = get_page_html()
    if not new_html:
        print("ページの取得に失敗しました。")
        return

    # 今回のハッシュ値を計算
    new_hash = hashlib.md5(new_html.encode('utf-8')).hexdigest()

    # 前回の状態（ハッシュ値）を一時保存ファイルから読み込む
    hash_file = "last_hash.txt"
    last_hash = ""
    if os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            last_hash = f.read().strip()

    # 比較する
    if not last_hash:
        # 初回実行時
        print("初回実行：現在の状態を保存します。")
        with open(hash_file, "w") as f:
            f.write(new_hash)
    elif new_hash != last_hash:
        # 変更があった場合
        print("更新を検知しました！")
        send_discord_notification(
            f"🔔 **【こみはるオフィシャルサイト更新！】** 🔔\n"
            f"公式サイトに何らかの変化・更新がありました！\n\n"
            f"🔗 **公式サイトをチェックする**:\n{TARGET_URL}"
        )
        # 新しい状態を保存
        with open(hash_file, "w") as f:
            f.write(new_hash)
    else:
        print("更新はありませんでした。")

if __name__ == "__main__":
    main()