import re
import time

from quality_checker import quality_check
from rewrite import rewrite_article

from utils.gemini_client import call_gemini
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
)


def generate_article(
    client,
    prompt,
    latest_info,
    past_articles_text,
):


    for attempt in range(MAX_RETRY):
        try:
            response = call_gemini(
                client,
                model="gemini-2.5-flash",
                contents=prompt,
            )

            article = response.text

            # タイトル欠落チェック
            if not re.search(r"^タイトル[:：]", article):
                log_warning("タイトル欠落。再生成します。")
                continue

            # 固定記事案内チェック
            fixed_text = (
                "AI×ショート動画で最速でマネタイズ（収益化）する具体的な手順と、"
                "豪華40大特典の受け取り方を下記の固定記事で詳しく解説しています。"
            )

            if fixed_text not in article:
                log_warning("固定記事案内欠落。再生成します。")
                continue

            article_length = len(article)

            # 文字数不足チェック
            if article_length < 2000:
                log_warning("記事文字数不足。再生成します。")
                continue

            # 評価だけリトライ
            for _ in range(3):
                evaluation = quality_check(
                    client,
                    article,
                    past_articles_text,
                    latest_info,
                )

                result = parse_evaluation(evaluation)

                score = result["score"]
                seo_score = result["seo_score"]
                duplicate_result = result["duplicate"]
                latest_result = result["latest"]

                if score != 0:
                    break

                log_warning("評価のみ再実行します...")
                time.sleep(EVALUATION_RETRY_WAIT)

            if score == 0:
                raise ValueError("評価結果からスコアを取得できませんでした")

            log_info(f"記事スコア：{score}\n{evaluation}")
            log_info(f"品質スコア：{score}")
            log_info(f"SEOスコア：{seo_score}")

            for rewrite in range(MAX_REWRITE):

                if (
                    score >= MIN_SCORE
                    and seo_score >= MIN_SEO_SCORE
                    and duplicate_result == "OK"
                    and latest_result == "OK"
                ):
                    log_info("すべての品質基準をクリアしました。")
                    break


                log_warning(f"{rewrite + 1}回目のリライトを開始します。")

                result = parse_evaluation(evaluation)

                rewrite_prompt = result["improvements"]

                if not rewrite_prompt.strip():
                    log_info("改善指示がないためリライトを終了します。")
                    break

                article = rewrite_article(
                    client,
                    article,
                    latest_info,
                    rewrite_prompt,
                )


                # 評価だけリトライ
                for _ in range(3):
                    evaluation = quality_check(
                        client,
                        article,
                        past_articles_text,
                        latest_info,
                    )

                    result = parse_evaluation(evaluation)

                    score = result["score"]
                    seo_score = result["seo_score"]
                    duplicate_result = result["duplicate"]
                    latest_result = result["latest"]

                    if score != 0:
                        break

                    log_warning("評価のみ再実行します...")
                    time.sleep(EVALUATION_RETRY_WAIT)

                if score == 0:
                    raise ValueError("評価結果からスコアを取得できませんでした")

                log_info(f"リライト後スコア：{score}\n{evaluation}")
                log_info(f"品質スコア：{score}")
                log_info(f"SEOスコア：{seo_score}")

                if (
                    re.search(r"改善点\s*[:：]?\s*なし", evaluation)
                    and duplicate_result == "OK"
                ):
                    log_info("改善点がないためリライトを終了します。")
                    break

                if (
                    score >= MIN_SCORE
                    and seo_score >= MIN_SEO_SCORE
                    and duplicate_result == "OK"
                    and latest_result == "OK"
                ):
                    log_info("すべての品質基準をクリアしました。")
                    break


            if score < MIN_SCORE:
                log_warning("最大回数リライトしましたが品質基準に届きませんでした。")


            if seo_score < MIN_SEO_SCORE:
                log_warning("最大回数リライトしましたがSEO基準に届きませんでした。")

            x_post, instagram_post = generate_sns_posts(
                client,
                article,
            )

            log_info(f"===== X投稿 =====\n{x_post}")

            log_info(f"===== Instagram投稿 =====\n{instagram_post}")

            break

        except Exception as e:
            log_error(f"Geminiエラー（{attempt + 1}回目）：{e}")

            if attempt == MAX_RETRY - 1:
                raise

            log_warning(f"{GEMINI_RETRY_WAIT}秒後に再試行します...")
            time.sleep(GEMINI_RETRY_WAIT)


    return {
        "article": article,
        "evaluation": evaluation,
        "score": score,
        "seo_score": seo_score,
        "duplicate_result": duplicate_result,
        "latest_result": latest_result,
    }