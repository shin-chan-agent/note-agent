import json
import random
from pathlib import Path


COMBINATION_HISTORY_FILE = Path("combination_history.json")


# ========================================
# テーマ × 切り口 × 対象AI
# ========================================

THEME_ANGLES = {
    "ショート動画": {
        "作業フロー": [
            "chatgpt",
            "gemini",
            "canva",
            "capcut",
        ],
        "品質改善": [
            "chatgpt",
            "gemini",
            "canva",
            "capcut",
        ],
    },

    "SNS運用": {
        "作業フロー": [
            "chatgpt",
            "gemini",
            "canva",
        ],
        "品質改善": [
            "chatgpt",
            "claude",
            "canva",
        ],
    },

    "AI×仕事効率化": {
        "作業フロー": [
            "chatgpt",
            "gemini",
            "copilot",
        ],
        "業務改善": [
            "chatgpt",
            "copilot",
            "claude",
        ],
    },

    "AI自動化": {
        "作業フロー": [
            "chatgpt",
            "gemini",
            "claude",
        ],
        "設計・構築": [
            "chatgpt",
            "claude",
            "claude_code",
            "gemini",
        ],
        "失敗回避": [
            "chatgpt",
            "claude",
            "gemini",
        ],
    },

    "AIリサーチ・情報収集": {
        "調査設計": [
            "perplexity",
            "chatgpt",
            "gemini",
        ],
        "作業フロー": [
            "perplexity",
            "chatgpt",
            "gemini_notebook",
        ],
        "検証・判断": [
            "perplexity",
            "gemini_notebook",
            "claude",
        ],
    },
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
# テーマ × 切り口から対象AIを取得
# ========================================

def get_target_services(
    theme,
    angle,
):

    theme_data = THEME_ANGLES.get(
        theme,
        {}
    )

    services = theme_data.get(
        angle,
        []
    )

    return services