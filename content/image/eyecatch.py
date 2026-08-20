from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os


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

    img = Image.open(background_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    width, height = img.size

    # =========================
    # Version 1.0 設定
    # =========================

    BASE_FONT_SIZE = 92
    MIN_FONT_SIZE = 64

    letter_spacing_ratio = 0.015
    line_spacing_ratio = 0.3

    # 日本語対応フォント
    base_dir = os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
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

    panel_width = panel_right - panel_left
    panel_height = panel_bottom - panel_top

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
            font_size * letter_spacing_ratio
        )

        # =========================
        # タイトルを2〜3行優先で分割
        # 最小フォントサイズのみ4行を許可
        # =========================

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
        # 2pxずつフォントを縮小
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
        font_size * line_spacing_ratio
    )

    # =========================
    # サイズ計算
    # =========================

    bbox = draw.textbbox(
        (0, 0),
        "あ",
        font=font,
    )

    line_height = bbox[3] - bbox[1]

    total_height = (
        line_height * len(lines)
        +
        line_spacing * (len(lines) - 1)
    )

    # =========================
    # タイトル全体をパネル中央へ
    # =========================

    start_y = (
        panel_top
        + (panel_height - total_height) / 2
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

    shadow_draw = ImageDraw.Draw(shadow)

    y = start_y

    for parts, line_width in zip(
        parts_list,
        line_widths,
    ):

        x = (
            panel_left
            +
            (panel_width - line_width) / 2
        )

        for text, _ in parts:

            for char in text:

                shadow_draw.text(
                    (x + 2, y + 3),
                    char,
                    font=font,
                    fill=(0, 0, 0, 70),
                )

                bbox = shadow_draw.textbbox(
                    (0, 0),
                    char,
                    font=font,
                )

                x += (
                    bbox[2] - bbox[0]
                    +
                    letter_spacing
                )

        y += line_height + line_spacing

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
            +
            (panel_width - line_width) / 2
        )

        for text, is_highlight in parts:

            if is_highlight:
                fill = (25, 105, 205, 255)
            else:
                fill = (255, 255, 255, 255)

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
                    bbox[2] - bbox[0]
                    +
                    letter_spacing
                )

        y += line_height + line_spacing

    img.convert("RGB").save(
        output_path,
        quality=95,
    )


