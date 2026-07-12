from google import genai

def rewrite_article(client, article, latest_info, evaluation):

    prompt = f"""
以下の記事を改善してください。

【最新情報】
{latest_info}

【記事】
{article}

【改善点】
{evaluation}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text