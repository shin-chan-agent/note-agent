import os
import re
import time

from google import genai
from google.genai import types

from theme_manager import get_theme_and_angle
from quality_checker import quality_check
from rewrite import rewrite_article

from article_history import load_articles, save_article

from content.article.prompt import get_article_prompt
from content.sns.generator import generate_sns_posts

from utils.gemini_client import call_gemini
from utils.line_sender import (
    send_line_messages,
    create_text_message,
)
from utils.evaluation_parser import parse_evaluation
from utils.logger import (
    log_info,
    log_warning,
    log_error,
)

from config import (
    MIN_SCORE,
    MIN_SEO_SCORE,
    MAX_REWRITE,
    MAX_RETRY,
    GOOGLE_SEARCH_RETRY_WAIT,
    GEMINI_RETRY_WAIT,
    EVALUATION_RETRY_WAIT,
)

from content.article.generator import generate_article


SEARCH_QUERIES = {
    "ChatGPT": "ChatGPT 最新 GPT-5 無料版 Plus Pro Teams Enterprise 料金 機能",
    "Gemini": "Google Gemini 最新 Gemini 2.5 Flash Pro 料金 AI Studio 機能",
    "Claude": "Claude 最新 Sonnet Opus 料金 機能",
    "Canva": "Canva 最新 AI機能 Magic Studio Visual Suite 料金",
    "CapCut": "CapCut 最新 AI機能 料金 商用利用",
    "note": "note 最新 アルゴリズム SEO 仕様変更",
    "Instagram": "Instagram 最新 リール アルゴリズム",
    "X": "X 最新 アルゴリズム 収益化",
    "AI副業": "AI副業 最新 トレンド AIツール",
    "ショート動画": "ショート動画 最新 トレンド YouTube Shorts Instagram Reels TikTok",
}


def get_search_query(theme):
    for keyword, query in SEARCH_QUERIES.items():
        if keyword in theme:
            return query

    return f"{theme} 最新"


def get_latest_info(client, theme):
    query = get_search_query(theme)

    prompt = f"""
以下の検索キーワードについて最新情報を調査してください。

検索キーワード
{query}

以下を優先してください。

・最新の料金プラン
・利用できるモデル
・新機能
・仕様変更
・注意点

記事執筆で使えるように、
箇条書きで500〜1000文字程度にまとめてください。
"""

    response = call_gemini(
        client,
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())]
        ),
    )

    return response.text


def split_text(text, max_length=4800):
    # タイトル・導入文を取得
    match = re.search(r"(.*?)(?=\n### |\n## |\Z)", text, re.DOTALL)

    if match:
        header = match.group(1).strip()
        body = text[len(match.group(1)):].strip()
    else:
        header = ""
        body = text

    # H3単位で分割
    sections = re.split(r"(?=\n### )", body)

    parts = []
    current = header

    for section in sections:

        section = section.strip()

        if not section:
            continue

        # 入るなら追加
        if len(current) + len(section) + 2 <= max_length:

            if current:
                current += "\n\n"

            current += section
            continue

        # 一旦保存
        if current:
            parts.append(current)

        # H3単体が長すぎる場合
        if len(section) > max_length:

            current = ""

            paragraphs = section.split("\n\n")

            for paragraph in paragraphs:

                if len(current) + len(paragraph) + 2 <= max_length:

                    if current:
                        current += "\n\n"

                    current += paragraph

                else:

                    if current:
                        parts.append(current)

                    # 段落でも長い場合
                    if len(paragraph) > max_length:

                        current = ""

                        lines = paragraph.split("\n")

                        for line in lines:

                            if len(current) + len(line) + 1 <= max_length:

                                if current:
                                    current += "\n"

                                current += line

                            else:

                                if current:
                                    parts.append(current)

                                while len(line) > max_length:
                                    parts.append(line[:max_length])
                                    line = line[max_length:]

                                current = line

                    else:
                        current = paragraph

        else:
            current = section

    if current:
        parts.append(current)

    # 【1/○】を付与
    total = len(parts)

    return [
        f"【{i + 1}/{total}】\n\n{part}"
        for i, part in enumerate(parts)
    ]


def generate_and_send_line():
    # 最新のライブラリでGeminiで記事を生成
    # 環境変数から自動でAPIキーを読み込む仕様になりました

    client = genai.Client()

    theme, angle = get_theme_and_angle()

    past_articles = load_articles()

    for _ in range(MAX_RETRY):
        try:
            latest_info = get_latest_info(client, theme)
            break
        except Exception as e:
            log_warning(f"Google Searchを再試行します... {e}")
            time.sleep(GOOGLE_SEARCH_RETRY_WAIT)
    else:
        raise ValueError("最新情報を取得できませんでした")

    log_info(f"===== 最新情報 =====\n{latest_info}")

    past_articles_text = "\n\n".join(
        (
            f"タイトル: {article['title']}\n"
            f"テーマ: {article['theme']}\n"
            f"切り口: {article['angle']}"
        )
        for article in past_articles[-20:]
    )


    prompt = get_article_prompt(
        theme,
        angle,
        latest_info,
        past_articles_text,
    )


    result = generate_article(
        client,
        prompt,
        latest_info,
        past_articles_text,
    )

    article = result["article"]
    evaluation = result["evaluation"]
    score = result["score"]
    seo_score = result["seo_score"]
    duplicate_result = result["duplicate_result"]
    latest_result = result["latest_result"]

    x_post, instagram_post = generate_sns_posts(
        client,
        article,
    )

    log_info(f"===== X投稿 =====\n{x_post}")
    log_info(f"===== Instagram投稿 =====\n{instagram_post}")


    status = (
        "✅ 全品質基準クリア"
        if (
            score >= MIN_SCORE
            and seo_score >= MIN_SEO_SCORE
            and duplicate_result == "OK"
            and latest_result == "OK"
        )
        else "⚠️ 品質基準未達"
    )
    
    # LINE公式アカウント（Messaging API）を使ってメッセージを送信
    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    user_id = os.environ["LINE_USER_ID"]
    
    line_api_url = "https://api.line.me/v2/bot/message/push"
    
    # 送信するメッセージの組み立て
    article_message = f"""🤖【Gemini生成のnote原稿】🤖

{status}

最終スコア：{score}点

--------------------

{article}
"""


    evaluation = evaluation.strip()
    x_post = x_post.strip()
    instagram_post = instagram_post.strip()


    summary_message = f"""
📊【AI評価】

{evaluation}

--------------------

🐦【X投稿】

{x_post}

--------------------

📸【Instagram投稿】

{instagram_post}
"""


    messages = []


    for part in split_text(article_message):
        messages.append(create_text_message(part))

    messages.append(create_text_message(summary_message))


    try:
        response_line = send_line_messages(messages)

        title = article.split("\n")[0].replace("タイトル：", "").replace("タイトル:", "").strip()

        save_article(
            title,
            theme,
            angle,
        )

        log_info("記事履歴を保存しました。")
        log_info("LINEへ正常に送信しました。")

    except Exception as e:
        log_error(f"予期しないエラー: {e}")
        raise e


if __name__ == "__main__":
    generate_and_send_line()
