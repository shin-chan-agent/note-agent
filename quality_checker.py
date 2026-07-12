def evaluate_article(client, article):
    prompt = f"""
以下の記事を100点満点で評価してください。

{article}

評価項目

各項目を20点満点で採点してください。

・SEO（検索されやすいタイトル、見出し、キーワード配置）
・読みやすさ（スマホで読みやすい文章構成）
・初心者への分かりやすさ（専門用語の説明、具体例）
・具体性（実践方法、手順、数字、事例）
・独自性（他の記事との差別化）

合計100点で評価してください。

最初の1行は必ず

SCORE:○○

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
