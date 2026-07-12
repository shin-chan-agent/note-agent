from google import genai

def rewrite_article(client, article, latest_info, evaluation):

    prompt = f"""
以下はGoogle Searchで取得した最新情報です。

【最新情報】
{latest_info}

以下の記事が最新情報と矛盾していないか確認してください。

【記事】
{article}

以下の基準で厳密に確認してください。

・料金
・無料版/有料版の違い
・モデル名
・利用可能機能
・サービス仕様
・提供状況

1つでも古い情報や誤情報があればNGにしてください。

もし矛盾があれば

NG

と書き、
修正すべき箇所だけを具体的に書いてください。

矛盾がなければ

OK

だけを出力してください。
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text
