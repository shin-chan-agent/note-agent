


def extract_score(text):
    m = re.search(r"SCORE\s*:\s*(\d+)", text, re.IGNORECASE)

    if m:
        return int(m.group(1))

    return 0


def extract_seo_score(text):
    m = re.search(r"SEO\s*:\s*(\d+)", text, re.IGNORECASE)
    return int(m.group(1)) if m else 0


