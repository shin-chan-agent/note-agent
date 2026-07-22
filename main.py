import os
import re
import time
import requests

from google import genai
from google.genai import types
from theme_manager import get_theme_and_angle

from quality_checker import quality_check
from latest_checker import latest_check

from rewrite import rewrite_article

from article_history import load_articles, save_article

from content.sns.generator import generate_sns_posts

from utils.gemini_client import call_gemini


def extract_score(text):
    m = re.search(r"SCORE\s*:\s*(\d+)", text, re.IGNORECASE)

    if m:
        return int(m.group(1))

    return 0


def extract_seo_score(text):
    m = re.search(r"SEO\s*:\s*(\d+)", text, re.IGNORECASE)
    return int(m.group(1)) if m else 0


def extract_latest_result(text):
    m = re.search(r"LATEST\s*:\s*(OK|NG)", text, re.IGNORECASE)
    return m.group(1).upper() if m else "NG"


def extract_duplicate_result(text):
    m = re.search(r"DUPLICATE\s*:\s*(OK|NG)", text, re.IGNORECASE)
    return m.group(1).upper() if m else "NG"


def extract_improvements(text):
    m = re.search(
        r"改善点\s*[:：]?\s*(.*)",
        text,
        re.DOTALL,
    )

    if m:
        return m.group(1).strip()

    return ""


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

    response = call_gemini(
        client,
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())]
        ),
    )

    return response.text


def split_text(text, max_length=4800):
    # タイトル・導入文を取得
    match = re.search(r"(.*?)(?=\n### |\n## |\Z)", text, re.DOTALL)

    if match:
        header = match.group(1).strip()
        body = text[len(match.group(1)):].strip()
    else:
        header = ""
        body = text

    # H3単位で分割
    sections = re.split(r"(?=\n### )", body)

    parts = []
    current = header

    for section in sections:

        section = section.strip()

        if not section:
            continue

        # 入るなら追加
        if len(current) + len(section) + 2 <= max_length:

            if current:
                current += "\n\n"

            current += section
            continue

        # 一旦保存
        if current:
            parts.append(current)

        # H3単体が長すぎる場合
        if len(section) > max_length:

            current = ""

            paragraphs = section.split("\n\n")

            for paragraph in paragraphs:

                if len(current) + len(paragraph) + 2 <= max_length:

                    if current:
                        current += "\n\n"

                    current += paragraph

                else:

                    if current:
                        parts.append(current)

                    # 段落でも長い場合
                    if len(paragraph) > max_length:

                        current = ""

                        lines = paragraph.split("\n")

                        for line in lines:

                            if len(current) + len(line) + 1 <= max_length:

                                if current:
                                    current += "\n"

                                current += line

                            else:

                                if current:
                                    parts.append(current)

                                while len(line) > max_length:
                                    parts.append(line[:max_length])
                                    line = line[max_length:]

                                current = line

                    else:
                        current = paragraph

        else:
            current = section

    if current:
        parts.append(current)

    # 【1/○】を付与
    total = len(parts)

    return [
        f"【{i + 1}/{total}】\n\n{part}"
        for i, part in enumerate(parts)
    ]


