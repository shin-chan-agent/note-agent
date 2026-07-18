from content.sns.prompt import get_sns_prompt


def generate_sns_posts(client, article):
    prompt = get_sns_prompt(article)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    text = response.text.strip()

    x_post = ""
    instagram_post = ""

    if "【Instagram】" in text:
        x_part, instagram_part = text.split("【Instagram】", 1)

        x_post = x_part.replace("【X】", "").strip()
        instagram_post = instagram_part.strip()

    return x_post, instagram_post