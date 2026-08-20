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
    MIN_FONT_SIZE = 50

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
    日本語タイトルを自然な意味のまとまりで分割する。

    方針：
    1. 【○○】は独立行として扱う
    2. 絶対に切ってはいけない位置を除外する
    3. 2行 → 3行 → 4行の順に候補を作る
    4. 意味のまとまりを最優先する
    5. 行幅のバランスは補助的に評価する
    """

    import re

    title = title.strip()

    letter_spacing = font.size * 0.015

    # ==================================================
    # 1. 基本設定
    # ==================================================

    PARTICLES = [
        "が",
        "は",
        "の",
        "を",
        "に",
        "へ",
        "と",
        "も",
        "や",
        "で",
    ]

    FORBIDDEN_LINE_START = (
        "！",
        "？",
        "。",
        "、",
        "：",
        ":",
        "；",
        ";",
        "）",
        ")",
        "」",
        "』",
        "】",
        "］",
        "]",
        "〉",
        "》",
        "〕",
        "・",
    )

    # ==================================================
    # 2. 分割したくない語・フレーズ
    # ==================================================

    PROTECTED_PHRASES = [
        # AI・動画
        "ショート動画",
        "AIショート動画",
        "動画副業",
        "AI副業",
        "AI活用",
        "AIチャット",
        "AI画像",
        "AIデザイン",
        "AI自動化",
        "動画編集",
        "動画制作",

        # マネタイズ
        "収益化",
        "収益化術",
        "時短術",
        "時短テクニック",
        "効率化",
        "自動化",

        # 解説系
        "実践ガイド",
        "完全ガイド",
        "初心者向け",
        "徹底解説",
        "成功戦略",
        "チェックリスト",

        # 比較系
        "メリット・デメリット",
        "機能比較",
        "料金比較",
        "無料版",
        "有料版",

        # その他
        "ロードマップ",
        "活用方法",
        "使い方",
        "始め方",
    ]

    # ==================================================
    # 3. さらに「意味のまとまり」として扱う表現
    # ==================================================

    # 助詞＋語句を途中で切らないためのパターン
    PROTECTED_PATTERNS = [
        r"[^、。！？]{1,12}から",
        r"[^、。！？]{1,12}まで",
        r"[^、。！？]{1,12}より",
        r"[^、。！？]{1,12}だけ",
        r"[^、。！？]{1,12}ほど",
        r"[^、。！？]{1,12}しか",
        r"[^、。！？]{1,12}こそ",
        r"[^、。！？]{1,12}など",
    ]

    # ==================================================
    # 4. 文字幅
    # ==================================================

    def get_width(text):
        return measure_line(
            draw,
            [(text, False)],
            font,
            letter_spacing,
        )

    # ==================================================
    # 5. ASCII英数字の途中判定
    # ==================================================

    def is_ascii_alnum(char):
        return bool(
            re.fullmatch(
                r"[A-Za-z0-9]",
                char,
            )
        )

    def is_inside_ascii_word(index, text):
        if index <= 0 or index >= len(text):
            return False

        return (
            is_ascii_alnum(text[index - 1])
            and
            is_ascii_alnum(text[index])
        )

    # ==================================================
    # 6. 保護フレーズの途中判定
    # ==================================================

    def is_inside_protected_phrase(
        index,
        text,
    ):
        for phrase in PROTECTED_PHRASES:

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

    # ==================================================
    # 7. 「から」「まで」などの途中判定
    # ==================================================

    def is_inside_protected_pattern(
        index,
        text,
    ):
        for pattern in PROTECTED_PATTERNS:

            for match in re.finditer(
                pattern,
                text,
            ):

                if (
                    match.start()
                    <
                    index
                    <
                    match.end()
                ):
                    return True

        return False

    # ==================================================
    # 8. 絶対に切ってはいけない位置
    # ==================================================

    def is_forbidden_boundary(
        index,
        text,
    ):
        if index <= 0 or index >= len(text):
            return True

        left = text[index - 1]
        right = text[index]

        # ----------------------------------------------
        # 英数字の途中
        # ----------------------------------------------

        if is_inside_ascii_word(
            index,
            text,
        ):
            return True

        # ----------------------------------------------
        # 保護フレーズの途中
        # ----------------------------------------------

        if is_inside_protected_phrase(
            index,
            text,
        ):
            return True

        # ----------------------------------------------
        # 「から」「まで」などのまとまり途中
        # ----------------------------------------------

        if is_inside_protected_pattern(
            index,
            text,
        ):
            return True

        # ----------------------------------------------
        # 次の行が記号から始まる
        # ----------------------------------------------

        if right in FORBIDDEN_LINE_START:
            return True

        # ----------------------------------------------
        # 助詞を次の行に送る
        # ----------------------------------------------

        if right in PARTICLES:
            return True

        # ----------------------------------------------
        # 括弧の中を分断する
        # ----------------------------------------------

        left_count = text[:index].count("「")
        right_count = text[:index].count("」")

        if left_count > right_count:
            return True

        left_count = text[:index].count("『")
        right_count = text[:index].count("』")

        if left_count > right_count:
            return True

        return False

    # ==================================================
    # 9. 分割候補位置を作る
    # ==================================================

    def get_valid_boundaries(text):

        boundaries = []

        for index in range(
            1,
            len(text),
        ):

            if is_forbidden_boundary(
                index,
                text,
            ):
                continue

            left = text[:index].strip()
            right = text[index:].strip()

            if not left or not right:
                continue

            boundaries.append(index)

        return boundaries

    # ==================================================
    # 10. 改行位置の自然さ
    # ==================================================

    def boundary_score(
        index,
        text,
    ):
        left = text[:index].strip()
        right = text[index:].strip()

        score = 0

        # ----------------------------------------------
        # 強い区切り
        # ----------------------------------------------

        if left.endswith(
            (
                "！",
                "？",
                "。",
                "：",
                ":",
            )
        ):
            score -= 2000

        # ----------------------------------------------
        # 助詞の直後
        # ----------------------------------------------

        for particle in PARTICLES:

            if left.endswith(
                particle
            ):
                score -= 700
                break

        # ----------------------------------------------
        # 意味のまとまり直後
        # ----------------------------------------------

        for phrase in PROTECTED_PHRASES:

            if left.endswith(
                phrase
            ):
                score -= 900
                break

        # ----------------------------------------------
        # 「から」「まで」などの直後
        # ----------------------------------------------

        for suffix in [
            "から",
            "まで",
            "より",
            "だけ",
            "ほど",
            "しか",
            "こそ",
            "など",
        ]:

            if left.endswith(
                suffix
            ):
                score -= 600
                break

        # ----------------------------------------------
        # 行頭が不自然な接続語
        # ----------------------------------------------

        for word in [
            "ので",
            "ため",
            "から",
            "まで",
            "より",
            "だけ",
            "ほど",
            "しか",
            "こそ",
            "など",
        ]:

            if right.startswith(word):
                score += 1500

        return score

    # ==================================================
    # 11. 候補全体の評価
    # ==================================================

    def evaluate_lines(lines):

        widths = [
            get_width(line)
            for line in lines
        ]

        # 幅オーバーは失格
        if any(
            width > max_width
            for width in widths
        ):
            return None

        score = 0

        # ----------------------------------------------
        # 各行の改行位置を評価
        # ----------------------------------------------

        position = 0

        for line in lines[:-1]:

            position += len(line)

            score += boundary_score(
                position,
                "".join(lines),
            )

        # ----------------------------------------------
        # 行数
        # ----------------------------------------------

        if len(lines) == 2:
            score -= 500

        elif len(lines) == 3:
            score -= 300

        elif len(lines) == 4:
            score += 2000

        # ----------------------------------------------
        # 極端に短い行を避ける
        # ----------------------------------------------

        max_width_value = max(
            widths
        )

        min_width_value = min(
            widths
        )

        if (
            min_width_value
            <
            max_width_value * 0.35
        ):
            score += 1000

        # ----------------------------------------------
        # 行幅の差
        #
        # ここは「補助評価」にする
        # ----------------------------------------------

        score += (
            max_width_value
            -
            min_width_value
        ) * 0.10

        return score

    # ==================================================
    # 12. 2〜4行候補を総当たり
    # ==================================================

    def generate_candidates(
        text,
        line_count,
    ):

        boundaries = (
            get_valid_boundaries(text)
        )

        candidates = []

        if line_count == 2:

            for i in boundaries:

                lines = [
                    text[:i].strip(),
                    text[i:].strip(),
                ]

                score = evaluate_lines(
                    lines
                )

                if score is not None:
                    candidates.append(
                        (
                            score,
                            lines,
                        )
                    )

        elif line_count == 3:

            for i in boundaries:

                for j in boundaries:

                    if j <= i:
                        continue

                    lines = [
                        text[:i].strip(),
                        text[i:j].strip(),
                        text[j:].strip(),
                    ]

                    if any(
                        not line
                        for line in lines
                    ):
                        continue

                    score = evaluate_lines(
                        lines
                    )

                    if score is not None:
                        candidates.append(
                            (
                                score,
                                lines,
                            )
                        )

        elif line_count == 4:

            for i in boundaries:

                for j in boundaries:

                    if j <= i:
                        continue

                    for k in boundaries:

                        if k <= j:
                            continue

                        lines = [
                            text[:i].strip(),
                            text[i:j].strip(),
                            text[j:k].strip(),
                            text[k:].strip(),
                        ]

                        if any(
                            not line
                            for line in lines
                        ):
                            continue

                        score = evaluate_lines(
                            lines
                        )

                        if score is not None:
                            candidates.append(
                                (
                                    score,
                                    lines,
                                )
                            )

        return candidates

    # ==================================================
    # 13. 【○○】を分離
    # ==================================================

    prefix_match = re.match(
        r"^(【[^】]+】)\s*(.*)$",
        title,
    )

    if prefix_match:

        prefix = (
            prefix_match
            .group(1)
            .strip()
        )

        body = (
            prefix_match
            .group(2)
            .strip()
        )

        # 【○○】だけならそのまま
        if not body:
            return [prefix]

        # 本文1行
        if (
            get_width(body)
            <= max_width
        ):
            return [
                prefix,
                body,
            ]

    else:

        prefix = None
        body = title

        # 1行で収まる
        if (
            get_width(body)
            <= max_width
        ):
            return [body]

    # ==================================================
    # 14. 2行 → 3行 → 4行
    # ==================================================

    max_lines = (
        4
        if allow_four_lines
        else 3
    )

    for line_count in range(
        2,
        max_lines + 1,
    ):

        candidates = (
            generate_candidates(
                body,
                line_count,
            )
        )

        if not candidates:
            continue

        candidates.sort(
            key=lambda item: item[0]
        )

        best_lines = (
            candidates[0][1]
        )

        if prefix:
            return [
                prefix,
                *best_lines,
            ]

        return best_lines

    # ==================================================
    # 15. 最終手段
    # ==================================================

    # ここまで来た場合は、
    # 自然な分割位置だけでは収まらない。
    #
    # それでも禁止位置では切らない。

    boundaries = (
        get_valid_boundaries(body)
    )

    if not boundaries:
        return (
            [prefix, body]
            if prefix
            else [body]
        )

    target_lines = (
        4
        if allow_four_lines
        else 3
    )

    result = []

    remaining = body

    for line_number in range(
        target_lines - 1
    ):

        remaining_lines = (
            target_lines
            -
            line_number
        )

        target_length = (
            len(remaining)
            /
            remaining_lines
        )

        best_index = None
        best_distance = None

        current_boundaries = (
            get_valid_boundaries(
                remaining
            )
        )

        for index in current_boundaries:

            distance = abs(
                index
                -
                target_length
            )

            if (
                best_distance is None
                or distance < best_distance
            ):
                best_distance = distance
                best_index = index

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
