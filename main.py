import os
import re
import time

from google import genai

from theme_manager import get_theme_and_angle

from article_history import load_articles, save_article

from content.article.prompt import get_article_prompt
from content.article.generator import generate_article
from content.sns.generator import generate_sns_posts

from utils.knowledge_manager import get_services
from utils.latest_info import fetch_latest_info
from utils.line_sender import (
    send_line_messages,
    create_text_message,
)
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
    THEME_SERVICES,
)


def get_target_services(theme):
    """
    テーマから最新情報取得対象のサービスを判定する。
    """

    services = []

    for service_id, service in AI_SERVICES.items():

        if service["name"] in theme:
            services.append(service_id)

    return services


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

    services = get_target_services(theme)

    if services:
        fetch_latest_info(
            client,
            services,
        )

    knowledge = get_services(services)

    past_articles = load_articles()

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
        knowledge,
        past_articles_text,
    )


    result = generate_article(
        client,
        prompt,
        knowledge,
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
