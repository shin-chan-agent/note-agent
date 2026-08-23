import os
import re

from PIL import Image, ImageDraw, ImageFont, ImageFilter


# =========================================================
# タイトル分割用の共通ルール
# =========================================================

FORBIDDEN_LINE_STARTS = [
    # 助詞・接続
    "が",
    "は",
    "の",
    "で",
    "を",
    "に",
    "へ",
    "と",
    "も",
    "や",

    # 接続・範囲
    "から",
    "まで",
    "より",
    "だけ",
    "ほど",
    "しか",
    "こそ",
    "など",

    # 動詞・文末表現
    "する",
    "した",
    "して",
    "できる",
    "できない",
    "なる",
    "なった",
    "ならない",
    "ならず",

    # 補助表現
    "ため",
    "ので",
    "よう",
    "たい",
    "ない",
    "なく",

    # 丁寧表現
    "です",
    "ます",
    "でした",
    "でしょう",

    # 記号
    "。",
    "、",
    "！",
    "？",
    "：",
    "」",
    "』",
    "）",
    ")",
    "】",
]


PARTICLES = [
    "が",
    "は",
    "の",
    "で",
    "を",
    "に",
    "へ",
    "と",
    "も",
    "や",
]


PREFERRED_END_MARKS = [
    "！",
    "？",
    "：",
    "。",
    "、",
    "｜",
]


SEMANTIC_MARKS = [
    "ショート動画",
    "AI副業",
    "動画副業",
    "収益化",
    "マネタイズ",
    "自動化",
    "効率化",
    "時短",
    "成功戦略",
    "実践ガイド",
    "チェックリスト",
    "ロードマップ",
    "メリット",
    "デメリット",
    "比較",
    "レビュー",
    "原因",
    "回避術",
    "活用術",
    "方法",
    "コツ",
    "おすすめ設定",
]


COMPOUND_PATTERNS = [
    "ショート動画",
    "AI副業",
    "動画副業",
    "収益化",
    "マネタイズ",
    "自動化",
    "効率化",
    "活用術",
    "実践ガイド",
    "成功戦略",
    "回避術",
    "おすすめ設定",
]


# =========================================================
# アイキャッチ生成
# =========================================================

