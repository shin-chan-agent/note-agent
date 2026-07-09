import json
from pathlib import Path

import random


THEME_HISTORY_FILE = Path("theme_history.json")
ANGLE_HISTORY_FILE = Path("angle_history.json")


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

# 記事の切り口
ANGLES = [
    "初心者向け",
    "実践・検証",
    "失敗しやすいポイント",
    "時短テクニック",
    "おすすめ設定",
    "メリット・デメリット",
    "よくある質問",
    "チェックリスト",
    "成功するコツ",
    "比較・レビュー"
]


def get_random_theme():
    """未使用テーマを優先してランダムに選び、履歴へ保存する"""

    history = load_theme_history()

    print(f"テーマ履歴（保存前）：{history}")

    # 未使用テーマだけ抽出
    unused_themes = [theme for theme in THEMES if theme not in history]

    # 全テーマ使い切ったら履歴リセット
    if not unused_themes:
        print("全テーマを使用したため履歴をリセットします。")

        history = []
        unused_themes = THEMES.copy()

    # 未使用テーマからランダム選択
    theme = random.choice(unused_themes)

    # 履歴へ追加
    history.append(theme)

    save_theme_history(history)

    print(f"今回のテーマ：{theme}")

    return theme


def get_random_angle():
    """記事の切り口をランダムに選ぶ"""

    angle = random.choice(ANGLES)

    print(f"今回の切り口：{angle}")

    return angle


def load_theme_history():
    """テーマ履歴を読み込む"""
    try:
        with open(THEME_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_theme_history(history):
    """テーマ履歴を保存する"""
    with open(THEME_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)