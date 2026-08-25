import json
import os

FILE_NAME = "article_history.json"


def load_articles():
    if not os.path.exists(FILE_NAME):
        return []

    with open(FILE_NAME, "r", encoding="utf-8") as f:
        return json.load(f)


def save_article(title, theme, angle):
    articles = load_articles()

    articles.append({
        "title": title,
        "theme": theme,
        "angle": angle,
    })

    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)


def get_past_articles_text(limit=20):
    """
    過去記事の履歴を記事生成用の文字列に変換する。

    最新の記事から指定件数を使用する。
    """

    articles = load_articles()

    return "\n\n".join(
        (
            f"タイトル: {article['title']}\n"
            f"テーマ: {article['theme']}\n"
            f"切り口: {article['angle']}"
        )
        for article in articles[-limit:]
    )