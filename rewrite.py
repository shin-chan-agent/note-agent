from google import genai

def rewrite_article(client, article, latest_info, evaluation):

    prompt = f"""
以下の記事を改善してください。

【最新情報】
{latest_info}

上記の最新情報は維持してください。
古い情報へ戻さないでください。

【記事】
{article}

【改善点】
{evaluation}

改善点を反映しながら、
記事全体を書き直してください。

記事の構成・文字数・固定記事への案内・ハッシュタグは維持してください。
現在の記事より品質が下がる書き換えは禁止します。
改善点のみを修正し、それ以外の品質は維持してください。
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text
