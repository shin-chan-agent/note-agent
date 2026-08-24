import re

from google import genai

from theme_manager import get_theme_and_angle

from article_history import load_articles

from content.article.prompt import get_article_prompt
from content.article.generator import generate_article
from content.sns.generator import generate_sns_posts

from utils.knowledge_manager import (
    get_article_knowledge,
    needs_update,
    needs_retry,
    get_background_update_service,
)
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
from utils.gemini_client import GeminiDailyQuotaExceeded

from config import (
    MIN_SCORE,
    MIN_SEO_SCORE,
    THEME_SERVICES,
)

from datetime import datetime
from zoneinfo import ZoneInfo


def get_target_services(theme):
    """
    テーマから最新情報取得対象のサービスを取得する。
    """

    print(f"[DEBUG] theme='{theme}'")
    print(
        f"[DEBUG] available={list(THEME_SERVICES.keys())}"
    )

    return THEME_SERVICES.get(theme, [])


def split_text(text, max_length=4990):
    """
    LINE送信用に文章を分割する。

    ・1メッセージ最大4990文字
    ・4990文字以内で最後に出てくる「。」で分割
    ・「。」がなければ改行で分割
    ・それもなければ文字数で分割
    """

    parts = []

    while len(text) > max_length:

        # max_length以内で最後の「。」を探す
        split_pos = text.rfind(
            "。",
            0,
            max_length,
        )

        # 「。」がなければ最後の改行を探す
        if split_pos == -1:
            split_pos = text.rfind(
                "\n",
                0,
                max_length,
            )

        # それでもなければ文字数で強制分割
        if split_pos == -1:
            split_pos = max_length

        else:
            # 「。」または改行を含める
            split_pos += 1

        part = text[:split_pos].strip()

        if part:
            parts.append(part)

        text = text[split_pos:].strip()

    # 最後に残った部分
    if text:
        parts.append(text)

    # 【1/○】を付与
    total = len(parts)

    return [
        f"【{i + 1}/{total}】\n\n{part}"
        for i, part in enumerate(parts)
    ]


def generate_and_send_line():

    # ========================================
    # 現在日付
    # ========================================

    current_date = datetime.now(
        ZoneInfo("Asia/Tokyo")
    ).strftime("%Y年%m月%d日")


    # ========================================
    # Geminiクライアント
    # ========================================

    client = genai.Client()


    # ========================================
    # テーマ・切り口取得
    # ========================================

    theme, angle = get_theme_and_angle()


    # ========================================
    # 対象サービス取得
    # ========================================

    services = get_target_services(theme)

    log_info(
        f"対象サービス: {services}"
    )


    # ========================================
    # AI知識DB更新対象
    # ========================================

    update_services = [
        service_id
        for service_id in services
        if needs_update(service_id)
        or needs_retry(service_id)
    ]


    # バックグラウンド更新対象を1件追加
    background_service = (
        get_background_update_service(
            services
        )
    )

    if background_service:
        update_services.append(
            background_service
        )


    # 重複除去
    update_services = list(
        dict.fromkeys(update_services)
    )


    log_info(
        f"DB更新対象: {update_services}"
    )


    # ========================================
    # 最新情報取得
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
    # 記事生成用知識取得
    # ========================================

    knowledge = get_article_knowledge(
        services
    )


    # ========================================
    # 過去記事取得
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
    duplicate_result = result[
        "duplicate_result"
    ]
    latest_result = result[
        "latest_result"
    ]


    # ========================================
    # SNS投稿生成
    # ========================================

    try:

        x_post, instagram_post = (
            generate_sns_posts(
                client,
                article,
            )
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
    # タイトル取得
    # ========================================

    title_match = re.search(
        r"^タイトル[:：]\s*(.+)$",
        article,
        re.MULTILINE,
    )

    if not title_match:

        raise ValueError(
            "記事内にタイトルが見つかりません。"
        )

    title = title_match.group(1).strip()


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
    # 評価・SNSメッセージ
    # ========================================

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


    # ========================================
    # LINEメッセージ作成
    # ========================================

    messages = []


    # 記事本文
    for part in split_text(
        article_message
    ):

        messages.append(
            create_text_message(part)
        )


    # 評価・SNS
    messages.append(
        create_text_message(
            summary_message
        )
    )


    # ========================================
    # LINE送信・履歴保存
    # ========================================

    try:

        send_line_messages(
            messages
        )


        save_article(
            title,
            theme,
            angle,
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

        raise


if __name__ == "__main__":
    generate_and_send_line()