def create_eyecatch(
    background_path,
    output_path,
    title,
    highlight_keywords,
):
    """
    固定背景画像にタイトルを自動配置して
    アイキャッチ画像を生成する。
    """

    img = Image.open(
        background_path
    ).convert("RGBA")

    draw = ImageDraw.Draw(img)

    width, height = img.size

    # =========================
    # Version 1.0 設定
    # =========================

    BASE_FONT_SIZE = 86
    MIN_FONT_SIZE = 50

    letter_spacing_ratio = 0.015
    line_spacing_ratio = 0.3

    # =========================
    # 日本語対応フォント
    # =========================

    base_dir = os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file)
            )
        )
    )

    font_candidates = [
        os.path.join(
            base_dir,
            "fonts",
            "NotoSansCJKjp-Bold.min.ttf",
        ),
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    ]

    font_path = next(
        (
            path
            for path in font_candidates
            if os.path.exists(path)
        ),
        None,
    )

    if not font_path:
        raise FileNotFoundError(
            "日本語フォントが見つかりません。"
        )

    # =========================
    # タイトル領域
    # =========================

    panel_left = int(width * 0.15)
    panel_right = int(width * 0.85)

    panel_top = int(height * 0.25)
    panel_bottom = int(height * 0.75)

    panel_width = (
        panel_right - panel_left
    )

    panel_height = (
        panel_bottom - panel_top
    )

    # =========================
    # フォントサイズを自動調整
    # =========================

    font_size = BASE_FONT_SIZE

    while font_size >= MIN_FONT_SIZE:

        font = ImageFont.truetype(
            font_path,
            font_size,
        )

        letter_spacing = (
            font_size
            * letter_spacing_ratio
        )

        # 最小フォントサイズまで
        # 縮小した場合のみ4行を許可
        allow_four_lines = (
            font_size == MIN_FONT_SIZE
        )

        lines = split_title(
            title,
            font,
            draw,
            panel_width,
            allow_four_lines=allow_four_lines,
        )

        parts_list = [
            split_highlights(
                line,
                highlight_keywords,
            )
            for line in lines
        ]

        line_widths = [
            measure_line(
                draw,
                parts,
                font,
                letter_spacing,
            )
            for parts in parts_list
        ]

        # =========================
        # 全行がパネル幅に収まれば確定
        # =========================

        if max(line_widths) <= panel_width:

            print(
                f"[DEBUG] lines={lines}"
            )

            print(
                f"[DEBUG] font_size={font_size}"
            )

            print(
                f"[DEBUG] line_count={len(lines)}"
            )

            break

        # =========================
        # 2pxずつ縮小
        # =========================

        font_size -= 2

    else:

        raise ValueError(
            "タイトルを指定範囲内に収められませんでした。"
        )

    # =========================
    # 行間
    # =========================

    line_spacing = int(
        font_size
        * line_spacing_ratio
    )

    # =========================
    # サイズ計算
    # =========================

    bbox = draw.textbbox(
        (0, 0),
        "あ",
        font=font,
    )

    line_height = (
        bbox[3] - bbox[1]
    )

    total_height = (
        line_height * len(lines)
        + line_spacing
        * (len(lines) - 1)
    )

    # =========================
    # タイトル全体を中央配置
    # =========================

    start_y = (
        panel_top
        + (
            panel_height
            - total_height
        ) / 2
        - 20
    )

    # =========================
    # 影
    # =========================

    shadow = Image.new(
        "RGBA",
        img.size,
        (0, 0, 0, 0),
    )

    shadow_draw = ImageDraw.Draw(
        shadow
    )

    y = start_y

    for parts, line_width in zip(
        parts_list,
        line_widths,
    ):

        x = (
            panel_left
            + (
                panel_width
                - line_width
            ) / 2
        )

        for text, _ in parts:

            for char in text:

                shadow_draw.text(
                    (x + 2, y + 3),
                    char,
                    font=font,
                    fill=(0, 0, 0, 70),
                )

                bbox = (
                    shadow_draw.textbbox(
                        (0, 0),
                        char,
                        font=font,
                    )
                )

                x += (
                    bbox[2]
                    - bbox[0]
                    + letter_spacing
                )

        y += (
            line_height
            + line_spacing
        )

    shadow = shadow.filter(
        ImageFilter.GaussianBlur(1.5)
    )

    img.alpha_composite(shadow)

    # =========================
    # タイトル本体
    # =========================

    draw = ImageDraw.Draw(img)

    y = start_y

    for parts, line_width in zip(
        parts_list,
        line_widths,
    ):

        x = (
            panel_left
            + (
                panel_width
                - line_width
            ) / 2
        )

        for text, is_highlight in parts:

            if is_highlight:
                fill = (
                    25,
                    105,
                    205,
                    255,
                )
            else:
                fill = (
                    255,
                    255,
                    255,
                    255,
                )

            for char in text:

                draw.text(
                    (x, y),
                    char,
                    font=font,
                    fill=fill,
                )

                bbox = draw.textbbox(
                    (0, 0),
                    char,
                    font=font,
                )

                x += (
                    bbox[2]
                    - bbox[0]
                    + letter_spacing
                )

        y += (
            line_height
            + line_spacing
        )

    img.convert("RGB").save(
        output_path,
        quality=95,
    )


# =========================================================
# タイトル分割
# =========================================================

def split_title(
    title,
    font,
    draw,
    max_width,
    allow_four_lines=False,
):
    """
    日本語として自然な意味のまとまりを優先して
    タイトルを2〜3行に分割する。

    優先順位

    1. 1行で収まる
    2. 【】部分を独立
    3. 2行
    4. 3行
    5. 最小フォントサイズ時のみ4行
    6. 最終フォールバック
    """

    title = title.strip()

    if not title:
        raise ValueError(
            "タイトルが空です。"
        )

    letter_spacing = (
        font.size * 0.015
    )

    # =====================================================
    # 1行で収まる場合
    # =====================================================

    if measure_line(
        draw,
        [(title, False)],
        font,
        letter_spacing,
    ) <= max_width:

        return [title]

    # =====================================================
    # 【】部分を先頭行として独立
    # =====================================================

    bracket_match = re.match(
        r"^(【[^】]+】)(.*)$",
        title,
    )

    if bracket_match:

        prefix = (
            bracket_match
            .group(1)
            .strip()
        )

        remaining = (
            bracket_match
            .group(2)
            .strip()
        )

        if remaining:

            remaining_lines = (
                _split_title_body(
                    remaining,
                    font,
                    draw,
                    max_width,
                    max_lines=2,
                )
            )

            if len(remaining_lines) <= 2:

                return [
                    prefix,
                    *remaining_lines,
                ]

    # =====================================================
    # 通常タイトル
    # =====================================================

    max_lines = (
        4
        if allow_four_lines
        else 3
    )

    return _split_title_body(
        title,
        font,
        draw,
        max_width,
        max_lines=max_lines,
    )


