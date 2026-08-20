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
    MIN_FONT_SIZE = 56

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
        # タイトルを2〜3行に分割
        # =========================

        lines = split_title(
            title,
            font,
            draw,
            panel_width,
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

        # 全行がパネル幅に収まれば確定
        if max(line_widths) <= panel_width:

            print(f"[DEBUG] lines={lines}")
            print(f"[DEBUG] font_size={font_size}")

            break

        font_size -= 2

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
):
    """
    タイトルを自然な位置で1〜4行に分割する。

    基本方針
    1. 1行で収まる場合は1行
    2. 「【○○】」がある場合は1行目に固定
    3. 本文は2〜3行を優先
    4. 必要な場合のみ4行を使用
    5. 英数字の単語を途中で分割しない
    6. 助詞や意味のまとまりを考慮する
    7. 行幅のバランスも考慮する
    """

    import re

    title = title.strip()

    letter_spacing = font.size * 0.015

    # ------------------------------------
    # 基本ルール
    # ------------------------------------

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
    ]

    punctuation_marks = [
        "！",
        "？",
        "。",
        "、",
        "：",
        "：",
        "！",
        "？",
    ]

    # ------------------------------------
    # 【○○】を分離
    # ------------------------------------

    prefix_match = re.match(
        r"^(【[^】]+】)\s*(.*)$",
        title,
    )

    prefix = None
    body = title

    if prefix_match:
        prefix = prefix_match.group(1).strip()
        body = prefix_match.group(2).strip()

    # ------------------------------------
    # 英数字単語の途中で分割しないための判定
    # ------------------------------------

    def is_ascii_alnum(char):
        return bool(
            re.match(
                r"[A-Za-z0-9]",
                char,
            )
        )

    def is_inside_ascii_word(index, text):
        """
        indexの位置で分割すると
        ASCII英数字の単語途中になる場合True。
        """

        if index <= 0 or index >= len(text):
            return False

        left = text[index - 1]
        right = text[index]

        return (
            is_ascii_alnum(left)
            and is_ascii_alnum(right)
        )

    # ------------------------------------
    # 分割候補として適切か
    # ------------------------------------

    def is_valid_boundary(index, text):
        if index <= 0 or index >= len(text):
            return False

        # 英数字単語の途中は禁止
        if is_inside_ascii_word(index, text):
            return False

        left = text[:index].strip()
        right = text[index:].strip()

        if not left or not right:
            return False

        # 次の行が助詞から始まる場合は禁止
        if any(
            right.startswith(particle)
            for particle in particles
        ):
            return False

        # 1行目が助詞だけで終わる場合は禁止
        if left[-1:] in particles:
            return False

        return True

    # ------------------------------------
    # 分割位置の評価
    # ------------------------------------

    def boundary_score(
        left,
        right,
        left_width,
        right_width,
    ):
        score = 0

        # 幅のバランス
        score += abs(
            left_width - right_width
        )

        # 助詞の直後
        for particle in particles:
            if left.endswith(particle):
                score -= 350
                break

        # 記号の直後
        if left.endswith(
            tuple(punctuation_marks)
        ):
            score -= 500

        # 意味のまとまり
        for mark in semantic_marks:
            if left.endswith(mark):
                score -= 300
                break

        # 文章途中での不自然な分割を軽く減点
        if right.startswith(
            (
                "そして",
                "また",
                "さらに",
                "そのため",
                "つまり",
            )
        ):
            score += 150

        return score

    # ------------------------------------
    # 2〜4行の候補を作る
    # ------------------------------------

    def make_candidates(
        text,
        line_count,
    ):
        """
        指定行数で分割可能な候補を作る。
        """

        candidates = []

        if not text:
            return candidates

        length = len(text)

        # --------------------------------
        # 2行
        # --------------------------------

        if line_count == 2:

            for i in range(1, length):

                if not is_valid_boundary(
                    i,
                    text,
                ):
                    continue

                line1 = text[:i].strip()
                line2 = text[i:].strip()

                width1 = measure_line(
                    draw,
                    [(line1, False)],
                    font,
                    letter_spacing,
                )

                width2 = measure_line(
                    draw,
                    [(line2, False)],
                    font,
                    letter_spacing,
                )

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

        # --------------------------------
        # 3行
        # --------------------------------

        elif line_count == 3:

            for i in range(1, length - 1):

                if not is_valid_boundary(
                    i,
                    text,
                ):
                    continue

                line1 = text[:i].strip()

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
                    length,
                ):

                    if not is_valid_boundary(
                        j,
                        text,
                    ):
                        continue

                    line2 = text[i:j].strip()
                    line3 = text[j:].strip()

                    if not line2 or not line3:
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

                    # 1行目・2行目の意味のまとまり
                    for mark in semantic_marks:

                        if line1.endswith(mark):
                            score -= 300

                        if line2.endswith(mark):
                            score -= 300

                    # 記号の直後
                    if line1.endswith(
                        tuple(punctuation_marks)
                    ):
                        score -= 400

                    if line2.endswith(
                        tuple(punctuation_marks)
                    ):
                        score -= 400

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

        # --------------------------------
        # 4行
        # --------------------------------

        elif line_count == 4:

            for i in range(1, length - 2):

                if not is_valid_boundary(
                    i,
                    text,
                ):
                    continue

                line1 = text[:i].strip()

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
                    length - 1,
                ):

                    if not is_valid_boundary(
                        j,
                        text,
                    ):
                        continue

                    line2 = text[i:j].strip()

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

                        # 意味のまとまり
                        lines = [
                            line1,
                            line2,
                            line3,
                        ]

                        for line in lines:

                            for mark in semantic_marks:

                                if line.endswith(mark):
                                    score -= 250
                                    break

                        # 記号の直後
                        for line in lines:

                            if line.endswith(
                                tuple(
                                    punctuation_marks
                                )
                            ):
                                score -= 300

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

    # ------------------------------------
    # 1行で収まる場合
    # ------------------------------------

    if (
        not prefix
        and
        measure_line(
            draw,
            [(title, False)],
            font,
            letter_spacing,
        ) <= max_width
    ):
        return [title]

    # ------------------------------------
    # 【○○】なし
    # ------------------------------------

    if not prefix:

        # 2行 → 3行 → 4行
        for line_count in [2, 3, 4]:

            candidates = make_candidates(
                body,
                line_count,
            )

            if candidates:

                candidates.sort(
                    key=lambda x: x[0]
                )

                return candidates[0][1]

    # ------------------------------------
    # 【○○】あり
    # ------------------------------------

    else:

        # prefix自体が幅を超える場合は
        # 現在のフォントサイズでは収まらない
        prefix_width = measure_line(
            draw,
            [(prefix, False)],
            font,
            letter_spacing,
        )

        if prefix_width <= max_width:

            # 本文が空ならprefixだけ
            if not body:
                return [prefix]

            # 本文1行で収まる場合
            body_width = measure_line(
                draw,
                [(body, False)],
                font,
                letter_spacing,
            )

            if body_width <= max_width:
                return [
                    prefix,
                    body,
                ]

            # 本文2行 → 3行
            for line_count in [2, 3]:

                candidates = make_candidates(
                    body,
                    line_count,
                )

                if candidates:

                    candidates.sort(
                        key=lambda x: x[0]
                    )

                    return [
                        prefix,
                        *candidates[0][1],
                    ]

    # ------------------------------------
    # 最終手段
    # ------------------------------------

    # 英数字の途中で切らない単純分割
    target_lines = 4

    if prefix:
        remaining_lines = 3
        text = body
    else:
        remaining_lines = target_lines
        text = title

    if not text:
        return [prefix] if prefix else [title]

    result = []

    remaining_text = text

    for line_number in range(
        remaining_lines - 1
    ):

        if not remaining_text:
            break

        target_length = (
            len(remaining_text)
            /
            (
                remaining_lines
                -
                line_number
            )
        )

        best_index = None
        best_distance = None

        for i in range(
            1,
            len(remaining_text),
        ):

            if not is_valid_boundary(
                i,
                remaining_text,
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
            remaining_text[
                :best_index
            ].strip()
        )

        remaining_text = (
            remaining_text[
                best_index:
            ].strip()
        )

    if remaining_text:
        result.append(
            remaining_text
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
