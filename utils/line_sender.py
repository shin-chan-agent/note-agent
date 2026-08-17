import os
import requests


def send_line_messages(messages):

    print(f"LINE送信メッセージ数: {len(messages)}")

    for i, message in enumerate(messages, 1):
        text_length = len(message["text"])

        print(f"LINE送信{i}文字数: {text_length}")

        if text_length > 5000:
            raise ValueError(
                f"LINE送信{i}が5000文字を超えています: "
                f"{text_length}文字"
            )

    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    user_id = os.environ["LINE_USER_ID"]

    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    user_id = os.environ["LINE_USER_ID"]

    url = "https://api.line.me/v2/bot/message/push"

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


def create_image_message(
    image_url,
    preview_url=None,
):
    """
    LINEへ画像を送信するためのメッセージを作成する。
    """

    if preview_url is None:
        preview_url = image_url

    return {
        "type": "image",
        "originalContentUrl": image_url,
        "previewImageUrl": preview_url,
    }