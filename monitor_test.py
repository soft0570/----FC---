import hashlib
import os
import requests

# ----------------- 設定 -----------------
TARGET_URL = "https://httpbin.org/uuid"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
HASH_FILE = "last_hash_test.txt"
# ----------------------------------------


def get_uuid():
    try:
        response = requests.get(TARGET_URL, timeout=15)
        if response.status_code == 200:
            # JSONからUUID文字列を取得
            data = response.json()
            return data.get("uuid")
        return None
    except Exception as e:
        print(f"Error fetching UUID: {e}")
        return None


def send_discord(message):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=10)
    except Exception as e:
        print(f"Notification failed: {e}")


def main():
    if not DISCORD_WEBHOOK_URL:
        print("エラー: DISCORD_WEBHOOK_URL が設定されていません。")
        return

    current_uuid = get_uuid()
    if not current_uuid:
        print("UUIDの取得に失敗しました。")
        return

    current_hash = hashlib.md5(current_uuid.encode("utf-8")).hexdigest()

    last_hash = ""
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            last_hash = f.read().strip()

    # 初回実行時：ハッシュを記録して終了
    if not last_hash:
        print(f"初回実行：テスト用UUIDを記憶します。({current_uuid})")
        with open(HASH_FILE, "w") as f:
            f.write(current_hash)
        return

    # 比較（必ず毎回値が変わるため更新検知される）
    if current_hash != last_hash:
        message = (
            f"🧪 **【動作テスト成功！】** 🧪\n"
            f"Web監視システムが正常に更新を検知しました。\n\n"
            f"🆔 **取得UUID**: `{current_uuid}`"
        )
        send_discord(message)

        # 新しいハッシュ値を保存
        with open(HASH_FILE, "w") as f:
            f.write(current_hash)
    else:
        print("更新はありませんでした。")


if __name__ == "__main__":
    main()