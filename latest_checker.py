from google.genai import types


def latest_check(client, article):
    prompt = f"""
以下の記事について、Google Searchを利用して最新の公式情報と照合してください。

【記事】
{article}

以下を確認してください。

・料金
・無料版／有料版
・モデル名
・機能
・仕様

公式サイトまたは公式発表を優先してください。

問題がなければ

LATEST:OK

問題があれば

LATEST:NG

と出力し、修正すべき箇所を箇条書きで出力してください。

出力形式は必ず次のようにしてください。

LATEST:OK

または

LATEST:NG

改善点
・○○
・○○
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(
                    google_search=types.GoogleSearch()
                )
            ]
        )
    )

    return response.text