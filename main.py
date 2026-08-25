import os
import re
import time

from google import genai

from theme_manager import (
    get_theme_and_angle,
    get_target_services,
)

from article_history import (
    get_past_articles_text,
    save_article,
)

from content.article.prompt import get_article_prompt
from content.article.generator import generate_article
from content.sns.generator import generate_sns_posts

from utils.knowledge_manager import (
    get_services,
    get_article_knowledge,
    needs_update,
    needs_retry,
    get_background_update_service,
)
from utils.latest_info import fetch_latest_info
from utils.line_sender import (
    send_line_messages,
    create_text_message,
    split_text,
)
from utils.logger import (
    log_info,
    log_warning,
    log_error,
)
from utils.gemini_client import GeminiDailyQuotaExceeded

from config import (
    MIN_SCORE,
    MIN_SEO_SCORE,
    MAX_REWRITE,
    MAX_RETRY,
    GOOGLE_SEARCH_RETRY_WAIT,
    KNOWLEDGE_UPDATE_INTERVAL_DAYS,
)

from datetime import datetime
from zoneinfo import ZoneInfo


def generate_and_send_line():

    # 現在日付を日本時間で取得
    current_date = datetime.now(
        ZoneInfo("Asia/Tokyo")
    ).strftime("%Y年%m月%d日")

    # Geminiクライアント
    client = genai.Client()

    # テーマ・切り口を決定
    theme, angle = get_theme_and_angle()

    # テーマから対象サービスを取得
    services = get_target_services(theme)

    log_info(f"対象サービス: {services}")

    # ========================================
    # AI知識DBの更新対象を決定
    # ========================================

    update_services = [
        service_id
        for service_id in services
        if needs_update(service_id)
        or needs_retry(service_id)
    ]

    # バックグラウンド更新対象を1件追加
    background_service = get_background_update_service(
        services
    )

    if background_service:
        update_services.append(
            background_service
        )

    # 重複除去
    update_services = list(
        dict.fromkeys(update_services)
    )

    log_info(f"DB更新対象: {update_services}")

    # ========================================
    # AI知識DBの最新情報を取得
    # ========================================

    if update_services:

        fetch_latest_info(
            client,
            update_services,
        )

    else:

        log_info(
            "AI知識DBは最新のため更新スキップ"
        )

    # ========================================
    # 記事生成用の知識を取得
    # ========================================

    knowledge = get_article_knowledge(
        services
    )

    # ========================================
    # 過去記事を取得
    # ========================================

    past_articles = load_articles()

    past_articles_text = "\n\n".join(
        (
            f"タイトル: {article['title']}\n"
            f"テーマ: {article['theme']}\n"
            f"切り口: {article['angle']}"
        )
        for article in past_articles[-20:]
    )

    # ========================================
    # 記事生成プロンプト
    # ========================================

    prompt = get_article_prompt(
        theme,
        angle,
        knowledge,
        past_articles_text,
        current_date,
    )

    # ========================================
    # 記事生成
    # ========================================

    try:

        result = generate_article(
            client,
            prompt,
            knowledge,
            past_articles_text,
        )

    except GeminiDailyQuotaExceeded:

        log_warning(
            "Gemini APIの日次クォータ超過のため、"
            "記事生成を中止します。"
        )

        log_warning(
            "記事が完成していないため、"
            "SNS生成・LINE送信・記事履歴保存は行いません。"
        )

        return

    # ========================================
    # 記事生成結果
    # ========================================

    article = result["article"]
    evaluation = result["evaluation"]
    score = result["score"]
    seo_score = result["seo_score"]
    duplicate_result = result["duplicate_result"]
    latest_result = result["latest_result"]

    # ========================================
    # X・Instagram投稿生成
    # ========================================

    try:

        x_post, instagram_post = generate_sns_posts(
            client,
            article,
        )

    except GeminiDailyQuotaExceeded:

        log_warning(
            "Gemini APIの日次クォータ超過のため、"
            "SNS投稿生成をスキップします。"
        )

        x_post = (
            "※Gemini APIの日次クォータ超過のため、"
            "X投稿は生成できませんでした。"
        )

        instagram_post = (
            "※Gemini APIの日次クォータ超過のため、"
            "Instagram投稿は生成できませんでした。"
        )

    # ========================================
    # 品質ステータス
    # ========================================

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

    # ========================================
    # 記事メッセージ
    # ========================================

    article_message = f"""🤖【Gemini生成のnote原稿】🤖

{status}

最終スコア：{score}点

--------------------

{article}
"""

    evaluation = evaluation.strip()
    x_post = x_post.strip()
    instagram_post = instagram_post.strip()

    # ========================================
    # 評価・SNS投稿メッセージ
    # ========================================

    summary_message = f"""📊【AI評価】

{evaluation}

--------------------

🐦【X投稿】

{x_post}

--------------------

📸【Instagram投稿】

{instagram_post}
"""

    # ========================================
    # LINEメッセージ作成
    # ========================================

    messages = []

    # 長い記事は分割して送信
    for part in split_text(article_message):

        messages.append(
            create_text_message(part)
        )

    # 評価・SNS投稿
    messages.append(
        create_text_message(summary_message)
    )

    # ========================================
    # LINE送信・記事履歴保存
    # ========================================

    try:

        response_line = send_line_messages(
            messages
        )

        save_article(
            title=re.search(
                r"^タイトル[:：]\s*(.+)$",
                article,
                re.MULTILINE,
            ).group(1).strip(),
            theme=theme,
            angle=angle,
        )

        log_info(
            "記事履歴を保存しました。"
        )

        log_info(
            "LINEへ正常に送信しました。"
        )

    except Exception as e:

        log_error(
            f"予期しないエラー: {e}"
        )

        raise e


if __name__ == "__main__":
    generate_and_send_line()