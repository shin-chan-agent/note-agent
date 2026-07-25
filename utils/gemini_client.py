import time

from config import MAX_RETRY
from config import GEMINI_RETRY_WAIT

from utils.logger import log_warning


RETRY_ERRORS = (
    "429",
    "RESOURCE_EXHAUSTED",
    "503",
    "UNAVAILABLE",
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
    を自動リトライする。
    """

    for attempt in range(max_retry):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

        except Exception as e:
            error = str(e)

            retry = any(keyword in error for keyword in RETRY_ERRORS)

            if not retry:
                raise

            log_warning(
                f"Gemini APIリトライ "
                f"({attempt + 1}/{max_retry}) : {error}"
            )

            if attempt == max_retry - 1:
                raise

            log_warning(f"{wait}秒待機します...")

            time.sleep(wait)
