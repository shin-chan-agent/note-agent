import os
import re
import time
import requests
from google import genai
from google.genai import types

from theme_manager import get_theme_and_angle


def evaluate_article(client, article):
    prompt = f"""
以下の記事を100点満点で評価してください。

{article}

評価項目
・SEO
・読みやすさ
・初心者への分かりやすさ
・具体性
・オリジナリティ
・最後まで読みたくなる構成

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


def check_latest_info(client, latest_info, article):
    prompt = f"""
以下はGoogle Searchで取得した最新情報です。

【最新情報】
{latest_info}

以下の記事が最新情報と矛盾していないか確認してください。

【記事】
{article}

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


def extract_score(text):
    m = re.search(r"SCORE\s*:\s*(\d+)", text, re.IGNORECASE)

    if m:
        return int(m.group(1))

    return 0


def get_search_query(theme):
    if "ChatGPT" in theme:
        return "ChatGPT 最新 GPT-5 無料版 Plus Pro Teams Enterprise 料金 機能"

    elif "Gemini" in theme:
        return "Google Gemini 最新 Gemini 2.5 Flash Pro 料金 AI Studio 機能"

    elif "Claude" in theme:
        return "Claude 最新 Sonnet Opus 料金 機能"

    elif "Canva" in theme:
        return "Canva 最新 AI機能 Magic Studio Visual Suite 料金"

    elif "CapCut" in theme:
        return "CapCut 最新 AI機能 料金 商用利用"

    elif "note" in theme:
        return "note 最新 アルゴリズム SEO 仕様変更"

    elif "Instagram" in theme:
        return "Instagram 最新 リール アルゴリズム"

    elif "X" in theme:
        return "X 最新 アルゴリズム 収益化"

    elif "AI副業" in theme:
        return "AI副業 最新 トレンド AIツール"

    elif "ショート動画" in theme:
        return "ショート動画 最新 トレンド YouTube Shorts Instagram Reels TikTok"

    else:
        return f"{theme} 最新"


