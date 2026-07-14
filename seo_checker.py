from google import genai


def seo_check(client, article):

    prompt = f"""
以下の記事のSEOを評価してください。

【記事】
{article}

以下の項目を100点満点で評価してください。

・タイトルに主要キーワードが自然に含まれているか
・タイトルがクリックしたくなる内容か
・導入文100文字以内に主要キーワードがあるか
・H2・H3にSEOキーワードが自然に含まれているか
・見出しだけ読んでも内容が分かる構成か
・Google検索とnote検索の両方を意識できているか
・キーワードを不自然に詰め込み過ぎていないか

以下の形式で必ず出力してください。

SCORE:○○

改善点
・〇〇
・〇〇

改善点が無ければ

SCORE:100

改善点
なし

だけを出力してください。
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text