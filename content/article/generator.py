import re
import time

from quality_checker import quality_check
from rewrite import rewrite_article

from utils.gemini_client import (
    call_gemini,
    GeminiDailyQuotaExceeded,
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
    EVALUATION_RETRY_WAIT,
    GEMINI_RETRY_WAIT,
    MAX_ARTICLE_LENGTH,
    GEMINI_MODEL_ARTICLE,
)


def extract_title(article):
    match = re.search(
        r"^タイトル[:：]\s*(.+)$",
        article,
        re.MULTILINE,
    )

    if not match:
        raise ValueError(
            "記事内にタイトルが見つかりません。"
        )

    return match.group(1).strip()


def remove_before_title(article):
    title_match = re.search(
        r"^タイトル[:：]",
        article,
        re.MULTILINE,
    )

    if not title_match:
        raise ValueError(
            "記事内にタイトルが見つかりません。"
        )

    return article[title_match.start():].strip()


def evaluate_article(
    client,
    article,
    past_articles_text,
    knowledge,
):
    score = 0

    for _ in range(MAX_RETRY):

        evaluation = quality_check(
            client,
            article,
            past_articles_text,
            knowledge,
        )

        result = parse_evaluation(
            evaluation
        )

        score = result["score"]
        seo_score = result["seo_score"]
        duplicate_result = result["duplicate"]
        latest_result = result["latest"]
        paid_value_result = result["paid_value"]

        if score != 0:
            break

        log_warning(
            "評価のみ再実行します..."
        )

        time.sleep(
            EVALUATION_RETRY_WAIT
        )

    if score == 0:
        raise ValueError(
            "評価結果からスコアを取得できませんでした"
        )

    return (
        evaluation,
        score,
        seo_score,
        duplicate_result,
        latest_result,
        paid_value_result,
    )


def is_quality_pass(
    score,
    seo_score,
    duplicate_result,
    latest_result,
    paid_value_result,
):
    return (
        score >= MIN_SCORE
        and seo_score >= MIN_SEO_SCORE
        and duplicate_result == "OK"
        and latest_result == "OK"
        and paid_value_result == "OK"
    )


def generate_article(
    client,
    prompt,
    knowledge,
    past_articles_text,
):
    for attempt in range(MAX_RETRY):

        try:

            response = call_gemini(
                client,
                model=GEMINI_MODEL_ARTICLE,
                contents=prompt,
            )

            generated_text = response.text

            article = remove_before_title(
                generated_text
            )

            extract_title(article)

            if len(article) < 2000:

                log_warning(
                    "記事文字数不足。再生成します。"
                )

                continue

            if len(article) > MAX_ARTICLE_LENGTH:

                log_warning(
                    f"記事文字数超過（{len(article)}文字）。"
                    "再生成します。"
                )

                continue

            (
                evaluation,
                score,
                seo_score,
                duplicate_result,
                latest_result,
                paid_value_result,
            ) = evaluate_article(
                client,
                article,
                past_articles_text,
                knowledge,
            )

            log_info(
                f"記事スコア：{score}\n{evaluation}"
            )

            log_info(
                f"品質スコア：{score}"
            )

            log_info(
                f"SEOスコア：{seo_score}"
            )

            log_info(
                f"重複判定：{duplicate_result}"
            )

            log_info(
                f"最新情報判定：{latest_result}"
            )

            log_info(
                f"有料記事価値判定：{paid_value_result}"
            )

            for rewrite in range(MAX_REWRITE):

                if is_quality_pass(
                    score,
                    seo_score,
                    duplicate_result,
                    latest_result,
                    paid_value_result,
                ):

                    log_info(
                        "すべての品質基準をクリアしました。"
                    )

                    break

                log_warning(
                    f"{rewrite + 1}回目のリライトを開始します。"
                )

                result = parse_evaluation(
                    evaluation
                )

                rewrite_prompt = result[
                    "improvements"
                ]

                if not rewrite_prompt.strip():

                    log_warning(
                        "改善指示がないためリライトを終了します。"
                    )

                    break

                article = rewrite_article(
                    client,
                    article,
                    knowledge,
                    rewrite_prompt,
                )

                article = remove_before_title(
                    article
                )

                extract_title(article)

                if len(article) < 2000:

                    log_warning(
                        f"リライト後の記事が短すぎます（{len(article)}文字）。"
                    )

                    raise ValueError(
                        f"リライト後の記事が短すぎます: "
                        f"{len(article)}文字"
                    )

                if len(article) > MAX_ARTICLE_LENGTH:

                    log_warning(
                        f"リライト後の記事が長すぎます（{len(article)}文字）。"
                    )

                    raise ValueError(
                        f"リライト後の記事が最大文字数を超えています: "
                        f"{len(article)}文字"
                    )

                (
                    evaluation,
                    score,
                    seo_score,
                    duplicate_result,
                    latest_result,
                    paid_value_result,
                ) = evaluate_article(
                    client,
                    article,
                    past_articles_text,
                    knowledge,
                )

                log_info(
                    f"リライト後スコア：{score}\n{evaluation}"
                )

                log_info(
                    f"品質スコア：{score}"
                )

                log_info(
                    f"SEOスコア：{seo_score}"
                )

                log_info(
                    f"重複判定：{duplicate_result}"
                )

                log_info(
                    f"最新情報判定：{latest_result}"
                )

                log_info(
                    f"有料記事価値判定：{paid_value_result}"
                )

                if is_quality_pass(
                    score,
                    seo_score,
                    duplicate_result,
                    latest_result,
                    paid_value_result,
                ):

                    log_info(
                        "すべての品質基準をクリアしました。"
                    )

                    break

            # ========================================
            # 最終品質判定
            # ========================================

            if not is_quality_pass(
                score,
                seo_score,
                duplicate_result,
                latest_result,
                paid_value_result,
            ):

                if score < MIN_SCORE:

                    log_warning(
                        "最終品質スコアが基準未達です。"
                    )

                if seo_score < MIN_SEO_SCORE:

                    log_warning(
                        "最終SEOスコアが基準未達です。"
                    )

                if duplicate_result != "OK":

                    log_warning(
                        "最終記事が重複基準を満たしていません。"
                    )

                if latest_result != "OK":

                    log_warning(
                        "最終記事が最新情報基準を満たしていません。"
                    )

                if paid_value_result != "OK":

                    log_warning(
                        "最終記事が有料記事価値基準を満たしていません。"
                    )

                raise ValueError(
                    "最大回数リライト後も"
                    "すべての品質基準を満たせませんでした。"
                )

            if len(article) < 2000:

                raise ValueError(
                    f"最終記事が短すぎます: "
                    f"{len(article)}文字"
                )

            if len(article) > MAX_ARTICLE_LENGTH:

                raise ValueError(
                    f"最終記事が最大文字数を超えています: "
                    f"{len(article)}文字"
                )

            break

        except GeminiDailyQuotaExceeded:

            raise

        except Exception as e:

            log_error(
                f"Geminiエラー（{attempt + 1}回目）：{e}"
            )

            if attempt == MAX_RETRY - 1:

                raise

            log_warning(
                f"{GEMINI_RETRY_WAIT}秒後に再試行します..."
            )

            time.sleep(
                GEMINI_RETRY_WAIT
            )

    return {
        "article": article,
        "evaluation": evaluation,
        "score": score,
        "seo_score": seo_score,
        "duplicate_result": duplicate_result,
        "latest_result": latest_result,
        "paid_value_result": paid_value_result,
    }