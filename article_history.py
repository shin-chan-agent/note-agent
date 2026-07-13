import json
import os

FILE_NAME = "article_history.json"


def load_articles():
    if not os.path.exists(FILE_NAME):
        return []

    with open(FILE_NAME, "r", encoding="utf-8") as f:
        return json.load(f)


def save_article(title, article):
    articles = load_articles()

    articles.append({
        "title": title,
        "article": article
    })

    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)