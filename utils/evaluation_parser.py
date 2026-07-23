import re


def parse_evaluation(text):
    return {
        "score": extract_score(text),
        "seo_score": extract_seo_score(text),
        "duplicate": extract_duplicate_result(text),
        "improvements": extract_improvements(text),
    }


def extract_score(text):
    m = re.search(r"SCORE\s*:\s*(\d+)", text)
    return int(m.group(1)) if m else 0


def extract_seo_score(text):
    m = re.search(r"SEO\s*:\s*(\d+)", text)
    return int(m.group(1)) if m else 0


def extract_duplicate_result(text):
    m = re.search(r"DUPLICATE\s*:\s*(OK|NG)", text)
    return m.group(1) if m else "NG"


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