import re

from utils.evaluation_parser import (
    parse_evaluation,
    extract_score,
    extract_seo_score,
    extract_duplicate_result,
    extract_improvements,
)


def extract_score(text):
    m = re.search(r"SCORE\s*:\s*(\d+)", text, re.IGNORECASE)

    if m:
        return int(m.group(1))

    return 0


def extract_seo_score(text):
    m = re.search(r"SEO\s*:\s*(\d+)", text, re.IGNORECASE)
    return int(m.group(1)) if m else 0


def extract_duplicate_result(text):
    m = re.search(r"DUPLICATE\s*:\s*(OK|NG)", text, re.IGNORECASE)
    return m.group(1).upper() if m else "NG"


def extract_improvements(text):
    m = re.search(
        r"【必須】\s*(.*?)(?:【推奨】|$)",
        text,
        re.DOTALL,
    )

    if not m:
        return ""

    improvements = m.group(1).strip()

    if improvements == "なし":
        return ""

    return improvements