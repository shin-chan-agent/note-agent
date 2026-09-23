import json
import random
from pathlib import Path


COMBINATION_HISTORY_FILE = Path("combination_history.json")


# ========================================
# テーマ × 切り口 × 対象AI
# ========================================

THEME_ANGLES = {
    "AI×ショート動画": {
        "始め方": [],
        "ツールの選び方": [],
        "失敗しやすいポイント": [],
        "活用アイデア": [],
    },

    "AIツール活用": {
        "できること・できないこと": [],
        "初心者向けの使い方": [],
        "ツールの選び方": [],
        "比較・レビュー": [],
    },

    "AI副業": {
        "始め方": [],
        "必要なAIツール": [],
        "収益化の基本": [],
        "失敗しやすいポイント": [],
    },

    "AI×SNS": {
        "始め方": [],
        "投稿作成の基本": [],
        "活用アイデア": [],
        "ツール比較": [],
    },

    "AI×仕事効率化": {
        "AIでできること": [],
        "活用アイデア": [],
        "初心者向けの使い方": [],
        "ツールの選び方": [],
    },

    "AI活用の基本": {
        "AIの得意・不得意": [],
        "プロンプトの基本": [],
        "情報の確認方法": [],
        "資料・情報の整理方法": [],
    },
}


# ========================================
# テーマごとの対象AI
# ========================================

THEME_SERVICES = {
    "AI×ショート動画": [
        "chatgpt",
        "gemini",
        "canva",
        "capcut",
    ],

    "AIツール活用": [
        "chatgpt",
        "gemini",
        "claude",
        "copilot",
        "claude_code",
    ],

    "AI副業": [
        "chatgpt",
        "gemini",
        "canva",
        "capcut",
    ],

    "AI×SNS": [
        "chatgpt",
        "gemini",
        "canva",
    ],

    "AI×仕事効率化": [
        "chatgpt",
        "gemini",
        "copilot",
    ],

    "AI活用の基本": [
        "chatgpt",
        "gemini",
        "claude",
        "perplexity",
        "gemini_notebook",
    ],
}


# ========================================
# 組み合わせ履歴
# ========================================

def load_combination_history():

    try:

        with open(
            COMBINATION_HISTORY_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            return json.load(f)

    except FileNotFoundError:

        return []


def save_combination_history(history):

    with open(
        COMBINATION_HISTORY_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            history,
            f,
            ensure_ascii=False,
            indent=2,
        )


# ========================================
# 全組み合わせ取得
# ========================================

def get_all_combinations():

    combinations = []

    for theme, angles in THEME_ANGLES.items():

        for angle in angles:

            combinations.append(
                {
                    "theme": theme,
                    "angle": angle,
                }
            )

    return combinations


# ========================================
# テーマ × 切り口を決定
# ========================================

def get_theme_and_angle():

    history = load_combination_history()
    all_combinations = get_all_combinations()

    unused = [
        combination
        for combination in all_combinations
        if combination not in history
    ]

    print(
        f"組み合わせ履歴：{len(history)}件"
    )

    print(
        f"登録済み組み合わせ："
        f"{len(all_combinations)}件"
    )

    print(
        f"未使用組み合わせ："
        f"{len(unused)}件"
    )

    # ====================================
    # すべて使用済みの場合
    # ====================================

    if not unused:

        print(
            "すべての組み合わせを使用したため、"
            "履歴をリセットします。"
        )

        history = []

        save_combination_history(
            history
        )

        unused = all_combinations.copy()

    # ====================================
    # 未使用からランダム選択
    # ====================================

    selected = random.choice(
        unused
    )

    print(
        f"今回："
        f"{selected['theme']} × "
        f"{selected['angle']}"
    )

    return (
        selected["theme"],
        selected["angle"],
    )


# ========================================
# 組み合わせを履歴へ登録
# ========================================

def mark_combination_completed(
    theme,
    angle,
):

    history = load_combination_history()

    combination = {
        "theme": theme,
        "angle": angle,
    }

    if combination in history:

        print(
            "組み合わせは既に履歴へ登録されています。"
        )

        return

    history.append(
        combination
    )

    save_combination_history(
        history
    )

    print(
        f"組み合わせ履歴へ登録："
        f"{theme} × {angle}"
    )


# ========================================
# テーマから対象AIを取得
# ========================================

def get_target_services(
    theme,
):

    return THEME_SERVICES.get(
        theme,
        [],
    )