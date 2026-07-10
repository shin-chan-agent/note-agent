import os
import time
import requests
from google import genai
from theme_manager import get_theme_and_angle


def generate_and_send_line():
    # 最新のライブラリでGeminiで記事を生成
    # 環境変数から自動でAPIキーを読み込む仕様になりました

    client = genai.Client()

    theme, angle = get_theme_and_angle()
    

    prompt = (
        f"今回の記事テーマは『{theme}』です。\n"
        f"記事の切り口は『{angle}』です。\n"
        f"記事全体を『{angle}』という視点で構成してください。\n"
        "noteに投稿する記事を1つ執筆してください。\n\n"

        "確信の持てる情報のみを掲載してください。\n"
        "構成は「タイトル→導入文→本文→まとめ」の順で\n"
        "タイトルを必ず最初に入れてください。\n"
        "最後に「まとめ」の章を必ず入れてください。\n\n"

        "トーンは親しみやすく知的なキャラクターとして語りかけるようにしてください。\n"
        "キャラクターに名前をつけないでください。\n"
        "AI特有の不自然なビジネス構文（「〜ですよね！」「さあ、始めましょう！」など）は一切禁止します。\n"
        "記事の最初にあいさつ（「こんにちは」「いつも読んでいただき、ありがとうございます」など）を入れないでください。\n"

        "記事の最後に以下の文を入れてください。\n"
        "AI×ショート動画で最速でマネタイズ（収益化）する具体的な手順と、豪華40大特典の受け取り方は、下記の固定記事で詳しく解説しています。\n"
        "↓↓↓\n"
        "[【初期費用ゼロ】スキルなしの会社員や主婦がショート動画で最速で月収10万を達成したロードマップ]\n"
        "(https://note.com/shin_chan_ai/n/n7bec364e6cd2)\n\n"

        "作成した文章に最適なハッシュタグを5つ考えて入れてください\n"
        "「ゼロイチ」は“マネタイズにおける最初の1円”の意味のみで使用してください\n"
        "読者に続きを読みたいと思わせるように、導入部分の最初の3行を“読者の悩みや状況から書き始める”ことを意識して書いてください\n"
        "各章の内容が分かるような見出しにしてください\n"
        "最後まで読んでもらえるようなタイトル・冒頭3行・見出し・記事の内容にしてください\n\n"

        "記事の文字数は2,500〜3,500文字程度にしてください。\n"
        "Markdown形式で出力してください。\n"
        "見出しは「#」「##」「###」を使用してください。\n"
        "同じ表現や言い回しを繰り返さず、自然な文章にしてください。\n"
        "過去の記事と似た構成にならないよう、説明の順番や具体例を毎回変えてください。\n"
        "箇条書き・表・番号付きリストを適度に使い、最後まで読みやすい構成にしてください。\n"
        "専門用語を使う場合は初心者にも分かるように簡潔に説明してください。\n"
        "読者が『すぐ試してみよう』と思える具体的な行動を1つ以上提案してください。\n\n"

        "タイトルは32〜40文字程度にしてください。\n"
        "タイトルだけでなく、H2・H3見出しにも自然にSEOキーワードを含めてください。\n"
        "導入文の前半100文字以内にテーマの主要キーワードを自然に含めてください。\n"
        "初心者が知りたい内容を漏れなく網羅してください。\n"
        "読者の疑問を先回りして回答してください。\n"
        "実際の利用例や具体例を交え、断定できない内容は推測を書かないでください。\n"

        "必要に応じて表や箇条書きを使い、スマホでも読みやすくしてください。\n"
        "まとめでは記事の要点を3〜5個に整理してください。\n"
        "Google検索とnote内検索の両方を意識したSEO記事にしてください。\n"
        "最初にSEOを意識したタイトル候補を5つ提示し、その中で最もクリック率が高そうなタイトルを採用してください。\n"
        "noteで最後まで読まれやすい文章構成にしてください。\n\n"

        "Google検索・note内検索のSEOを意識し、初心者にも分かりやすく、最後まで読まれやすい構成にしてください。タイトル・導入文・見出しには主要キーワードを自然に含め、必要に応じて箇条書きや具体例を用いて網羅性と読みやすさを高めてください。タイトルは32〜40文字程度とし、クリックしたくなる内容にしてください。\n\n"

    )


    MAX_RETRY = 3

    for attempt in range(MAX_RETRY):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            break

        except Exception as e:
            print(f"Geminiエラー（{attempt + 1}回目）：{e}")

            if attempt == MAX_RETRY - 1:
                raise

            print("30秒後に再試行します...")
            time.sleep(30)

    
    # LINE公式アカウント（Messaging API）を使ってメッセージを送信
    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    user_id = os.environ["LINE_USER_ID"]
    
    line_api_url = "https://api.line.me/v2/bot/message/push"
    
    # 送信するメッセージの組み立て
    message_text = f"🤖【Gemini生成のnote原稿】🤖\n\n{response.text}"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message_text
            }
        ]
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
