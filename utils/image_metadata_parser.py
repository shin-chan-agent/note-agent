import re


def parse_image_metadata(text):
    """
    Geminiの生成結果から
    画像カテゴリと強調キーワードを抽出する。
    """

    # 画像カテゴリ
    category_match = re.search(
        r"画像カテゴリ\s*[:：]\s*(.+)",
        text
    )

    image_category = (
        category_match.group(1).strip()
        if category_match
        else ""
    )

    # 強調キーワード
    keyword_match = re.search(
        r"強調キーワード\s*[:：]\s*(.+)",
        text
    )

    if keyword_match:
        keyword_text = keyword_match.group(1).strip()

        if keyword_text in ["なし", "無し", "なし。", "無し。"]:
            highlight_keywords = []
        else:
            highlight_keywords = [
                keyword.strip()
                for keyword in re.split(
                    r"[,、]",
                    keyword_text
                )
                if keyword.strip()
            ]
    else:
        highlight_keywords = []

    # 記事本文から画像用情報を削除
    article = re.sub(
        r"\n*画像カテゴリ\s*[:：].*",
        "",
        text
    )

    article = re.sub(
        r"\n*強調キーワード\s*[:：].*",
        "",
        article
    )

    return {
        "article": article.strip(),
        "image_category": image_category,
        "highlight_keywords": highlight_keywords,
    }


def is_valid_image_metadata(metadata):
    """
    画像カテゴリと強調キーワードの取得結果が
    正常かどうかを判定する。
    """

    image_category = metadata.get(
        "image_category",
        ""
    ).strip()

    highlight_keywords = metadata.get(
        "highlight_keywords",
        []
    )

    # 画像カテゴリが空なら異常
    if not image_category:
        return False

    # 強調キーワードは0個でも正常
    # 「なし」の場合も正常
    return True