def get_latest_info(client, theme):
    query = get_search_query(theme)

    prompt = f"""
以下の検索キーワードについて最新情報を調査してください。

検索キーワード
{query}

以下を優先してください。

・最新の料金プラン
・利用できるモデル
・新機能
・仕様変更
・注意点

記事執筆で使えるように、
箇条書きで500〜1000文字程度にまとめてください。
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    return response.text


def split_text(text, max_length=4800):
    return [
        text[i:i + max_length]
        for i in range(0, len(text), max_length)
    ]


def generate_and_send_line():
    # 最新のライブラリでGeminiで記事を生成
    # 環境変数から自動でAPIキーを読み込む仕様になりました

    client = genai.Client()

    theme, angle = get_theme_and_angle()

    for _ in range(3):
        try:
            latest_info = get_latest_info(client, theme)
            break
        except Exception as e:
            print(f"Google Searchを再試行します... {e}")
            time.sleep(5)
    else:
        raise ValueError("最新情報を取得できませんでした")

    print("===== 最新情報 =====")
    print(latest_info)  

    prompt = (
        "noteに投稿する記事を1本執筆してください。\n"
        "記事はMarkdown形式で出力してください。\n\n"

        "【最新情報】\n"
        f"{latest_info}\n\n"
        "上記はGoogle検索で取得した最新情報です。\n"
        "記事では必ずこの情報を優先してください。\n\n"

        f"今回の記事テーマは『{theme}』です。\n"
        f"記事の切り口は『{angle}』です。\n"
        f"記事全体を『{angle}』という視点で構成してください。\n\n"

        "【最新情報のルール】\n"
        "・Google Searchで取得した情報を最優先してください。\n"
        "・記事中の料金・プラン・対応モデル・バージョン・機能・仕様は、現時点で確認できる情報のみを使用してください。\n"
        "・古い情報と最新情報が異なる場合は、必ず最新情報を採用してください。\n"
        "・情報に確信が持てない場合は、推測で補完せず、その内容には触れないでください。\n"
        "・記事中で「現時点では」「現在」などの表現は必要な場合のみ使用してください。\n"

        "【基本ルール】\n"
        "・確信の持てる情報のみを掲載してください。\n"
        "・不明な情報や推測は断定しないでください。\n"
        "・AI特有の不自然な表現（『こんにちは』『さあ始めましょう』『〜ですよね！』『〜していきます』など）は使用しないでください。\n"
        "・キャラクター設定や名前は付けないでください。\n"
        "・同じ表現や言い回しを繰り返さず、自然な日本語で執筆してください。\n"
        "・抽象論だけで終わらせず、具体例・実践例を交えて説明してください。\n"
        "・専門用語を使う場合は初心者にも分かるよう簡潔に説明してください。\n\n"

        "【記事構成】\n"
        "・タイトル\n"
        "・導入文\n"
        "・本文（H2・H3見出しを使用）\n"
        "・まとめ\n"
        "・固定記事への案内\n"
        "・ハッシュタグ5個\n\n"

        "【タイトル】\n"
        "・32〜40文字程度にしてください。\n"
        "・SEOを意識したタイトルにしてください。\n"
        "・タイトル候補を内部で5案考え、最もクリック率が高いものだけを出力してください。\n"
        "・タイトルには以下のキーワードから2つ以上を自然に含めてください。\n"
        "『AI副業』『ショート動画』『自動化』『タイパ』『コスパ』『ロードマップ』\n"
        "・キーワードを不自然に詰め込まないでください。\n\n"

        "【SEO】\n"
        "・Google検索とnote内検索の両方を意識してください。\n"
        "・導入文100文字以内に主要キーワードを自然に含めてください。\n"
        "・H2・H3見出しにもSEOキーワードを自然に含めてください。\n"
        "・SEOキーワードを過剰に繰り返さないでください。\n\n"

        "【導入文】\n"
        "・最初の3行で読者の悩み・状況・疑問から書き始めてください。\n"
        "・続きを読みたくなる内容にしてください。\n"
        "・あいさつは不要です。\n\n"

        "【本文】\n"
        "・記事全体で2,500〜3,500文字程度にしてください。\n"
        "・初心者が知りたい内容を漏れなく網羅してください。\n"
        "・読者の疑問を先回りして回答してください。\n"
        "・必要に応じて箇条書き・番号付きリスト・表を使い、スマホでも読みやすくしてください。\n"
        "・読者が今日から実践できる具体的な行動を1つ以上提案してください。\n"
        "・過去の記事とタイトル・導入文・見出し・説明の順番・具体例・まとめが似ないよう工夫してください。\n\n"

        "【まとめ】\n"
        "・記事の要点を3〜5項目に整理してください。\n"
        "・読者が次の行動を起こしたくなる内容で締めてください。\n\n"

        "【固定記事への案内】\n"
        "記事内容から自然につながる流れで、最後に以下の文章をそのまま掲載してください。\n\n"

        "AI×ショート動画で最速でマネタイズ（収益化）する具体的な手順と、豪華40大特典の受け取り方は、下記の固定記事で詳しく解説しています。\n"
        "↓↓↓\n"
        "[【初期費用ゼロ】スキルなしの会社員や主婦がショート動画で最速で月収10万を達成したロードマップ]\n"
        "(https://note.com/shin_chan_ai/n/n7bec364e6cd2)\n\n"

        "【ハッシュタグ】\n"
        "記事内容に最適なハッシュタグを5つ付けてください。\n\n"

        "【その他】\n"
        "・『ゼロイチ』は『マネタイズにおける最初の1円』という意味でのみ使用してください。\n"
        "・最後まで読まれやすく、保存したくなる品質の記事を作成してください。\n"
    )


    MIN_SCORE = 90
    MAX_REWRITE = 3

    MAX_RETRY = 3

    for attempt in range(MAX_RETRY):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )

            article = response.text

            # 評価だけリトライ
            for _ in range(3):
                evaluation = evaluate_article(client, article)
                score = extract_score(evaluation)

                if score != 0:
                    break

                print("評価のみ再実行します...")
                time.sleep(5)

            if score == 0:
                raise ValueError("評価結果からスコアを取得できませんでした")

            print(f"記事スコア：{score}")

            for rewrite in range(MAX_REWRITE):

                if score >= MIN_SCORE:
                    print("品質基準をクリアしました。")
                    break

                print(f"{rewrite + 1}回目のリライトを実施します。")

                rewrite_prompt = f"""
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
                    contents=rewrite_prompt,
                )

                article = response.text

                # 評価だけリトライ
                for _ in range(3):
                    evaluation = evaluate_article(client, article)
                    score = extract_score(evaluation)

                    if score != 0:
                        break

                    print("評価のみ再実行します...")
                    time.sleep(5)

                if score == 0:
                    raise ValueError("評価結果からスコアを取得できませんでした")

                print(f"リライト後スコア：{score}")

                if re.search(r"改善点\s*[:：]?\s*なし", evaluation):
                    print("改善点がないためリライトを終了します。")
                    break

                if score >= MIN_SCORE:
                    print("品質基準をクリアしました。")
                    break

            if score < MIN_SCORE:
                print("最大回数リライトしましたが品質基準に届きませんでした。")


            latest_check = check_latest_info(client, latest_info, article)

            print(latest_check)

            if latest_check.strip().startswith("NG"):
                print("最新情報との矛盾を修正します。")

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"""
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
    )

                article = response.text

                for _ in range(3):
                    evaluation = evaluate_article(client, article)
                    score = extract_score(evaluation)

                    if score != 0:
                        break

                    print("最終評価を再実行します...")
                    time.sleep(5)

                print(f"最終スコア：{score}")

            break

        except Exception as e:
            print(f"Geminiエラー（{attempt + 1}回目）：{e}")

            if attempt == MAX_RETRY - 1:
                raise

            print("30秒後に再試行します...")
            time.sleep(30)

    status = (
        "✅ 品質基準クリア"
        if score >= MIN_SCORE
        else "⚠️ 品質基準未達"
    )
    
    # LINE公式アカウント（Messaging API）を使ってメッセージを送信
    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    user_id = os.environ["LINE_USER_ID"]
    
    line_api_url = "https://api.line.me/v2/bot/message/push"
    
    # 送信するメッセージの組み立て
    article_message = f"""🤖【Gemini生成のnote原稿】🤖

{status}

最終スコア：{score}点

--------------------

{article}
"""

    evaluation_message = f"""📊【AI評価】

{evaluation}
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
   
    messages = []

    for part in split_text(article_message):
        messages.append({
            "type": "text",
            "text": part
        })

    messages.append({
        "type": "text",
        "text": evaluation_message
    })

    payload = {
        "to": user_id,
        "messages": messages
    }


    try:
        response_line = requests.post(line_api_url, headers=headers, json=payload)

        if response_line.status_code == 200:
            print("Success: Message sent to LINE safely!")

        else:
            print(f"Error: LINE API returned status code {response_line.status_code}")

            print(response_line.text)
    except Exception as e:

        print(f"Error: {e}")

        raise e


if __name__ == "__main__":
    generate_and_send_line()