def generate_and_send_line():
    # 最新のライブラリでGeminiで記事を生成
    # 環境変数から自動でAPIキーを読み込む仕様になりました

    client = genai.Client()

    theme, angle = get_theme_and_angle()

    past_articles = load_articles()

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

    past_articles_text = "\n\n".join(
        article["title"] for article in past_articles[-20:]
)

    prompt = f"""

noteに投稿する記事を1本執筆してください。
記事はMarkdown形式で出力してください。

【過去記事タイトル】
{past_articles_text}

上記の過去記事とはタイトル・切り口・構成・具体例・まとめが似ない記事を作成してください。
同じ内容を言い換えただけの記事は禁止です。

【最新情報】
{latest_info}

上記はGoogle検索で取得した最新情報です。
記事では必ずこの情報を優先してください。

【記事全体の軸】
この記事は「AI×ショート動画で収益化するための実践情報」を発信するメディアの記事です。
今回のテーマがChatGPT・Gemini・Canva・CapCutなど何であっても、必ず「AI×ショート動画による収益化」という文脈で解説してください。

単なるツール紹介にはせず、
　・ショート動画制作でどう活用するのか
　・副業・収益化にどう役立つのか
　・初心者はどのように使えばよいのか
　・実践例
　・AI×ショート動画のワークフロー
を必ず盛り込んでください。

記事全体を通して「AI×ショート動画で収益化する」という軸を維持してください。
ツールの専門記事ではないので、専門的な解説や深掘りはせず「AI×ショート動画」の固定記事に繋げる記事にしてください。

【記事のテーマと切り口】
今回の記事テーマは『{theme}』です。
記事の切り口は『{angle}』です。
記事全体を『{angle}』という視点で構成してください。

【最新情報のルール】
・Google Searchで取得した情報を最優先してください。
・記事中の料金・プラン・対応モデル・バージョン・機能・仕様は、現時点で確認できる情報のみを使用してください。
・古い情報と最新情報が異なる場合は、必ず最新情報を採用してください。
・情報に確信が持てない場合は、推測で補完せず、その内容には触れないでください。
・記事中で「現時点では」「現在」などの表現は必要な場合のみ使用してください。

【基本ルール】
・確信の持てる情報のみを掲載してください。
・不明な情報や推測は断定しないでください。
・AI特有の不自然な表現（『こんにちは』『さあ始めましょう』『〜ですよね！』『〜していきます』など）は使用しないでください。
・キャラクター設定や名前は付けないでください。

・同じ表現や言い回しを繰り返さず、自然な日本語で執筆してください。
・抽象論だけで終わらせず、具体例・実践例を交えて説明してください。
・専門用語を使う場合は初心者にも分かるよう簡潔に説明してください。

【記事構成】
以下の順番を必ず守って出力してください。
　①タイトル
　②導入文
　③本文（H2・H3見出しを使用）
　④まとめ\n"
　⑤固定記事への案内\n"
　⑥ハッシュタグ5個\n\n"
タイトルを省略することは禁止です。\n"
導入文や本文から開始してはいけません。\n\n"

【タイトル】
・32〜40文字程度にしてください。
・記事の最初の1行に必ずタイトルを出力してください。
・タイトルには必ず「タイトル：」という見出しを付けてください。
・タイトルがない記事は不完全な記事として扱います。
・SEOを意識したタイトルにしてください。
・タイトル候補を内部で5案考え、最もクリック率が高いものだけを出力してください。
・タイトルには以下のキーワードから1つ以上を自然に含めてください。
　『AI副業』『ショート動画』『自動化』『コスパ』『タイパ』『ロードマップ』
・キーワードを不自然に詰め込まないでください。

【SEO】
・Google検索とnote内検索の両方を意識してください。
・導入文100文字以内に主要キーワードを自然に含めてください。
・H2・H3見出しにもSEOキーワードを自然に含めてください。
・SEOキーワードを過剰に繰り返さないでください。

【導入文】
・最初の3行で読者の悩み・状況・疑問から書き始めてください。
・続きを読みたくなる内容にしてください。
・あいさつは不要です。

【本文】
・記事全体は2,500〜5,000文字を目安にしてください。
・テーマに対して必要十分な情報量を確保してください。
・文字数を増やすことを目的にせず、不要な説明や同じ内容の繰り返しは避けてください。
・情報が少ないテーマでは簡潔に、情報量が多いテーマでは十分な解説を行ってください。

・各H2またはH3見出しで、AIツールをショート動画制作・運用・収益化に結び付けて解説してください。
・読者の疑問を先回りして回答してください。
・必要に応じて箇条書き・番号付きリスト・表を使い、スマホでも読みやすくしてください。
・読者が今日から実践できる具体的な行動を1つ以上提案してください。
・過去の記事とタイトル・導入文・見出し・説明の順番・具体例・まとめが似ないよう工夫してください。

【まとめ】
・記事の要点を3〜5項目に整理してください。
・読者が次の行動を起こしたくなる内容で締めてください。
・「AIツール単体を学ぶことが目的ではなく、AI×ショート動画として組み合わせることで収益化しやすくなる」という流れで締めてください。
・その流れから固定記事への案内へ自然につなげてください。

【固定記事への案内】
記事内容から自然につながる流れで、最後に以下の文章をそのまま掲載してください。

AI×ショート動画で最速でマネタイズ（収益化）する具体的な手順と、豪華40大特典の受け取り方を下記の固定記事で詳しく解説しています。
　↓↓↓
【初期費用ゼロ】スキルなしの会社員や主婦がショート動画で最速で月収10万を達成したロードマップ

【ハッシュタグ】
記事内容に最適なハッシュタグを5つ付けてください。
ハッシュタグは半角スペースを1つ挟んで横並びで書いてください。

【その他】
・『ゼロイチ』は『マネタイズにおける最初の1円』という意味でのみ使用してください。
・最後まで読まれやすく、保存したくなる品質の記事を作成してください。

    """


    MIN_SCORE = 90
    MIN_SEO_SCORE = 90
    MAX_REWRITE = 3

    MAX_RETRY = 3

    for attempt in range(MAX_RETRY):
        try:
            response = call_gemini(
                client,
                model="gemini-2.5-flash",
                contents=prompt,
            )

            article = response.text

            # タイトル欠落チェック
            if not re.search(r"^タイトル[:：]", article):
                print("タイトル欠落。再生成します。")
                continue

            # 固定記事案内チェック
            fixed_text = (
                "AI×ショート動画で最速でマネタイズ（収益化）する具体的な手順と、"
                "豪華40大特典の受け取り方を下記の固定記事で詳しく解説しています。"
            )

            if fixed_text not in article:
                print("固定記事案内欠落。再生成します。")
                continue

            article_length = len(article)

            # 文字数不足チェック
            if article_length < 2000:
                print("記事文字数不足。再生成します。")
                continue

            # 評価だけリトライ
            for _ in range(3):
                evaluation = quality_check(
                    client,
                    article,
                    past_articles_text,
                )

                latest_evaluation = latest_check(
                    client,
                    article,
                )

                score = extract_score(evaluation)
                seo_score = extract_seo_score(evaluation)
                duplicate_result = extract_duplicate_result(evaluation)

                latest_result = extract_latest_result(latest_evaluation)

                if score != 0:
                    break

                print("評価のみ再実行します...")
                time.sleep(5)

            if score == 0:
                raise ValueError("評価結果からスコアを取得できませんでした")

            print(f"記事スコア：{score}")

            print(evaluation)
            print(f"品質スコア：{score}")
            print(f"SEOスコア：{seo_score}")
            print(f"最新情報：{latest_result}")

            for rewrite in range(MAX_REWRITE):

                if (
                    score >= MIN_SCORE
                    and seo_score >= MIN_SEO_SCORE
                    and latest_result == "OK"
                    and duplicate_result == "OK"
                ):
                    print("すべての品質基準をクリアしました。")
                    break


                print(f"{rewrite + 1}回目のリライトを実施します。")

                rewrite_prompt = extract_improvements(evaluation)

                if latest_result == "NG":
                    latest_improvements = extract_improvements(latest_evaluation)

                    if latest_improvements:
                        if rewrite_prompt:
                            rewrite_prompt += "\n\n"
                        rewrite_prompt += latest_improvements
                if not rewrite_prompt.strip():
                    print("改善指示がないためリライトを終了します。")
                    break

                article = rewrite_article(
                    client,
                    article,
                    latest_info,
                    rewrite_prompt,
                )


                # 評価だけリトライ
                for _ in range(3):
                    evaluation = quality_check(
                        client,
                        article,
                        past_articles_text,
                    )

                    latest_evaluation = latest_check(
                        client,
                        article,
                    )

                    score = extract_score(evaluation)
                    seo_score = extract_seo_score(evaluation)
                    duplicate_result = extract_duplicate_result(evaluation)

                    latest_result = extract_latest_result(latest_evaluation)

                    if score != 0:
                        break

                    print("評価のみ再実行します...")
                    time.sleep(5)

                if score == 0:
                    raise ValueError("評価結果からスコアを取得できませんでした")

                print(f"リライト後スコア：{score}")

                print(evaluation)
                print(f"品質スコア：{score}")
                print(f"SEOスコア：{seo_score}")
                print(f"最新情報：{latest_result}")

                if (
                    re.search(r"改善点\s*[:：]?\s*なし", evaluation)
                    and latest_result == "OK"
                    and duplicate_result == "OK"
                ):
                    print("改善点がないためリライトを終了します。")
                    break

                if (
                    score >= MIN_SCORE
                    and seo_score >= MIN_SEO_SCORE
                    and latest_result == "OK"
                    and duplicate_result == "OK"
                ):
                    print("すべての品質基準をクリアしました。")
                    break


            if score < MIN_SCORE:
                print("最大回数リライトしましたが品質基準に届きませんでした。")


            if seo_score < MIN_SEO_SCORE:
                print("最大回数リライトしましたがSEO基準に届きませんでした。")

            x_post, instagram_post = generate_sns_posts(
                client,
                article,
            )

            print("===== X投稿 =====")
            print(x_post)

            print("===== Instagram投稿 =====")
            print(instagram_post)

            break

        except Exception as e:
            print(f"Geminiエラー（{attempt + 1}回目）：{e}")

            if attempt == MAX_RETRY - 1:
                raise

            print("30秒後に再試行します...")
            time.sleep(30)

    status = (
        "✅ 全品質基準クリア"
        if (
            score >= MIN_SCORE
            and seo_score >= MIN_SEO_SCORE
            and latest_result == "OK"
            and duplicate_result == "OK"
        )
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

    summary_message = f"""📊【AI評価】

    {evaluation}

    --------------------

    🐦【X投稿】

    {x_post}

    --------------------

    📸【Instagram投稿】

    {instagram_post}
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
        "text": summary_message
    })

    payload = {
        "to": user_id,
        "messages": messages
    }


    try:
        response_line = requests.post(line_api_url, headers=headers, json=payload)

        if response_line.status_code == 200:
            title = article.split("\n")[0].replace("タイトル：", "").replace("タイトル:", "").strip()
            save_article(title, article)

            print("記事履歴を保存しました。")
            print("Success: Message sent to LINE safely!")

        else:
            print(f"Error: LINE API returned status code {response_line.status_code}")

            print(response_line.text)
    except Exception as e:

        print(f"Error: {e}")

        raise e


if __name__ == "__main__":
    generate_and_send_line()
