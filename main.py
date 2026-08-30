from datetime import datetime
from zoneinfo import ZoneInfo

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
from content.article.generator import (
    generate_article,
    extract_title,
)
from content.sns.generator import generate_sns_posts
from content.video.generator import generate_video_scripts

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
)


def send_error_notification(
    error_type,
    error_message,
):
    """
    エラー発生時にLINEへ通知する。

    LINE通知自体の失敗で
    元のエラー処理を妨げないようにする。
    """

    message = f"""🚨【Note AI Agent エラー】

エラー種別：
{error_type}

内容：
{error_message}

発生日時：
{datetime.now(
    ZoneInfo("Asia/Tokyo")
).strftime("%Y年%m月%d日 %H:%M:%S")}
"""

    try:

        send_line_messages(
            [
                create_text_message(
                    message
                )
            ]
        )

        log_info(
            "エラー通知をLINEへ送信しました。"
        )

    except Exception as e:

        log_error(
            f"エラー通知のLINE送信にも失敗しました: {e}"
        )


def generate_and_send_line():

    # ========================================
    # 現在日付を日本時間で取得
    # ========================================

    current_date = datetime.now(
        ZoneInfo("Asia/Tokyo")
    ).strftime("%Y年%m月%d日")

    # ========================================
    # Geminiクライアント
    # ========================================

    client = genai.Client()

    # ========================================
    # テーマ・切り口を決定
    # ========================================

    theme, angle = get_theme_and_angle()

    # ========================================
    # テーマから対象サービスを取得
    # ========================================

    services = get_target_services(theme)

    log_info(
        f"対象サービス: {services}"
    )

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

    log_info(
        f"DB更新対象: {update_services}"
    )

    # ========================================
    # AI知識DBの最新情報を取得
    # ========================================

    if update_services:

        try:

            fetch_latest_info(
                client,
                update_services,
            )

        except GeminiDailyQuotaExceeded as e:

            log_warning(
                "Gemini APIの日次クォータ超過のため、"
                "AI知識DB更新を中止します。"
            )

            send_error_notification(
                "Gemini API日次クォータ超過",
                str(e),
            )

            return

        except Exception as e:

            log_error(
                f"AI知識DB更新エラー: {e}"
            )

            send_error_notification(
                "AI知識DB更新エラー",
                str(e),
            )

            return

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

    past_articles_text = get_past_articles_text()

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

    except GeminiDailyQuotaExceeded as e:

        log_warning(
            "Gemini APIの日次クォータ超過のため、"
            "記事生成を中止します。"
        )

        send_error_notification(
            "Gemini API日次クォータ超過",
            str(e),
        )

        log_warning(
            "記事が完成していないため、"
            "SNS生成・動画台本生成・LINE送信・"
            "記事履歴保存は行いません。"
        )

        return

    except Exception as e:

        log_error(
            f"記事生成エラー: {e}"
        )

        send_error_notification(
            "記事生成エラー",
            str(e),
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
    # X・Threads・Instagram投稿生成
    # ========================================

    try:

        (
            x_post,
            threads_post,
            instagram_post,
        ) = generate_sns_posts(
            client,
            article,
        )

    except GeminiDailyQuotaExceeded as e:

        log_warning(
            "Gemini APIの日次クォータ超過のため、"
            "SNS投稿生成をスキップします。"
        )

        send_error_notification(
            "Gemini API日次クォータ超過（SNS生成）",
            str(e),
        )

        x_post = (
            "※Gemini APIの日次クォータ超過のため、"
            "X投稿は生成できませんでした。"
        )

        threads_post = (
            "※Gemini APIの日次クォータ超過のため、"
            "Threads投稿は生成できませんでした。"
        )

        instagram_post = (
            "※Gemini APIの日次クォータ超過のため、"
            "Instagram投稿は生成できませんでした。"
        )

    except Exception as e:

        log_error(
            f"SNS投稿生成エラー: {e}"
        )

        send_error_notification(
            "SNS投稿生成エラー",
            str(e),
        )

        x_post = (
            "※SNS投稿の生成に失敗しました。"
        )

        threads_post = (
            "※SNS投稿の生成に失敗しました。"
        )

        instagram_post = (
            "※SNS投稿の生成に失敗しました。"
        )

    # ========================================
    # ショート動画台本生成
    # ========================================

    try:

        video_30, video_60 = generate_video_scripts(
            client,
            article,
        )

    except GeminiDailyQuotaExceeded as e:

        log_warning(
            "Gemini APIの日次クォータ超過のため、"
            "ショート動画台本生成をスキップします。"
        )

        send_error_notification(
            "Gemini API日次クォータ超過（動画台本生成）",
            str(e),
        )

        video_30 = (
            "※Gemini APIの日次クォータ超過のため、"
            "30秒動画台本は生成できませんでした。"
        )

        video_60 = (
            "※Gemini APIの日次クォータ超過のため、"
            "60秒動画台本は生成できませんでした。"
        )

    except Exception as e:

        log_error(
            f"ショート動画台本生成エラー: {e}"
        )

        send_error_notification(
            "ショート動画台本生成エラー",
            str(e),
        )

        video_30 = (
            "※30秒動画台本の生成に失敗しました。"
        )

        video_60 = (
            "※60秒動画台本の生成に失敗しました。"
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
    threads_post = threads_post.strip()
    instagram_post = instagram_post.strip()
    video_30 = video_30.strip()
    video_60 = video_60.strip()

    # ========================================
    # 評価・SNS・動画台本メッセージ
    # ========================================

    summary_message = f"""📊【AI評価】

{evaluation}

--------------------

🐦【X投稿】

{x_post}

--------------------

🧵【Threads投稿】

{threads_post}

--------------------

📸【Instagram投稿】

{instagram_post}

--------------------

🎬【30秒ショート動画台本】

{video_30}

--------------------

🎬【60秒ショート動画台本】

{video_60}
"""

    # ========================================
    # LINEメッセージ作成
    # ========================================

    messages = []

    # 長い記事は分割して送信
    for part in split_text(
        article_message
    ):

        messages.append(
            create_text_message(part)
        )

    # 評価・SNS投稿・動画台本
    messages.append(
        create_text_message(
            summary_message
        )
    )

    # ========================================
    # LINE送信・記事履歴保存
    # ========================================

    try:

        send_line_messages(
            messages
        )

        save_article(
            title=extract_title(article),
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
            f"LINE送信または記事履歴保存エラー: {e}"
        )

        send_error_notification(
            "LINE送信または記事履歴保存エラー",
            str(e),
        )

        raise


if __name__ == "__main__":
    generate_and_send_line()