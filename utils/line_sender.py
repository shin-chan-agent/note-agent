import os
import requests


def send_line_messages(messages):
    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    user_id = os.environ["LINE_USER_ID"]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    payload = {
        "to": user_id,
        "messages": messages,
    }

    response = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers,
        json=payload,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"LINE API Error {response.status_code}\n{response.text}"
        )

    return response