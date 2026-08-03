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
            f"""
JSONの解析に失敗しました。

位置: line={e.lineno}, column={e.colno}, pos={e.pos}

エラー:
{e}

対象:
{text[max(0, e.pos-200):e.pos+200]}
"""
        ) from e