# =========================================================
# タイトル本文分割
# =========================================================

def _split_title_body(
    title,
    font,
    draw,
    max_width,
    max_lines=3,
):
    """
    タイトル本文を指定行数以内に分割する。

    「から」の途中、
    「する」の途中、
    「ショート動画」の途中など、
    不自然な改行を避ける。
    """

    title = title.strip()

    if not title:
        return []

    letter_spacing = (
        font.size * 0.015
    )

    max_lines = max(
        2,
        max_lines,
    )

    # =====================================================
    # 2行
    # =====================================================

    candidates = _build_two_line_candidates(
        title,
        font,
        draw,
        max_width,
        letter_spacing,
    )

    if candidates:

        candidates.sort(
            key=lambda x: x[0]
        )

        best = candidates[0]

        return [
            best[1],
            best[2],
        ]

    # =====================================================
    # 3行
    # =====================================================

    if max_lines >= 3:

        candidates = (
            _build_three_line_candidates(
                title,
                font,
                draw,
                max_width,
                letter_spacing,
            )
        )

        if candidates:

            candidates.sort(
                key=lambda x: x[0]
            )

            best = candidates[0]

            return [
                best[1],
                best[2],
                best[3],
            ]

    # =====================================================
    # 4行
    # =====================================================

    if max_lines >= 4:

        candidates = (
            _build_four_line_candidates(
                title,
                font,
                draw,
                max_width,
                letter_spacing,
            )
        )

        if candidates:

            candidates.sort(
                key=lambda x: x[0]
            )

            best = candidates[0]

            return [
                best[1],
                best[2],
                best[3],
                best[4],
            ]

    # =====================================================
    # 最終フォールバック
    # =====================================================

    return _fallback_split_title(
        title,
        font,
        draw,
        max_width,
        letter_spacing,
    )


# =========================================================
# 2行候補
# =========================================================

def _build_two_line_candidates(
    title,
    font,
    draw,
    max_width,
    letter_spacing,
):

    candidates = []

    for index in range(
        1,
        len(title),
    ):

        left = (
            title[:index]
            .strip()
        )

        right = (
            title[index:]
            .strip()
        )

        if not left or not right:
            continue

        if _is_bad_break(
            title,
            index,
            left,
            right,
        ):
            continue

        left_width = measure_line(
            draw,
            [(left, False)],
            font,
            letter_spacing,
        )

        right_width = measure_line(
            draw,
            [(right, False)],
            font,
            letter_spacing,
        )

        if (
            left_width > max_width
            or right_width > max_width
        ):
            continue

        score = _score_break(
            title,
            index,
            left,
            right,
            [
                left_width,
                right_width,
            ],
        )

        candidates.append(
            (
                score,
                left,
                right,
            )
        )

    return candidates


# =========================================================
# 3行候補
# =========================================================

def _build_three_line_candidates(
    title,
    font,
    draw,
    max_width,
    letter_spacing,
):

    candidates = []

    for i in range(
        1,
        len(title) - 1,
    ):

        line1 = (
            title[:i]
            .strip()
        )

        if not line1:
            continue

        if _is_bad_line_end(line1):
            continue

        width1 = measure_line(
            draw,
            [(line1, False)],
            font,
            letter_spacing,
        )

        if width1 > max_width:
            continue

        for j in range(
            i + 1,
            len(title),
        ):

            line2 = (
                title[i:j]
                .strip()
            )

            line3 = (
                title[j:]
                .strip()
            )

            if not line2 or not line3:
                continue

            if _is_bad_break(
                title,
                i,
                line1,
                line2,
            ):
                continue

            if _is_bad_break(
                title,
                j,
                line2,
                line3,
            ):
                continue

            if _is_bad_line_end(
                line2
            ):
                continue

            width2 = measure_line(
                draw,
                [(line2, False)],
                font,
                letter_spacing,
            )

            width3 = measure_line(
                draw,
                [(line3, False)],
                font,
                letter_spacing,
            )

            if (
                width2 > max_width
                or width3 > max_width
            ):
                continue

            score = _score_n_lines(
                title,
                [i, j],
                [
                    line1,
                    line2,
                    line3,
                ],
                [
                    width1,
                    width2,
                    width3,
                ],
            )

            candidates.append(
                (
                    score,
                    line1,
                    line2,
                    line3,
                )
            )

    return candidates


# =========================================================
# 4行候補
# =========================================================

