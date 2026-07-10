import json
import random
from pathlib import Path

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


def load_combination_history():
    try:
        with open(COMBINATION_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_combination_history(history):
    with open(COMBINATION_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_theme_and_angle():
    """未使用のテーマ×切り口をランダムに返す"""

    history = load_combination_history()

    print(f"組み合わせ履歴（保存前）：{len(history)}件")

    # 全100通りの組み合わせを作成
    all_combinations = [
        {"theme": theme, "angle": angle}
        for theme in THEMES
        for angle in ANGLES
    ]

    # 未使用のみ抽出
    unused = [c for c in all_combinations if c not in history]

    # 全部使い切ったらリセット
    if not unused:
        print("100通り使用したため履歴をリセットします。")

        history = []
        unused = all_combinations.copy()

    # ランダム選択
    selected = random.choice(unused)

    history.append(selected)
    save_combination_history(history)

    print(
        f"今回：{selected['theme']} × {selected['angle']}"
    )

    return selected["theme"], selected["angle"]