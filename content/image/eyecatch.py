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
    日本語として自然な位置を優先して
    タイトルを2〜3行に分割する。

    優先順位
    1. 1行で収まる
    2. 助詞の直後
    3. 記号の直後
    4. 意味のまとまり
    5. 文字数バランス

    助詞が次の行の先頭に来る分割は避ける。
    """

    title = title.strip()

    letter_spacing = font.size * 0.015

    # ------------------------------------
    # 1行で収まる場合
    # ------------------------------------

    if measure_line(
        draw,
        [(title, False)],
        font,
        letter_spacing,
    ) <= max_width:
        return [title]

    # ------------------------------------
    # 助詞
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

    # ------------------------------------
    # 意味のまとまり
    # ------------------------------------

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
    ]

    # ------------------------------------
    # 改行候補を作る
    # ------------------------------------

    candidates = []

    for index in range(1, len(title)):

        left = title[:index]
        right = title[index:]

        left = left.strip()
        right = right.strip()

        if not left or not right:
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

        # --------------------------------
        # 次の行が助詞から始まる場合
        # 強く減点
        # --------------------------------

        starts_with_particle = any(
            right.startswith(particle)
            for particle in particles
        )

        if starts_with_particle:
            continue

        # --------------------------------
        # 分割位置の評価
        # --------------------------------

        score = 0

        # 左右の長さを近づける
        score += abs(
            left_width - right_width
        )

        # 助詞の直後を高評価
        for particle in particles:
            if left.endswith(particle):
                score -= 300
                break

        # --------------------------------
        # 記号の直後を高評価
        # --------------------------------

        if left[-1:] in [
            "！",
            "？",
            "。",
            "！",
            "？",
            "、",
            "：",
        ]:
            score -= 500


        for mark in semantic_marks:
            if left.endswith(mark):
                score -= 200
                break

        candidates.append(
            (
                score,
                left,
                right,
            )
        )

    # ------------------------------------
    # 2行にできる場合
    # ------------------------------------

    if candidates:

        candidates.sort(
            key=lambda x: x[0]
        )

        _, left, right = candidates[0]

        return [
            left,
            right,
        ]

    # ------------------------------------
    # 3行に分割
    # ------------------------------------

    best = None

    for i in range(1, len(title) - 1):

        line1 = title[:i].strip()

        if not line1:
            continue

        # 1行目が助詞で終わる場合は避ける
        if line1[-1:] in particles:
            continue

        width1 = measure_line(
            draw,
            [(line1, False)],
            font,
            letter_spacing,
        )

        if width1 > max_width:
            continue

        for j in range(i + 1, len(title)):

            line2 = title[i:j].strip()
            line3 = title[j:].strip()

            if not line2 or not line3:
                continue

            # 2行目・3行目が助詞から始まる場合は除外
            if any(
                line2.startswith(p)
                for p in particles
            ):
                continue

            if any(
                line3.startswith(p)
                for p in particles
            ):
                continue

            # 2行目が助詞で終わる場合も避ける
            if line2[-1:] in particles:
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

            # --------------------------------
            # 3行の長さをできるだけ均等に
            # --------------------------------

            max_line = max(
                width1,
                width2,
                width3,
            )

            min_line = min(
                width1,
                width2,
                width3,
            )

            score = max_line - min_line

            # 助詞の直後を優先
            if line1[-1:] in particles:
                score -= 300

            if line2[-1:] in particles:
                score -= 300

            # 記号の直後を優先
            if line1[-1:] in [
                "！",
                "？",
                "。",
                "、",
            ]:
                score -= 400

            if line2[-1:] in [
                "！",
                "？",
                "。",
                "、",
            ]:
                score -= 400

            # 意味のまとまりを優先
            for mark in semantic_marks:
                if line1.endswith(mark):
                    score -= 150

                if line2.endswith(mark):
                    score -= 150

            if best is None or score < best[0]:
                best = (
                    score,
                    line1,
                    line2,
                    line3,
                )

    if best:
        return [
            best[1],
            best[2],
            best[3],
        ]

    # ------------------------------------
    # 最終手段（文字数で分割）
    # ------------------------------------

    third = len(title) // 3

    return [
        title[:third].strip(),
        title[third:third * 2].strip(),
        title[third * 2:].strip(),
    ]


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
