from google import genai

def rewrite_latest_info(client, article, latest_info, latest_check):

    prompt = f"""
以下はGoogle Searchで取得した最新情報です。

【最新情報】
{latest_info}

以下の記事を修正してください。

【記事】
{article}

【修正内容】
{latest_check}

Google Searchで取得した最新情報を最優先してください。
記事全体を書き直してください。
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text
