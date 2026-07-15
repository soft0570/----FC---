import requests
import hashlib
import os
from bs4 import BeautifulSoup

# ----------------- 設定 -----------------
TARGET_URL = "https://komiyamaharuka-fc.jp/"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
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

def parse_latest_info(html_content):
    """
    ファンクラブサイトのトップページから最新の更新情報を解析する関数
    戻り値: (カテゴリ, タイトル, 詳細リンク) のタプル
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    # 込山榛香FCサイトの新着情報のリスト要素（liタグや特定のクラス）を探します
    # 一般的なサイト構造（新着アイテムのまとまり）をターゲットにします
    # ※サイト仕様に合わせて最適な要素を抽出します
    
    category = "UNKNOWN"
    title = "新しい更新があります"
    link_url = TARGET_URL

    # 1. ニュースや新着リストの要素を探索 (一般的なFCサイトのパターン)
    # <a>タグや<li>タグの中から、NEWS/MOVIE/PHOTO/BLOGなどのテキストを含む要素を探します
    items = soup.find_all(["li", "div", "a"], class_=lambda x: x and any(term in x.lower() for term in ["news", "post", "item", "article", "latest"]))
    
    # うまくクラス名で取れない場合は、直近のリンク付きカードやリスト要素を探す
    if not items:
        items = soup.find_all("a", href=True)

    for item in items:
        text = item.get_text().strip()
        # カテゴリのキーワードが含まれているか判定
        found_cat = None
        for cat in ["NEWS", "MOVIE", "PHOTO", "BLOG"]:
            if cat in text.upper():
                found_cat = cat
                break
        
        if found_cat:
            category = found_cat
            # テキストからカテゴリ名や日付を除外して「タイトル」部分を綺麗に取り出す
            clean_text = text.replace(category, "").strip()
            # 改行や連続する空白を1つにまとめる
            title = " ".join(clean_text.split())
            
            # リンクURLの取得
            href = item.get("href") or (item.find("a") and item.find("a").get("href"))
            if href:
                if href.startswith("/"):
                    link_url = f"https://komiyamaharuka-fc.jp{href}"
                elif href.startswith("http"):
                    link_url = href
            break  # 一番最初（最新）の項目が見つかったら終了
            
    return category, title, link_url

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

    # 今回の最新情報を解析
    category, title, link_url = parse_latest_info(new_html)
    
    # 今回取得した最新情報の「識別用テキスト」を作成
    # これが前回と変わっていれば更新とみなす
    current_state = f"{category}:::{title}"
    current_hash = hashlib.md5(current_state.encode('utf-8')).hexdigest()

    # 前回のハッシュ値を読み込む
    hash_file = "last_hash_komiharu.txt"
    last_hash = ""
    if os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            last_hash = f.read().strip()

    # 初回実行時
    if not last_hash:
        print(f"初回実行：現在の最新情報を記憶します。({category}: {title})")
        with open(hash_file, "w") as f:
            f.write(current_hash)
        return

    # 比較
    if current_hash != last_hash:
        print(f"更新を検知！ {category} - {title}")
        
        # カテゴリに応じたメッセージの作成
        if category in ["NEWS", "BLOG"]:
            # タイトルまで詳細に通知
            message = (
                f"🔔 **【こみはるオフィシャルサイト更新！】** 🔔\n"
                f"公式ファンクラブに新しい **{category}** が投稿されました！\n\n"
                f"📌 **タイトル**: {title}\n\n"
                f"🔗 **今すぐチェックする**:\n{link_url}"
            )
        elif category in ["MOVIE", "PHOTO"]:
            # ムービーやフォトの更新通知
            message = (
                f"🎥 **【こみはるオフィシャルサイト更新！】** 🎥\n"
                f"ファンクラブに新しい **{category}** がアップされました！\n\n"
                f"🔗 **見に行く**:\n{link_url}"
            )
        else:
            # 万が一カテゴリが判別できなかった場合
            message = (
                f"✨ **【こみはるオフィシャルサイト更新！】** ✨\n"
                f"ファンクラブサイトに何らかの更新がありました！\n\n"
                f"🔗 **公式サイトをチェックする**:\n{TARGET_URL}"
            )

        send_discord_notification(message)
        
        # 新しいハッシュ値を保存
        with open(hash_file, "w") as f:
            f.write(current_hash)
    else:
        print("更新はありませんでした。")

if __name__ == "__main__":
    main()