MIN_SCORE = 90
MIN_SEO_SCORE = 90

MAX_REWRITE = 3
MAX_RETRY = 3

GOOGLE_SEARCH_RETRY_WAIT = 5
GEMINI_RETRY_WAIT = 30
EVALUATION_RETRY_WAIT = 5


SEARCH_QUERIES = {
    "ChatGPT": "ChatGPT 最新 GPT-5 無料版 Plus Pro Teams Enterprise 料金 機能",
    "Gemini": "Google Gemini 最新 Gemini 2.5 Flash Pro 料金 AI Studio 機能",
    "Claude": "Claude 最新 Sonnet Opus 料金 機能",
    "Canva": "Canva 最新 AI機能 Magic Studio Visual Suite 料金",
    "CapCut": "CapCut 最新 AI機能 料金 商用利用",
    "note": "note 最新 アルゴリズム SEO 仕様変更",
    "Instagram": "Instagram 最新 リール アルゴリズム",
    "X": "X 最新 アルゴリズム 収益化",
    "AI副業": "AI副業 最新 トレンド AIツール",
    "ショート動画": "ショート動画 最新 トレンド YouTube Shorts Instagram Reels TikTok",
}


AI_SERVICES = {
    "chatgpt": {
        "name": "ChatGPT",
        "enabled": True,
        "official_domains": [
            "openai.com",
            "platform.openai.com",
            "help.openai.com",
        ],
        "search_prompt": """
ChatGPTについて最新情報を調査してください。

以下を重点的に確認してください。

・最新モデル
・料金プラン
・新機能
・API仕様変更
・利用制限
・注意点

公式情報を優先してください。
"""
    },

    "gemini": {
        "name": "Gemini",
        "enabled": True,
        "official_domains": [
            "ai.google.dev",
            "cloud.google.com",
            "deepmind.google",
            "developers.googleblog.com",
        ],
        "search_prompt": """
Geminiについて最新情報を調査してください。

以下を重点的に確認してください。

・最新モデル
・料金プラン
・新機能
・API仕様変更
・利用制限
・注意点

公式情報を優先してください。
"""
    },

    "claude": {
        "name": "Claude",
        "enabled": True,
        "official_domains": [
            "anthropic.com",
            "docs.anthropic.com",
        ],
        "search_prompt": """
Claudeについて最新情報を調査してください。

以下を重点的に確認してください。

・最新モデル
・料金プラン
・新機能
・利用制限
・注意点

公式情報を優先してください。
"""
    },

    "canva": {
        "name": "Canva",
        "enabled": True,
        "official_domains": [
            "canva.com",
            "canva.dev",
        ],
        "search_prompt": """
Canvaについて最新情報を調査してください。

以下を重点的に確認してください。

・AI機能
・料金プラン
・新機能
・商用利用条件
・注意点

公式情報を優先してください。
"""
    },

    "capcut": {
        "name": "CapCut",
        "enabled": True,
        "official_domains": [
            "capcut.com",
            "support.capcut.com",
        ],
        "search_prompt": """
CapCutについて最新情報を調査してください。

以下を重点的に確認してください。

・AI機能
・料金プラン
・新機能
・利用制限
・注意点

公式情報を優先してください。
"""
    },
}