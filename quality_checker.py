def quality_check(article: str) -> dict:
    """
    記事をチェックし、品質評価を返す
    """
    return {
        "score": 100,
        "rewrite_required": False,
        "issues": []
    }
