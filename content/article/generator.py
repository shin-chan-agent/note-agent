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
    """
    記事本文から「タイトル：」のタイトルを抽出する。

    「タイトル:」と「タイトル：」の両方に対応する。
    """

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
    """
    「タイトル：」より前にある余計な文章を削除する。
    """

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
    """
    記事を評価し、スコアと判定結果を返す。

    評価結果からスコアを取得できなかった場合は、
    MAX_RETRY回まで評価のみ再実行する。
    """

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
    )


def generate_article(
    client,
    prompt,
    knowledge,
    past_articles_text,
):

    # 固定記事案内
    fixed_text = (
        "AI×ショート動画で最速でマネタイズ（収益化）する具体的な手順と、"
        "豪華40大特典の受け取り方を下記の固定記事で詳しく解説しています。"
    )

    for attempt in range(MAX_RETRY):

        try:

            response = call_gemini(
                client,
                model=GEMINI_MODEL_ARTICLE,
                contents=prompt,
            )

            generated_text = response.text

            article = generated_text

            # 「タイトル：」より前の余計な文章を除去
            article = remove_before_title(article)

            # タイトル抽出・存在チェック
            extract_title(article)

            # 固定記事案内チェック
            if fixed_text not in article:
                log_warning(
                    "固定記事案内欠落。再生成します。"
                )
                continue

            # 文字数チェック
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

            # ========================================
            # 初回評価
            # ========================================

            (
                evaluation,
                score,
                seo_score,
                duplicate_result,
                latest_result,
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

            # ========================================
            # リライト
            # ========================================

            for rewrite in range(MAX_REWRITE):

                if (
                    score >= MIN_SCORE
                    and seo_score >= MIN_SEO_SCORE
                    and duplicate_result == "OK"
                    and latest_result == "OK"
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

                rewrite_prompt = result["improvements"]

                if not rewrite_prompt.strip():
                    log_info(
                        "改善指示がないためリライトを終了します。"
                    )
                    break

                article = rewrite_article(
                    client,
                    article,
                    knowledge,
                    rewrite_prompt,
                )

                # リライト後の記事から余計な文章を除去
                article = remove_before_title(
                    article
                )

                # タイトル抽出・存在チェック
                extract_title(article)

                # ====================================
                # リライト後の固定記事案内チェック
                # ====================================

                if fixed_text not in article:
                    log_warning(
                        "リライト後に固定記事案内が欠落しました。"
                    )

                    raise ValueError(
                        "リライト後の記事に固定記事案内がありません。"
                    )

                # ====================================
                # リライト後の文字数チェック
                # ====================================

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

                # ====================================
                # リライト後の再評価
                # ====================================

                (
                    evaluation,
                    score,
                    seo_score,
                    duplicate_result,
                    latest_result,
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

                # 改善点がない場合
                if (
                    re.search(
                        r"改善点\s*[:：]?\s*なし",
                        evaluation,
                    )
                    and duplicate_result == "OK"
                    and latest_result == "OK"
                ):
                    log_info(
                        "改善点がないためリライトを終了します。"
                    )
                    break

                # すべての品質基準をクリア
                if (
                    score >= MIN_SCORE
                    and seo_score >= MIN_SEO_SCORE
                    and duplicate_result == "OK"
                    and latest_result == "OK"
                ):
                    log_info(
                        "すべての品質基準をクリアしました。"
                    )
                    break

            # ========================================
            # 最終品質チェック
            # ========================================

            if score < MIN_SCORE:
                log_warning(
                    "最大回数リライトしましたが品質基準に届きませんでした。"
                )

            if seo_score < MIN_SEO_SCORE:
                log_warning(
                    "最大回数リライトしましたがSEO基準に届きませんでした。"
                )

            if duplicate_result != "OK":
                log_warning(
                    "最終記事が過去記事との重複基準を満たしていません。"
                )

            if latest_result != "OK":
                log_warning(
                    "最終記事が最新情報基準を満たしていません。"
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

            # 最終固定記事案内チェック
            if fixed_text not in article:
                raise ValueError(
                    "最終記事に固定記事案内がありません。"
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
    }