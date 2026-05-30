import os
import requests
from google import genai

def generate_and_send_line():
    # 1. 最新のライブラリでGeminiで記事を生成
    # 💡 環境変数から自動でAPIキーを読み込む仕様になりました
    client = genai.Client()
    
    prompt = (
        "noteに投稿する記事をタイトル付きで1つ執筆してください。\n"
        "確信の持てる情報のみを掲載してください。"
        "テーマは以下のいずれかから毎回ランダムに選び、実用的で目からウロコの内容にしてください：\n"
        "1. クリエイターの作業が劇的にラクになるお役立ちの知恵\n"
        "2. 初心者でも今すぐ私生活や仕事で使える具体的な【AI活用術】\n"
        "3. スマホやPCで始められる具体的な【AI副業のアイデアやロードマップ】\n\n"
        "トーンは親しみやすく知的なキャラクターとして語りかけるようにしてください。"
        "キャラクターに名前をつけないでください。"
        "AI特有の不自然なビジネス構文（「〜ですよね！」「さあ、始めましょう！」など）は一切禁止します。"
        "タイトルは必ず最初に入れて、タイトルと本文は完全に分けてください。"
        "見出しを分かりやすく表示してください"
        "作成した文章に最適なハッシュタグを5つ考えて入れてください。"
    )


    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    
    # 2. LINE公式アカウント（Messaging API）を使ってメッセージを送信
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
