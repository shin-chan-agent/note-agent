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

    return json.loads(text)