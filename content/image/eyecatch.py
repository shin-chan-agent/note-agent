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

    font_size = 64
    letter_spacing = font_size * 0.015
    line_spacing = int(font_size * 0.15)

    # 日本語対応フォント
    font_candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
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

    font = ImageFont.truetype(
        font_path,
        font_size,
    )

    # =========================
    # タイトル領域
    # =========================

    panel_left = int(width * 0.15)
    panel_right = int(width * 0.85)

    panel_top = int(height * 0.24)
    panel_bottom = int(height * 0.76)

    panel_width = panel_right - panel_left
    panel_height = panel_bottom - panel_top

    # =========================
    # タイトルを2〜3行にする
    # =========================

    lines = split_title(
        title,
        font,
        draw,
        panel_width,
    )

    # =========================
    # 強調キーワード
    # =========================

    parts_list = [
        split_highlights(
            line,
            highlight_keywords,
        )
        for line in lines
    ]

    # =========================
    # サイズ計算
    # =========================

    line_height = (
        draw.textbbox(
            (0, 0),
            "あ",
            font=font,
        )[3]
        -
        draw.textbbox(
            (0, 0),
            "あ",
            font=font,
        )[1]
    )

    line_widths = [
        measure_line(
            draw,
            parts,
            font,
            letter_spacing,
        )
        for parts in parts_list
    ]

    total_height = (
        line_height * len(lines)
        +
        line_spacing * (len(lines) - 1)
    )

    # タイトル全体をパネル中央へ
    start_y = (
        panel_top
        +
        (panel_height - total_height) / 2
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
    タイトルを2〜3行に分割する。
    """

    # 最初は手動で自然な位置を探す。
    # 後で自動最適化する。
    if len(title) <= 20:
        return [title]

    if len(title) <= 30:
        midpoint = len(title) // 2
        return [
            title[:midpoint],
            title[midpoint:],
        ]

    midpoint = len(title) // 3

    return [
        title[:midpoint],
        title[midpoint:midpoint * 2],
        title[midpoint * 2:],
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