def _build_four_line_candidates(
    title,
    font,
    draw,
    max_width,
    letter_spacing,
):

    candidates = []

    for i in range(
        1,
        len(title) - 2,
    ):

        line1 = (
            title[:i]
            .strip()
        )

        if (
            not line1
            or _is_bad_line_end(line1)
        ):
            continue

        width1 = measure_line(
            draw,
            [(line1, False)],
            font,
            letter_spacing,
        )

        if width1 > max_width:
            continue

        for j in range(
            i + 1,
            len(title) - 1,
        ):

            line2 = (
                title[i:j]
                .strip()
            )

            if (
                not line2
                or _is_bad_line_end(line2)
            ):
                continue

            if _is_bad_break(
                title,
                i,
                line1,
                line2,
            ):
                continue

            width2 = measure_line(
                draw,
                [(line2, False)],
                font,
                letter_spacing,
            )

            if width2 > max_width:
                continue

            for k in range(
                j + 1,
                len(title),
            ):

                line3 = (
                    title[j:k]
                    .strip()
                )

                line4 = (
                    title[k:]
                    .strip()
                )

                if (
                    not line3
                    or not line4
                ):
                    continue

                if _is_bad_line_end(
                    line3
                ):
                    continue

                if _is_bad_break(
                    title,
                    j,
                    line2,
                    line3,
                ):
                    continue

                if _is_bad_break(
                    title,
                    k,
                    line3,
                    line4,
                ):
                    continue

                width3 = measure_line(
                    draw,
                    [(line3, False)],
                    font,
                    letter_spacing,
                )

                width4 = measure_line(
                    draw,
                    [(line4, False)],
                    font,
                    letter_spacing,
                )

                if (
                    width3 > max_width
                    or width4 > max_width
                ):
                    continue

                score = _score_n_lines(
                    title,
                    [i, j, k],
                    [
                        line1,
                        line2,
                        line3,
                        line4,
                    ],
                    [
                        width1,
                        width2,
                        width3,
                        width4,
                    ],
                )

                candidates.append(
                    (
                        score,
                        line1,
                        line2,
                        line3,
                        line4,
                    )
                )

    return candidates


# =========================================================
# 不自然な改行判定
# =========================================================

def _is_bad_break(
    title,
    index,
    left,
    right,
):
    """
    改行位置として明確に不自然なケースを除外する。
    """

    if not left or not right:
        return True

    # -------------------------
    # 次の行が助詞・接続語から始まる
    # -------------------------

    if any(
        right.startswith(word)
        for word in FORBIDDEN_LINE_STARTS
    ):
        return True

    # -------------------------
    # 複合語の途中を禁止
    # -------------------------

    for word in COMPOUND_PATTERNS:

        for k in range(
            1,
            len(word),
        ):

            if left.endswith(
                word[:k]
            ):
                return True

    # -------------------------
    # 括弧類
    # -------------------------

    if right.startswith(
        (
            "」",
            "』",
            "）",
            ")",
            "】",
        )
    ):
        return True

    if left.endswith(
        (
            "「",
            "『",
            "（",
            "(",
            "【",
        )
    ):
        return True

    return False


def _is_bad_line_end(line):
    """
    行末として不自然な位置を判定する。
    """

    if not line:
        return True

    if any(
        line.endswith(word)
        for word in FORBIDDEN_LINE_STARTS
    ):
        return True

    if line.endswith(
        (
            "「",
            "『",
            "（",
            "(",
            "【",
        )
    ):
        return True

    return False


# =========================================================
# 2行スコア
# =========================================================

def _score_break(
    title,
    index,
    left,
    right,
    widths,
):
    """
    2行分割のスコア。
    小さいほど良い。
    """

    score = 0

    max_width = max(widths)
    min_width = min(widths)

    # -------------------------
    # 左右の幅を近づける
    # -------------------------

    score += (
        max_width
        - min_width
    )

    # -------------------------
    # 記号直後
    # -------------------------

    if left.endswith(
        tuple(PREFERRED_END_MARKS)
    ):
        score -= 1200

    # -------------------------
    # 助詞直後
    # -------------------------

    if left[-1:] in PARTICLES:
        score -= 500

    # -------------------------
    # 意味のまとまり
    # -------------------------

    for mark in SEMANTIC_MARKS:

        if left.endswith(mark):
            score -= 700

    # -------------------------
    # 複合語の直後
    # -------------------------

    for mark in COMPOUND_PATTERNS:

        if left.endswith(mark):
            score -= 900

    # -------------------------
    # 中央から離れすぎる分割を少し減点
    # -------------------------

    middle = len(title) / 2

    score += (
        abs(index - middle)
        * 2
    )

    return score


