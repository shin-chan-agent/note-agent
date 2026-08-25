import json


def parse_json(text):
    """
    Geminiが返したJSON文字列をPythonのdictへ変換する。

    対応:
    ・通常のJSON
    ・```json ... ``` のコードブロック
    ・``` ... ``` のコードブロック
    ・JSON前後に余計な文章がある場合
    """

    if not isinstance(text, str):
        raise TypeError(
            "JSON解析対象は文字列で指定してください。"
        )

    text = text.strip()

    # ========================================
    # コードブロック除去
    # ========================================

    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    # ========================================
    # JSONとして直接解析
    # ========================================

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        pass

    # ========================================
    # 前後に余計な文章がある場合
    # ========================================

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and start < end:

        json_text = text[start:end + 1]

        try:
            return json.loads(json_text)

        except json.JSONDecodeError as e:

            raise ValueError(
                f"""
JSONの解析に失敗しました。

位置: line={e.lineno}, column={e.colno}, pos={e.pos}

エラー:
{e}

対象:
{json_text[max(0, e.pos-200):e.pos+200]}
"""
            ) from e

    # ========================================
    # JSON自体が存在しない場合
    # ========================================

    raise ValueError(
        f"""
JSONの解析に失敗しました。

JSONオブジェクトを検出できませんでした。

対象:
{text[:500]}
"""
    )