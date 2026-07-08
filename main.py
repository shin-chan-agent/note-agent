すimport os
import requests
from google import genai

def generate_and_send_line():
    # 最新のライブラリでGeminiで記事を生成
    # 環境変数から自動でAPIキーを読み込む仕様になりました
    client = genai.Client()
    
    prompt = (
        "noteに投稿する記事をタイトル付きで1つ執筆してください"
        "確信の持てる情報のみを掲載してください"
        "テーマは以下のいずれかから毎回ランダムに選び、実用的な内容にしてください\n"
        "1. AI×ショート動画の実践・検証記事\n"
        "2. ショート動画作成に使用するAIツールの解説\n"
        "3. 初心者でもスマホやPCで今すぐ始められる具体的なAI副業のアイデア\n\n"
        "構成は、「タイトル→導入文→本文→まとめ」"
        "次のキーワードをタイトルに2つ以上含めてください\n"
        "「AI副業」「ショート動画」「自動化」「タイパ」「コスパ」「ロードマップ」\n"
        "不自然にならないよう、キーワードは詰め込みすぎないように気をつけてください\n\n"
        "トーンは親しみやすく知的なキャラクターとして語りかけるようにしてください\n"
        "キャラクターに名前をつけないでください\n\n"
        "AI特有の不自然なビジネス構文（「〜ですよね！」「さあ、始めましょう！」など）は一切禁止します"
        "タイトルは必ず最初に入れて、タイトルと本文は完全に分けてください"
        "記事の最初にあいさつ（「こんにちは」「いつも読んでいただきありがとうございます」など）を入れないでください"
        "記事の最後に、次の文を入れてください\n"
        "「AI×ショート動画で最速でマネタイズ（収益化）する具体的な手順と、豪華40大特典の受け取り方は、下記の固定記事で詳しく解説しています。\n"
        "↓↓↓\n"
        "【初期費用ゼロ】スキルなしの会社員や主婦がショート動画で最速で月収10万を達成したロードマップ」\n\n"
        "見出しを分かりやすく表示してください"
        "作成した文章に最適なハッシュタグを5つ考えて入れてください"
        "「ゼロイチ」は“マネタイズにおける最初の1円”の意味のみで使用してください"
        "読者に続きを読みたいと思わせるように、最初の3行を“読者の悩みや状況から書き始める”ことを意識して書いてください"
        "各章の内容が分かるような見出しにしてください"
        "最後まで読んでもらえるような“タイトル・冒頭3行・見出し・記事の内容"にしてください"
    )


    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    
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
