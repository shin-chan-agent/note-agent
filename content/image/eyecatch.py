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

    BASE_FONT_SIZE = 72
    MIN_FONT_SIZE = 58

    letter_spacing_ratio = 0.015
    line_spacing_ratio = 0.15

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
    タイトルを意味のまとまりを優先して
    2〜3行に分割する。
    """

    title = title.strip()

    # =========================
    # まず1行で収まるか確認
    # =========================

    if measure_line(
        draw,
        [(title, False)],
        font,
        font.size * 0.015,
    ) <= max_width:

        return [title]

    # =========================
    # 2行候補を作る
    # =========================

    candidates = []

    # 優先する改行位置
    break_marks = [
        "！",
        "？",
        "。",
        "：",
        "！",
        "?",
        "!",
        "：",
    ]

    for mark in break_marks:

        start = 0

        while True:

            index = title.find(
                mark,
                start,
            )

            if index == -1:
                break

            split_at = index + 1

            left = title[:split_at].strip()
            right = title[split_at:].strip()

            if left and right:
                candidates.append(
                    (left, right)
                )

            start = split_at

    # =========================
    # 「〜向け」「〜活用」などの
    # 意味の区切りも候補にする
    # =========================

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
    ]

    for mark in semantic_marks:

        start = 0

        while True:

            index = title.find(
                mark,
                start,
            )

            if index == -1:
                break

            split_at = index + len(mark)

            left = title[:split_at].strip()
            right = title[split_at:].strip()

            if left and right:
                candidates.append(
                    (left, right)
                )

            start = split_at

    # =========================
    # 文字数による候補も追加
    # =========================

    length = len(title)

    for ratio in [0.45, 0.5, 0.55]:

        split_at = int(length * ratio)

        left = title[:split_at].strip()
        right = title[split_at:].strip()

        if left and right:
            candidates.append(
                (left, right)
            )

    # =========================
    # 2行候補から最適なものを選ぶ
    # =========================

    valid_candidates = []

    for left, right in candidates:

        left_width = measure_line(
            draw,
            [(left, False)],
            font,
            font.size * 0.015,
        )

        right_width = measure_line(
            draw,
            [(right, False)],
            font,
            font.size * 0.015,
        )

        if (
            left_width <= max_width
            and right_width <= max_width
        ):

            # 行幅の差が小さいほど高評価
            balance = abs(
                left_width - right_width
            )

            # 極端に短い行を避ける
            min_length = min(
                len(left),
                len(right),
            )

            if min_length >= 4:
                valid_candidates.append(
                    (
                        balance,
                        left,
                        right,
                    )
                )

    if valid_candidates:

        valid_candidates.sort(
            key=lambda x: x[0]
        )

        _, left, right = (
            valid_candidates[0]
        )

        return [left, right]

    # =========================
    # 2行にできない場合は3行
    # =========================

    third_candidates = []

    for first_ratio in [0.30, 0.33, 0.36]:

        first_end = int(
            length * first_ratio
        )

        first = title[:first_end].strip()

        remaining = title[first_end:].strip()

        if len(remaining) < 4:
            continue

        for second_ratio in [0.45, 0.5, 0.55]:

            second_length = int(
                len(remaining)
                * second_ratio
            )

            second_end = second_length

            second = (
                remaining[:second_end]
                .strip()
            )

            third = (
                remaining[second_end:]
                .strip()
            )

            if not second or not third:
                continue

            widths = [
                measure_line(
                    draw,
                    [(line, False)],
                    font,
                    font.size * 0.015,
                )
                for line in [
                    first,
                    second,
                    third,
                ]
            ]

            if max(widths) <= max_width:

                balance = (
                    max(widths)
                    - min(widths)
                )

                third_candidates.append(
                    (
                        balance,
                        [
                            first,
                            second,
                            third,
                        ],
                    )
                )

    if third_candidates:

        third_candidates.sort(
            key=lambda x: x[0]
        )

        return third_candidates[0][1]

    # 最終手段
    third = len(title) // 3

    return [
        title[:third],
        title[third:third * 2],
        title[third * 2:],
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


if __name__ == "__main__":

    create_eyecatch(
        background_path="content/image/backgrounds/default.png",
        output_path="test_eyecatch.png",
        title="ChatGPTで業務効率化！初心者向け5選",
        highlight_keywords=[
            "ChatGPT",
            "5選",
        ],
    )