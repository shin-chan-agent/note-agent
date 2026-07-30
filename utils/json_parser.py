import json


def parse_json(text):
    """
    Geminiが返したJSON文字列をPythonのdictへ変換する。
    """

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    if text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    try:
        return json.loads(text)

    except json.JSONDecodeError as e:
        raise ValueError(
            f"JSONの解析に失敗しました。\n\n{text}"
        ) from e