# Geminiモデル設定
GEMINI_MODEL_ARTICLE = "gemini-2.5-flash"
GEMINI_MODEL_EVALUATION = "gemini-2.5-flash"
GEMINI_MODEL_REWRITE = "gemini-2.5-flash"
GEMINI_MODEL_SNS = "gemini-2.5-flash"
GEMINI_MODEL_VIDEO = "gemini-2.5-flash"
GEMINI_MODEL_LATEST = "gemini-2.5-flash"


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
MAX_KNOWLEDGE_AGE_DAYS = 14
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

    "perplexity": {
        "name": "Perplexity",
        "enabled": True,
        "official_domains": [
            "perplexity.ai",
        ],
    },

    "gemini_notebook": {
        "name": "Gemini Notebook",
        "enabled": True,
        "official_domains": [
            "notebooklm.google.com",
            "blog.google",
        ],
    },

    "copilot": {
        "name": "Microsoft Copilot",
        "enabled": True,
        "official_domains": [
            "microsoft.com",
            "copilot.microsoft.com",
            "support.microsoft.com",
            "learn.microsoft.com",
        ],
    },

    "claude_code": {
        "name": "Claude Code",
        "enabled": True,
        "official_domains": [
            "anthropic.com",
            "docs.anthropic.com",
        ],
    },
}


THEME_SERVICES = {
    "ショート動画": [
        "chatgpt",
        "gemini",
        "canva",
        "capcut",
    ],

    "SNS運用": [
        "chatgpt",
        "gemini",
        "claude",
        "canva",
    ],

    "AI×仕事効率化": [
        "chatgpt",
        "gemini",
        "claude",
        "copilot",
    ],

    "AI自動化": [
        "chatgpt",
        "gemini",
        "claude",
        "copilot",
        "claude_code",
    ],

    "AIリサーチ・情報収集": [
        "perplexity",
        "chatgpt",
        "gemini",
        "gemini_notebook",
        "claude",
    ],
}

    "AI×仕事効率化": {
        "作業フロー": [
            "chatgpt",
            "gemini",
            "claude",
            "copilot",
        ],
        "業務改善": [
            "chatgpt",
            "copilot",
            "claude",
            "gemini",
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
            "gemini",
            "copilot",
            "claude_code",
        ],
        "失敗回避": [
            "chatgpt",
            "gemini",
            "claude",
            "copilot",
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
            "gemini",
            "gemini_notebook",
        ],
        "検証・判断": [
            "perplexity",
            "gemini_notebook",
            "claude",
            "gemini",
        ],
    },
}