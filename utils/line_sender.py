import os
import requests


def send_line_messages(messages):

    print(f"LINE送信メッセージ数: {len(messages)}")

    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    user_id = os.environ["LINE_USER_ID"]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    for i in range(0, len(messages), 5):
        payload = {
            "to": user_id,
            "messages": messages[i:i+5]
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"LINE API Error {response.status_code}\n{response.text}"
            )

    return response


def create_text_message(text):

    return {
        "type": "text",
        "text": text,
    }