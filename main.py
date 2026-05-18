import os
import requests
import google.generativeai as genai

def generate_and_send_line():
    # 1. Geminiで記事を生成
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = "noteに投稿する、クリエイター向けのタメになる面白い記事をタイトル付きで1つ執筆してください。親しみやすく知的なトーンで。LINEに送るので読みやすいように適度に改行を入れてください。"
    response = model.generate_content(prompt)
    
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
