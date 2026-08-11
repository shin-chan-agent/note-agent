# 品質チェック設定
MIN_SCORE = 90
MIN_SEO_SCORE = 90
MAX_REWRITE = 3
MAX_ARTICLE_LENGTH = 9500


# APIリトライ設定
MAX_RETRY = 3
GOOGLE_SEARCH_RETRY_WAIT = 5
GEMINI_RETRY_WAIT = 30
EVALUATION_RETRY_WAIT = 5


# AI知識DB更新設定
KNOWLEDGE_UPDATE_INTERVAL_DAYS = 7
MISSING_LIMIT = 2


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


THEME_SERVICES = {
    "AI×ショート動画の実践・検証": [
        "chatgpt",
        "gemini",
        "canva",
        "capcut",
    ],

    "ショート動画作成に役立つAIツール": [
        "chatgpt",
        "gemini",
        "canva",
        "capcut",
    ],

    "初心者向けAI副業": [
        "chatgpt",
        "gemini",
        "canva",
        "capcut",
    ],

    "ChatGPT活用術": [
        "chatgpt",
    ],

    "Gemini活用術": [
        "gemini",
    ],

    "Claude活用術": [
        "claude",
    ],

    "Canva活用術": [
        "canva",
    ],

    "CapCut活用術": [
        "capcut",
    ],

    "AI副業ロードマップ": [
        "chatgpt",
        "gemini",
        "canva",
        "capcut",
    ],

    "AIで収益化する方法": [
        "chatgpt",
        "gemini",
        "canva",
        "capcut",
    ],

    "AI活用による時間短縮術": [
        "chatgpt",
        "gemini",
        "canva",
        "capcut",
    ],
}