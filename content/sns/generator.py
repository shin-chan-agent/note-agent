from content.sns.prompt import get_sns_prompt

from utils.gemini_client import call_gemini

from config import GEMINI_MODEL_SNS


def generate_sns_posts(client, article):
    prompt = get_sns_prompt(article)

    response = call_gemini(
        client,
        model=GEMINI_MODEL_SNS,
        contents=prompt,
    )

    text = response.text.strip()

    x_post = ""
    threads_post = ""
    instagram_post = ""

    if "【Threads】" in text:

        before_threads, after_threads = text.split(
            "【Threads】",
            1,
        )

        x_post = (
            before_threads
            .replace("【X】", "")
            .strip()
        )

        if "【Instagram】" in after_threads:

            threads_part, instagram_part = after_threads.split(
                "【Instagram】",
                1,
            )

            threads_post = threads_part.strip()
            instagram_post = instagram_part.strip()

        else:

            threads_post = after_threads.strip()

    elif "【Instagram】" in text:

        x_part, instagram_part = text.split(
            "【Instagram】",
            1,
        )

        x_post = (
            x_part
            .replace("【X】", "")
            .strip()
        )

        instagram_post = instagram_part.strip()

    else:

        x_post = text

    return (
        x_post,
        threads_post,
        instagram_post,
    )