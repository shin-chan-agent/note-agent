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
    },

    "claude": {
        "name": "Claude",
        "enabled": True,
        "official_domains": [
            "anthropic.com",
            "docs.anthropic.com",
        ],
    },

    "canva": {
        "name": "Canva",
        "enabled": True,
        "official_domains": [
            "canva.com",
            "canva.dev",
        ],
    },

    "capcut": {
        "name": "CapCut",
        "enabled": True,
        "official_domains": [
            "capcut.com",
            "support.capcut.com",
        ],
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