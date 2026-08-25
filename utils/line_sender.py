import os
import requests


LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
LINE_MAX_MESSAGES = 5
LINE_MAX_TEXT_LENGTH = 5000


def split_text(text, max_length=4990):
    """
    LINE送信用に文章を分割する。

    ・1メッセージ最大4990文字
    ・4990文字以内で最後に出てくる「。」で分割
    ・「。」がなければ改行で分割
    ・それもなければ文字数で分割
    """

    parts = []

    while len(text) > max_length:

        # max_length以内で最後の「。」を探す
        split_pos = text.rfind("。", 0, max_length)

        # 「。」がなければ最後の改行を探す
        if split_pos == -1:
            split_pos = text.rfind("\n", 0, max_length)

        # それでもなければ文字数で強制分割
        if split_pos == -1:
            split_pos = max_length
        else:
            # 「。」または改行を含める
            split_pos += 1

        part = text[:split_pos].strip()

        if part:
            parts.append(part)

        text = text[split_pos:].strip()

    # 最後に残った部分
    if text:
        parts.append(text)

    # 【1/○】を付与
    total = len(parts)

    return [
        f"【{i + 1}/{total}】\n\n{part}"
        for i, part in enumerate(parts)
    ]


def send_line_messages(messages):
    """
    LINE Messaging APIへメッセージを送信する。

    ・テキストは1メッセージ5000文字以内
    ・1回のPush APIにつき最大5メッセージ
    """

    print(f"LINE送信メッセージ数: {len(messages)}")

    # ==========================================
    # 送信前チェック
    # ==========================================

    for i, message in enumerate(messages, 1):

        message_type = message.get("type")

        if message_type == "text":

            text = message.get("text", "")
            text_length = len(text)

            print(
                f"LINE送信{i}文字数: {text_length}"
            )

            if text_length > LINE_MAX_TEXT_LENGTH:
                raise ValueError(
                    f"LINE送信{i}が"
                    f"{LINE_MAX_TEXT_LENGTH}文字を超えています: "
                    f"{text_length}文字"
                )

        else:
            raise ValueError(
                f"未対応のLINEメッセージタイプです: "
                f"{message_type}"
            )

    # ==========================================
    # 環境変数
    # ==========================================

    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    user_id = os.environ["LINE_USER_ID"]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    # ==========================================
    # 最大5メッセージずつ送信
    # ==========================================

    response = None

    for i in range(
        0,
        len(messages),
        LINE_MAX_MESSAGES,
    ):

        batch = messages[
            i:i + LINE_MAX_MESSAGES
        ]

        payload = {
            "to": user_id,
            "messages": batch,
        }

        response = requests.post(
            LINE_PUSH_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"LINE API Error "
                f"{response.status_code}\n"
                f"{response.text}"
            )

        print(
            f"LINE送信成功: "
            f"{i + 1}〜{i + len(batch)}件"
        )

    return response


def create_text_message(text):
    """
    LINE用のテキストメッセージを作成する。
    """

    if not isinstance(text, str):
        raise TypeError(
            "LINEテキストメッセージは文字列で指定してください。"
        )

    if len(text) > LINE_MAX_TEXT_LENGTH:
        raise ValueError(
            f"LINEテキストが"
            f"{LINE_MAX_TEXT_LENGTH}文字を超えています: "
            f"{len(text)}文字"
        )

    return {
        "type": "text",
        "text": text,
    }