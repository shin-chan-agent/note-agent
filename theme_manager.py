import json
from pathlib import Path

import random

HISTORY_FILE = Path("theme_history.json")

# 記事テーマ一覧
THEMES = [
    "AI×ショート動画の実践・検証",
    "ショート動画作成に役立つAIツール",
    "初心者向けAI副業",
    "ChatGPT活用術",
    "Gemini活用術",
    "CapCut活用術",
    "Canva活用術",
    "AI副業ロードマップ",
    "AIで収益化する方法",
    "AI活用による時間短縮術"
]


def get_random_theme():
    """テーマをランダムに選び、履歴へ保存する"""

    history = load_theme_history()

    print(f"テーマ履歴（保存前）：{history}")

    theme = random.choice(THEMES)

    history.append(theme)

    save_theme_history(history)

    print(f"今回のテーマ：{theme}")

    return theme


def load_theme_history():
    """テーマ履歴を読み込む"""
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []