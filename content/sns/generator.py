from content.sns.prompt import (
    get_x_prompt,
    get_instagram_prompt,
)


def generate_x_post(client, article):
    prompt = get_x_prompt(article)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text.strip()


def generate_instagram_post(client, article):
    prompt = get_instagram_prompt(article)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text.strip()