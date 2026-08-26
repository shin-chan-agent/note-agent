from content.video.prompt import get_video_prompt

from utils.gemini_client import call_gemini


def generate_video_scripts(client, article):
    """
    記事から30秒・60秒の
    ショート動画台本を生成する。
    """

    prompt = get_video_prompt(article)

    response = call_gemini(
        client,
        model="gemini-2.5-flash",
        contents=prompt,
    )

    text = response.text.strip()

    video_30 = ""
    video_60 = ""

    if "【60秒】" in text:

        part_30, part_60 = text.split(
            "【60秒】",
            1,
        )

        video_30 = (
            part_30
            .replace("【30秒】", "")
            .strip()
        )

        video_60 = part_60.strip()

    else:

        video_30 = text

    return video_30, video_60