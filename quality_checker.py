from google import genai
from google.genai import types

def quality_check(client, article):
    prompt = f"""
以下の記事を100点満点で評価してください。

{article}

【評価項目】
次の各項目を採点してください。

・SEO
・読みやすさ
・独自性
・初心者への分かりやすさ
・具体性

【評価ルール】
各項目それぞれを20点満点とし、
合計100点満点で評価してください。

情報の正確性を最優先で評価してください。

料金・モデル名・機能・仕様などは、必要に応じて
Google Searchで最新の公式情報を確認したうえで
評価してください。

記事の情報が最新の公式情報と一致している場合は、
情報の正確性を理由に減点しないでください。

【出力ルール】
最初の1行は必ず

SCORE:○○

という形式だけで出力してください。

続けて改善点を重要なものから最大3つ挙げて下さい。
改善不要な場合は「改善点なし」と出力してください。
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    return response.text