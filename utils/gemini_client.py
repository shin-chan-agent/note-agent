import time

from config import MAX_RETRY
from config import GEMINI_RETRY_WAIT

from utils.logger import log_warning


RETRY_ERRORS = (
    "429",
    "RESOURCE_EXHAUSTED",
    "503",
    "UNAVAILABLE",
    "Gemini returned empty response",
)

# 日次クォータ超過を示すエラー
DAILY_QUOTA_ERRORS = (
    "GenerateRequestsPerDayPerProject-FreeTier",
    "generate_content_free_tier_requests",
    "You exceeded your current quota",
)


def call_gemini(
    client,
    *,
    model,
    contents,
    config=None,
    max_retry=MAX_RETRY,
    wait=GEMINI_RETRY_WAIT,
):
    """
    Gemini API共通呼び出し

    429 RESOURCE_EXHAUSTED
    503 UNAVAILABLE
    空レスポンスを自動リトライする。

    ただし、日次クォータ超過の場合は
    リトライせず即座に例外を発生させる。
    """

    for attempt in range(max_retry):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

            if not response.text:
                raise Exception(
                    "Gemini returned empty response"
                )

            return response

        except Exception as e:
            error = str(e)

            # --------------------------------
            # 日次クォータ超過
            # --------------------------------
            daily_quota_exceeded = any(
                keyword in error
                for keyword in DAILY_QUOTA_ERRORS
            )

            if daily_quota_exceeded:
                log_warning(
                    "Gemini APIの日次クォータを超過しました。"
                    "リトライせず処理を終了します。"
                )
                raise

            # --------------------------------
            # リトライ対象か判定
            # --------------------------------
            retry = any(
                keyword in error
                for keyword in RETRY_ERRORS
            )

            if not retry:
                raise

            log_warning(
                f"Gemini APIリトライ "
                f"({attempt + 1}/{max_retry}) : {error}"
            )

            if attempt == max_retry - 1:
                raise

            log_warning(
                f"{wait}秒待機します..."
            )

            time.sleep(wait)