# =========================================================
# 3〜4行共通スコア
# =========================================================

def _score_n_lines(
    title,
    break_indexes,
    lines,
    widths,
):
    """
    3〜4行分割の共通スコア。
    小さいほど良い。
    """

    max_width = max(widths)
    min_width = min(widths)

    score = (
        max_width
        - min_width
    )

    # -------------------------
    # 極端に短い行を避ける
    # -------------------------

    average = (
        sum(widths)
        / len(widths)
    )

    for width in widths:

        ratio = (
            width
            / average
        )

        if ratio < 0.55:
            score += 900

        elif ratio < 0.70:
            score += 350

    # -------------------------
    # 各改行位置
    # -------------------------

    for index, line in zip(
        break_indexes,
        lines[:-1],
    ):

        right = (
            title[index:]
            .strip()
        )

        # 記号直後
        if line.endswith(
            tuple(PREFERRED_END_MARKS)
        ):
            score -= 1200

        # 助詞直後
        if line[-1:] in PARTICLES:
            score -= 400

        # 意味のまとまり
        for mark in SEMANTIC_MARKS:

            if line.endswith(mark):
                score -= 700

        # 複合語
        for mark in COMPOUND_PATTERNS:

            if line.endswith(mark):
                score -= 900

        # 念のため次行開始もチェック
        if any(
            right.startswith(word)
            for word in FORBIDDEN_LINE_STARTS
        ):
            score += 5000

    # -------------------------
    # 改行位置が近すぎる場合
    # -------------------------

    for a, b in zip(
        break_indexes,
        break_indexes[1:],
    ):

        distance = b - a

        if distance <= 2:
            score += 2500

        elif distance == 3:
            score += 800

    return score


# =========================================================
# 最終フォールバック
# =========================================================

def _fallback_split_title(
    title,
    font,
    draw,
    max_width,
    letter_spacing,
):
    """
    通常候補が存在しない場合の安全なフォールバック。
    """

    middle = len(title) // 2

    candidates = []

    for offset in range(
        len(title)
    ):

        indexes = [
            middle - offset,
            middle + offset,
        ]

        for index in indexes:

            if (
                index <= 0
                or index >= len(title)
            ):
                continue

            left = (
                title[:index]
                .strip()
            )

            right = (
                title[index:]
                .strip()
            )

            if not left or not right:
                continue

            if _is_bad_break(
                title,
                index,
                left,
                right,
            ):
                continue

            left_width = measure_line(
                draw,
                [(left, False)],
                font,
                letter_spacing,
            )

            right_width = measure_line(
                draw,
                [(right, False)],
                font,
                letter_spacing,
            )

            if (
                left_width > max_width
                or right_width > max_width
            ):
                continue

            candidates.append(
                (
                    abs(
                        index - middle
                    ),
                    left,
                    right,
                )
            )

        if candidates:
            break

    if candidates:

        candidates.sort(
            key=lambda x: x[0]
        )

        return [
            candidates[0][1],
            candidates[0][2],
        ]

    # 極端に長いタイトルなど、
    # どうしても分割できない場合。
    # create_eyecatch側でフォントを縮小する。
    return [title]


# =========================================================
# 強調キーワード分離
# =========================================================

def split_highlights(
    text,
    highlight_keywords,
):
    """
    強調キーワードと通常文字を分離する。
    """

    parts = []
    rest = text

    highlight_keywords = (
        highlight_keywords or []
    )

    while rest:

        matches = []

        for keyword in highlight_keywords:

            if not keyword:
                continue

            index = rest.find(
                keyword
            )

            if index >= 0:

                matches.append(
                    (
                        index,
                        keyword,
                    )
                )

        if not matches:

            parts.append(
                (
                    rest,
                    False,
                )
            )

            break

        index, keyword = min(
            matches,
            key=lambda x: (
                x[0],
                -len(x[1]),
            ),
        )

        if index > 0:

            parts.append(
                (
                    rest[:index],
                    False,
                )
            )

        parts.append(
            (
                keyword,
                True,
            )
        )

        rest = rest[
            index + len(keyword):
        ]

    return parts


# =========================================================
# 文字幅計測
# =========================================================

def measure_line(
    draw,
    parts,
    font,
    letter_spacing,
):
    """
    1行の横幅を計算する。
    """

    width = 0

    for text, _ in parts:

        if not text:
            continue

        for char in text:

            bbox = draw.textbbox(
                (0, 0),
                char,
                font=font,
            )

            width += (
                bbox[2]
                - bbox[0]
                + letter_spacing
            )

    return max(
        0,
        width - letter_spacing,
    )