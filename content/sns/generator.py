from content.sns.prompt import get_sns_prompt

from utils.gemini_client import call_gemini


def generate_sns_posts(client, article):
    """
    記事をもとにX・Threads・Instagram投稿を生成する。
    """

    prompt = get_sns_prompt(article)

    response = call_gemini(
        client,
        model="gemini-2.5-flash",
        contents=prompt,
    )

    text = response.text.strip()

    x_post = ""
    threads_post = ""
    instagram_post = ""

    # ========================================
    # X
    # ========================================

    if "【X】" in text:

        x_part = text.split("【X】", 1)[1]

        if "【Threads】" in x_part:
            x_post = x_part.split(
                "【Threads】",
                1
            )[0].strip()

    # ========================================
    # Threads
    # ========================================

    if "【Threads】" in text:

        threads_part = text.split(
            "【Threads】",
            1
        )[1]

        if "【Instagram】" in threads_part:
            threads_post = threads_part.split(
                "【Instagram】",
                1
            )[0].strip()

    # ========================================
    # Instagram
    # ========================================

    if "【Instagram】" in text:

        instagram_post = text.split(
            "【Instagram】",
            1
        )[1].strip()

    return (
        x_post,
        threads_post,
        instagram_post,
    )