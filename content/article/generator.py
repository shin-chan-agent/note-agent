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
from utils.image_metadata_parser import (
    parse_image_metadata,
    is_valid_image_metadata,
)

from config import (
    MIN_SCORE,
    MIN_SEO_SCORE,
    MAX_REWRITE,
    MAX_RETRY,
    EVALUATION_RETRY_WAIT,
    GEMINI_RETRY_WAIT,
    MAX_ARTICLE_LENGTH,
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
                model="gemini-2.5-flash",
                contents=prompt,
            )

            generated_text = response.text

            article = generated_text

            # 「タイトル：」より前の余計な文章を除去
            title_match = re.search(
                r"^タイトル[:：]",
                article,
                re.MULTILINE,
            )

            if title_match:
                article = article[title_match.start():].strip()
            else:
                raise ValueError(
                    "記事内にタイトルが見つかりません。"
                )

            # タイトル欠落チェック
            if not re.search(
                r"^タイトル[:：]",
                article,
                re.MULTILINE,
            ):
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

            # 文字数チェック
            if len(article) < 2000:
                log_warning("記事文字数不足。再生成します。")
                continue

            if len(article) > MAX_ARTICLE_LENGTH:
                log_warning(
                    f"記事文字数超過（{len(article)}文字）。再生成します。"
                )
                continue

            # 評価だけリトライ
            for _ in range(MAX_RETRY):
                evaluation = quality_check(
                    client,
                    article,
                    past_articles_text,
                    knowledge,
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
                    knowledge,
                    rewrite_prompt,
                )

                # リライト時にタイトルより前へ余計な文章を除去
                title_match = re.search(
                    r"タイトル[:：]",
                    article,
                )

                if title_match:
                    article = article[title_match.start():].strip()
                else:
                    raise ValueError(
                        "リライト後の記事にタイトルが見つかりません。"
    )

                if len(article) > MAX_ARTICLE_LENGTH:
                    log_warning(
                        f"リライト後の記事が長すぎます（{len(article)}文字）。"
                        "記事生成をやり直します。"
                    )
                    raise ValueError(
                        f"リライト後の記事が最大文字数を超えています: {len(article)}文字"
                    )


                # 評価だけリトライ
                for _ in range(MAX_RETRY):
                    evaluation = quality_check(
                        client,
                        article,
                        past_articles_text,
                        knowledge,
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


            if len(article) > MAX_ARTICLE_LENGTH:
                raise ValueError(
                    f"最終記事が最大文字数を超えています: {len(article)}文字"
                )


            break


        except GeminiDailyQuotaExceeded:
            raise

        except Exception as e:
            log_error(f"Geminiエラー（{attempt + 1}回目）：{e}")

            if attempt == MAX_RETRY - 1:
                raise

            log_warning(
                f"{GEMINI_RETRY_WAIT}秒後に再試行します..."
            )
            time.sleep(GEMINI_RETRY_WAIT)


        # ========================================
        # アイキャッチ画像用メタデータ取得
        # ========================================

        metadata = parse_image_metadata(article)

        # ----------------------------------------
        # メタデータが欠落している場合のみ再取得
        # 記事本文の再生成・リライトは行わない
        # ----------------------------------------

        if not is_valid_image_metadata(metadata):

            log_warning(
                "画像メタデータが正常に取得できませんでした。"
                "画像メタデータのみ再取得します。"
            )

            metadata_prompt = f"""
以下の記事について、アイキャッチ画像生成に必要な
画像メタデータだけを判定してください。

記事本文：
{article}

以下の形式で必ず2行だけ出力してください。

画像カテゴリ：〇〇
強調キーワード：〇〇、〇〇

画像カテゴリは以下から必ず1つだけ選択してください。

・AIチャット
・AI画像・デザイン
・動画編集・ショート動画
・AI副業・マネタイズ
・AI自動化・業務効率化

強調キーワードは、記事タイトルに実際に含まれている
重要なキーワードを0〜3個選択してください。

適切な強調キーワードがない場合は、
「強調キーワード：なし」
としてください。

記事本文や説明文は出力せず、
必ず画像カテゴリと強調キーワードの2行だけを出力してください。
"""

            try:

                metadata_response = call_gemini(
                    client,
                    model="gemini-2.5-flash",
                    contents=metadata_prompt,
                )

                metadata_text = metadata_response.text.strip()

                # 元の記事にメタデータだけを追加して再解析
                metadata = parse_image_metadata(
                    article
                    + "\n\n"
                    + metadata_text
                )

                if is_valid_image_metadata(metadata):

                    log_info(
                        "画像メタデータの再取得に成功しました。"
                    )

                else:

                    log_warning(
                        "画像メタデータの再取得にも失敗しました。"
                    )

            except GeminiDailyQuotaExceeded:
                raise

            except Exception as e:

                log_warning(
                    f"画像メタデータ再取得エラー：{e}"
                )

        # ----------------------------------------
        # 最終結果
        # ----------------------------------------

        article = metadata["article"]
        image_category = metadata["image_category"]
        highlight_keywords = metadata["highlight_keywords"]

        log_info(
            f"画像カテゴリ：{image_category}"
        )

        log_info(
            f"強調キーワード：{highlight_keywords}"
        )


    return {
        "article": article,
        "evaluation": evaluation,
        "score": score,
        "seo_score": seo_score,
        "duplicate_result": duplicate_result,
        "latest_result": latest_result,
        "image_category": image_category,
        "highlight_keywords": highlight_keywords,
    }