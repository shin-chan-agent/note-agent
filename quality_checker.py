from google.genai import types

def quality_check(client, article, past_articles):
    prompt = f"""
以下の記事を総合評価してください。

【記事】
{article}

以下の3項目を評価してください。

①品質（100点満点）
②SEO（100点満点）
③最新情報との整合性

---

【品質評価】

次の5項目を20点満点で採点してください。

・読みやすさ
・独自性
・初心者への分かりやすさ
・具体性
・情報の正確性

合計100点満点で評価してください。

---

【SEO評価】

100点満点で評価してください。

以下を確認してください。

・タイトルに主要キーワードが自然に含まれているか
・タイトルがクリックしたくなる内容か
・導入文100文字以内に主要キーワードがあるか
・H2・H3にSEOキーワードが自然に含まれているか
・見出しだけ読んでも内容が分かる構成か
・Google検索とnote検索の両方を意識できているか
・キーワードを不自然に詰め込み過ぎていないか

---

【最新情報チェック】

Google Searchで最新情報を確認し、

・料金
・無料版／有料版
・モデル名
・機能
・仕様

に誤りがないか確認してください。

---

【過去記事】

{past_articles}

---

【重複チェック】

上記の過去記事と比較し、

・テーマ
・切り口
・構成
・タイトル
・見出し
・具体例
・まとめ

が実質的に重複していないか評価してください。

問題なければ

DUPLICATE:OK

重複している場合は

DUPLICATE:NG

と出力し、
続けて重複している理由を具体的に説明してください。

---

【出力形式】

必ず以下の形式で出力してください。

SCORE:◯◯
SEO:◯◯
LATEST:OK または NG
DUPLICATE:OK  または　NG

改善点
・○○
・○○
・○○

最新情報に問題がある場合は

LATEST:NG

とし、
修正箇所を改善点へ含めてください。

改善不要なら

改善点なし

とだけ書いてください。

DUPLICATE:NG の場合は、

どの記事と、どこが重複しているのかを
改善点へ具体的に記載してください。
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