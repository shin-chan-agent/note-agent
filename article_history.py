import json
import os
import re


FILE_NAME = "article_history.json"


def load_articles():
    """
    記事履歴を読み込む。
    """

    if not os.path.exists(FILE_NAME):
        return []

    with open(
        FILE_NAME,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


def extract_comparison_text(article):
    """
    記事本文から類似度チェック用の
    比較テキストを作成する。

    保存容量を抑えるため、
    タイトル・見出し・本文の要点を
    抽出する。
    """

    lines = article.splitlines()

    comparison_parts = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # タイトル
        if re.match(
            r"^タイトル[:：]",
            line,
        ):
            comparison_parts.append(line)
            continue

        # Markdown見出し
        if re.match(
            r"^#{2,3}\s+",
            line,
        ):
            comparison_parts.append(line)
            continue

    # 見出しが少ない場合に備えて、
    # 本文から主要な文章を追加する。
    body_sentences = []

    for sentence in re.split(
        r"(?<=[。！？])",
        article,
    ):

        sentence = sentence.strip()

        if not sentence:
            continue

        # タイトル・見出しは除外
        if re.match(
            r"^タイトル[:：]",
            sentence,
        ):
            continue

        if re.match(
            r"^#{2,3}\s+",
            sentence,
        ):
            continue

        body_sentences.append(sentence)

    # 本文は最大1500文字まで保存
    body_text = "".join(
        body_sentences
    )[:1500]

    if body_text:
        comparison_parts.append(
            body_text
        )

    return "\n".join(
        comparison_parts
    )


def save_article(
    title,
    theme,
    angle,
    article=None,
):
    """
    記事履歴を保存する。

    title:
        記事タイトル

    theme:
        記事テーマ

    angle:
        記事の切り口

    article:
        類似度チェック用の比較テキストを
        作成するための記事本文。
    """

    articles = load_articles()

    item = {
        "title": title,
        "theme": theme,
        "angle": angle,
    }

    # 記事本文が渡された場合のみ
    # 類似度チェック用データを保存
    if article:

        item["comparison_text"] = (
            extract_comparison_text(
                article
            )
        )

    articles.append(item)

    with open(
        FILE_NAME,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            articles,
            f,
            ensure_ascii=False,
            indent=2,
        )


def get_past_articles_text(
    limit=20,
):
    """
    過去記事の履歴を記事生成・重複チェック用の
    文字列に変換する。

    最新の記事から指定件数を使用する。

    新しい履歴:
        タイトル・テーマ・切り口・比較用テキスト

    古い履歴:
        タイトル・テーマ・切り口のみ
    """

    articles = load_articles()

    result = []

    for article in articles[-limit:]:

        parts = [
            f"タイトル: {article.get('title', '')}",
            f"テーマ: {article.get('theme', '')}",
            f"切り口: {article.get('angle', '')}",
        ]

        comparison_text = article.get(
            "comparison_text"
        )

        if comparison_text:

            parts.append(
                "比較用本文:\n"
                + comparison_text
            )

        result.append(
            "\n".join(parts)
        )

    return "\n\n".join(result)