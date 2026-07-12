from google import genai

def quality_check(client, article):
    prompt = f"""
以下の記事を100点満点で評価してください。

{article}

評価項目

各項目を20点満点で採点してください。

・SEO
・読みやすさ
・初心者への分かりやすさ
・具体性
・独自性

合計100点で評価してください。

最初の1行は必ず

SCORE:○○

という形式だけで出力してください。

改善点は重要なものだけを最大3つ挙げてください。
改善不要な場合は「改善点なし」と出力してください。
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text
という形式だけで出力してください。

改善点は重要なものだけを最大3つ挙げてください。
改善点は具体的に書いてください。
改善不要な場合は「改善点なし」と出力してください。
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text
