import time


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
    max_retry=3,
    wait=60,
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

            print(
                f"Gemini APIリトライ "
                f"({attempt + 1}/{max_retry}) : {error}"
            )

            if attempt == max_retry - 1:
                raise

            print(f"{wait}秒待機します...")
            time.sleep(wait)
