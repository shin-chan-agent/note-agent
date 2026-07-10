import json
from pathlib import Path

import random


THEME_HISTORY_FILE = Path("theme_history.json")
ANGLE_HISTORY_FILE = Path("angle_history.json")
COMBINATION_HISTORY_FILE = Path("combination_history.json")


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

    print(f"今回のテーマ：{theme}")

    return theme


def get_random_angle():
    """未使用の切り口を優先してランダムに選び、履歴へ保存する"""

    history = load_angle_history()

    print(f"切り口履歴（保存前）：{history}")

    # 未使用の切り口だけ抽出
    unused_angles = [angle for angle in ANGLES if angle not in history]

    # 全切り口を使い切ったらリセット
    if not unused_angles:
        print("全切り口を使用したため履歴をリセットします。")

        history = []
        unused_angles = ANGLES.copy()

    # 未使用からランダム選択
    angle = random.choice(unused_angles)

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


def load_angle_history():
    """切り口履歴を読み込む"""
    try:
        with open(ANGLE_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_angle_history(history):
    """切り口履歴を保存する"""
    with open(ANGLE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def load_combination_history():
    """組み合わせ履歴を読み込む"""
    try:
        with open(COMBINATION_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_combination_history(history):
    """組み合わせ履歴を保存する"""
    with open(COMBINATION_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_theme_and_angle():
    """未使用のテーマ×切り口の組み合わせを返す"""

    combination_history = load_combination_history()

    while True:
        theme = get_random_theme()
        angle = get_random_angle()

        combination = {
            "theme": theme,
            "angle": angle
        }

        if combination not in combination_history:

            combination_history.append(combination)
            save_combination_history(combination_history)

            theme_history = load_theme_history()
            theme_history.append(theme)
            save_theme_history(theme_history)

            angle_history = load_angle_history()
            angle_history.append(angle)
            save_angle_history(angle_history)

            print(f"今回の組み合わせ：{theme} × {angle}")

            return theme, angle

        print("組み合わせが重複したため再抽選します。")