def split_title(
    title,
    font,
    draw,
    max_width,
    allow_four_lines=False,
):
    """
    タイトルを自然な位置で分割する。

    基本ルール
    1. 1行で収まれば1行
    2. 2行を優先
    3. 2行が無理なら3行
    4. それでも無理な場合のみ4行
    5. ただし4行はallow_four_lines=Trueの場合のみ
    6. 【○○】は1行目に固定
    7. 英数字の単語途中では改行しない
    8. 意味のまとまりを途中で分割しない
    """

    import re

    title = title.strip()

    letter_spacing = font.size * 0.015

    # ====================================
    # 助詞
    # ====================================

    particles = [
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
        "から",
        "まで",
        "より",
        "だけ",
        "ほど",
        "しか",
        "こそ",
        "など",
    ]

    # ====================================
    # 意味のまとまり
    # ====================================

    semantic_marks = [
        "向け",
        "活用",
        "方法",
        "コツ",
        "比較",
        "まとめ",
        "ロードマップ",
        "収益化",
        "効率化",
        "自動化",
        "チェックリスト",
        "時短術",
        "成功戦略",
        "徹底解説",
        "メリット・デメリット",
        "メリット",
        "デメリット",
        "料金比較",
        "機能比較",
    ]

    # ====================================
    # 改行途中にしたくない語句
    # ====================================

    protected_phrases = [
        "AI副業",
        "AIチャット",
        "AI画像",
        "AIデザイン",
        "AI自動化",
        "AIショート動画",
        "ショート動画",
        "動画編集",
        "動画制作",
        "動画副業",
        "時短術",
        "収益化",
        "効率化",
        "自動化",
        "成功戦略",
        "料金比較",
        "機能比較",
        "メリット・デメリット",
        "無料版",
        "有料版",
        "ショート動画収益化",
    ]

    punctuation_marks = [
        "！",
        "？",
        "。",
        "、",
        "：",
        ":",
    ]

    # ====================================
    # 【○○】を分離
    # ====================================

    prefix_match = re.match(
        r"^(【[^】]+】)\s*(.*)$",
        title,
    )

    prefix = None
    body = title

    if prefix_match:
        prefix = prefix_match.group(1).strip()
        body = prefix_match.group(2).strip()

    # ====================================
    # 1行の幅
    # ====================================

    def get_width(text):
        return measure_line(
            draw,
            [(text, False)],
            font,
            letter_spacing,
        )

    # ====================================
    # 英数字単語の途中か
    # ====================================

    def is_ascii_alnum(char):
        return bool(
            re.fullmatch(
                r"[A-Za-z0-9]",
                char,
            )
        )

    def is_inside_ascii_word(
        index,
        text,
    ):
        if index <= 0 or index >= len(text):
            return False

        left = text[index - 1]
        right = text[index]

        return (
            is_ascii_alnum(left)
            and is_ascii_alnum(right)
        )

    # ====================================
    # 保護語句の途中か
    # ====================================

    def is_inside_protected_phrase(
        index,
        text,
    ):
        for phrase in protected_phrases:

            start = 0

            while True:

                position = text.find(
                    phrase,
                    start,
                )

                if position == -1:
                    break

                end = (
                    position
                    + len(phrase)
                )

                if (
                    position
                    < index
                    < end
                ):
                    return True

                start = end

        return False

    # ====================================
    # 改行可能位置か
    # ====================================

    def is_valid_boundary(
        index,
        text,
    ):
        if index <= 0 or index >= len(text):
            return False

        # 英数字単語の途中
        if is_inside_ascii_word(
            index,
            text,
        ):
            return False

        # 意味のまとまりの途中
        if is_inside_protected_phrase(
            index,
            text,
        ):
            return False

        left = text[:index].strip()
        right = text[index:].strip()

        if not left or not right:
            return False

        # 次の行が助詞から始まる
        if any(
            right.startswith(p)
            for p in particles
        ):
            return False

        return True

    # ====================================
    # 分割位置の評価
    # ====================================

    def boundary_score(
        left,
        right,
        left_width,
        right_width,
    ):
        score = 0

        # --------------------------------
        # 行幅のバランス
        # --------------------------------

        score += abs(
            left_width
            -
            right_width
        )

        # --------------------------------
        # 助詞の直後
        # --------------------------------

        for particle in particles:

            if left.endswith(
                particle
            ):
                score -= 300
                break

        # --------------------------------
        # 記号の直後
        # --------------------------------

        if left.endswith(
            tuple(punctuation_marks)
        ):
            score -= 500

        # --------------------------------
        # 意味のまとまり
        # --------------------------------

        for mark in semantic_marks:

            if left.endswith(mark):
                score -= 300
                break

        return score

    # ====================================
    # 2行候補
    # ====================================

    def make_two_line_candidates(
        text,
    ):
        candidates = []

        for i in range(
            1,
            len(text),
        ):

            if not is_valid_boundary(
                i,
                text,
            ):
                continue

            line1 = text[:i].strip()
            line2 = text[i:].strip()

            width1 = get_width(line1)
            width2 = get_width(line2)

            if (
                width1 > max_width
                or width2 > max_width
            ):
                continue

            score = boundary_score(
                line1,
                line2,
                width1,
                width2,
            )

            candidates.append(
                (
                    score,
                    [
                        line1,
                        line2,
                    ],
                )
            )

        return candidates

    # ====================================
    # 3行候補
    # ====================================

    def make_three_line_candidates(
        text,
    ):
        candidates = []

        length = len(text)

        for i in range(
            1,
            length - 1,
        ):

            if not is_valid_boundary(
                i,
                text,
            ):
                continue

            line1 = text[:i].strip()

            width1 = get_width(line1)

            if width1 > max_width:
                continue

            for j in range(
                i + 1,
                length,
            ):

                if not is_valid_boundary(
                    j,
                    text,
                ):
                    continue

                line2 = text[i:j].strip()
                line3 = text[j:].strip()

                if (
                    not line2
                    or not line3
                ):
                    continue

                width2 = get_width(line2)
                width3 = get_width(line3)

                if (
                    width2 > max_width
                    or width3 > max_width
                ):
                    continue

                widths = [
                    width1,
                    width2,
                    width3,
                ]

                score = (
                    max(widths)
                    -
                    min(widths)
                )

                # 意味のまとまり
                for line in [
                    line1,
                    line2,
                ]:
                    for mark in semantic_marks:

                        if line.endswith(mark):
                            score -= 250
                            break

                # 記号の直後
                for line in [
                    line1,
                    line2,
                ]:
                    if line.endswith(
                        tuple(
                            punctuation_marks
                        )
                    ):
                        score -= 350

                candidates.append(
                    (
                        score,
                        [
                            line1,
                            line2,
                            line3,
                        ],
                    )
                )

        return candidates

    # ====================================
    # 4行候補
    # ====================================

    def make_four_line_candidates(
        text,
    ):
        candidates = []

        length = len(text)

        for i in range(
            1,
            length - 2,
        ):

            if not is_valid_boundary(
                i,
                text,
            ):
                continue

            line1 = text[:i].strip()
            width1 = get_width(line1)

            if width1 > max_width:
                continue

            for j in range(
                i + 1,
                length - 1,
            ):

                if not is_valid_boundary(
                    j,
                    text,
                ):
                    continue

                line2 = text[i:j].strip()
                width2 = get_width(line2)

                if width2 > max_width:
                    continue

                for k in range(
                    j + 1,
                    length,
                ):

                    if not is_valid_boundary(
                        k,
                        text,
                    ):
                        continue

                    line3 = text[j:k].strip()
                    line4 = text[k:].strip()

                    if (
                        not line3
                        or not line4
                    ):
                        continue

                    width3 = get_width(line3)
                    width4 = get_width(line4)

                    if (
                        width3 > max_width
                        or width4 > max_width
                    ):
                        continue

                    widths = [
                        width1,
                        width2,
                        width3,
                        width4,
                    ]

                    score = (
                        max(widths)
                        -
                        min(widths)
                    )

                    candidates.append(
                        (
                            score,
                            [
                                line1,
                                line2,
                                line3,
                                line4,
                            ],
                        )
                    )

        return candidates

    # ====================================
    # 1行で収まる場合
    # ====================================

    if not prefix:

        if get_width(title) <= max_width:
            return [title]

    else:

        if (
            get_width(prefix)
            <= max_width
            and not body
        ):
            return [prefix]

        if (
            get_width(prefix)
            <= max_width
            and get_width(body)
            <= max_width
        ):
            return [
                prefix,
                body,
            ]

    # ====================================
    # 【○○】なし
    # ====================================

    if not prefix:

        # ------------------------------
        # 2行を最優先
        # ------------------------------

        candidates = (
            make_two_line_candidates(
                body
            )
        )

        if candidates:

            candidates.sort(
                key=lambda x: x[0]
            )

            return candidates[0][1]

        # ------------------------------
        # 3行
        # ------------------------------

        candidates = (
            make_three_line_candidates(
                body
            )
        )

        if candidates:

            candidates.sort(
                key=lambda x: x[0]
            )

            return candidates[0][1]

        # ------------------------------
        # 4行
        # 最小フォントサイズのみ
        # ------------------------------

        if allow_four_lines:

            candidates = (
                make_four_line_candidates(
                    body
                )
            )

            if candidates:

                candidates.sort(
                    key=lambda x: x[0]
                )

                return candidates[0][1]

    # ====================================
    # 【○○】あり
    # ====================================

    else:

        if (
            get_width(prefix)
            <= max_width
        ):

            # --------------------------
            # 本文2行
            # --------------------------

            candidates = (
                make_two_line_candidates(
                    body
                )
            )

            if candidates:

                candidates.sort(
                    key=lambda x: x[0]
                )

                return [
                    prefix,
                    *candidates[0][1],
                ]

            # --------------------------
            # 本文3行
            # --------------------------

            candidates = (
                make_three_line_candidates(
                    body
                )
            )

            if candidates:

                candidates.sort(
                    key=lambda x: x[0]
                )

                return [
                    prefix,
                    *candidates[0][1],
                ]

            # --------------------------
            # 本文4行
            # --------------------------

            if allow_four_lines:

                candidates = (
                    make_four_line_candidates(
                        body
                    )
                )

                if candidates:

                    candidates.sort(
                        key=lambda x: x[0]
                    )

                    return [
                        prefix,
                        *candidates[0][1],
                    ]

    # ====================================
    # 最終手段
    # ====================================

    # ここまで来た場合は、
    # 自然な分割候補が見つからない。
    #
    # ただし英数字・保護語句の途中では
    # 絶対に分割しない。

    text = body

    if not text:
        return [prefix] if prefix else [title]

    target_lines = (
        4 if allow_four_lines else 3
    )

    result = []

    remaining = text

    for line_number in range(
        target_lines - 1
    ):

        if not remaining:
            break

        target_length = (
            len(remaining)
            /
            (
                target_lines
                -
                line_number
            )
        )

        best_index = None
        best_distance = None

        for i in range(
            1,
            len(remaining),
        ):

            if not is_valid_boundary(
                i,
                remaining,
            ):
                continue

            distance = abs(
                i - target_length
            )

            if (
                best_distance is None
                or distance < best_distance
            ):
                best_distance = distance
                best_index = i

        if best_index is None:
            break

        result.append(
            remaining[
                :best_index
            ].strip()
        )

        remaining = (
            remaining[
                best_index:
            ].strip()
        )

    if remaining:
        result.append(
            remaining
        )

    if prefix:
        return [
            prefix,
            *result,
        ]

    return result


def split_highlights(
    text,
    highlight_keywords,
):
    """
    強調キーワードと通常文字を分離する。
    """

    parts = []
    rest = text

    while rest:

        matches = []

        for keyword in highlight_keywords:

            index = rest.find(keyword)

            if index >= 0:
                matches.append(
                    (index, keyword)
                )

        if not matches:

            parts.append(
                (rest, False)
            )

            break

        index, keyword = min(
            matches,
            key=lambda x: x[0],
        )

        if index > 0:

            parts.append(
                (rest[:index], False)
            )

        parts.append(
            (keyword, True)
        )

        rest = rest[
            index + len(keyword):
        ]

    return parts


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

        for char in text:

            bbox = draw.textbbox(
                (0, 0),
                char,
                font=font,
            )

            width += (
                bbox[2] - bbox[0]
                +
                letter_spacing
            )

    return max(
        0,
        width - letter_spacing,
    )
