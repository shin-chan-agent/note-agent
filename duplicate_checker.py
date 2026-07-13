from google import genai


def check_duplicate(client, past_articles, article):

    prompt = f"""
あなたは記事の重複判定を行う編集者です。

以下は過去の記事です。

【過去記事】
{past_articles}

以下は今回の記事です。

【今回の記事】
{article}

以下の項目を総合的に比較してください。

・タイトル
・導入文
・記事構成
・見出し
・説明の流れ
・具体例
・まとめ
・読者への提案

文章が一部違っていても、
内容や構成が70%以上似ている場合は重複と判断してください。

重複なら

NG

と出力し、
どこが似ているかを3点以内で具体的に書いてください。

重複していなければ

OK

だけを出力してください。
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text