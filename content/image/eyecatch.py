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
    タイトルを意味のまとまりを優先して
    2〜3行に分割する。

    優先順位：
    1. 1行
    2. 意味の良い2行
    3. 意味の良い3行
    4. 文字数ベースの2〜3行
    """

    title = title.strip()

    letter_spacing = font.size * 0.015

    # =========================
    # 1行で収まる場合
    # =========================

    if measure_line(
        draw,
        [(title, False)],
        font,
        letter_spacing,
    ) <= max_width:
        return [title]

    # =========================
    # 改行候補
    # =========================

    break_positions = []

    # 強い区切り
    priority_marks = [
        "！",
        "？",
        "。",
        "!",
        "?",
    ]

    # 意味のまとまりとして使いやすい区切り
    semantic_marks = [
        "収益化",
        "効率化",
        "ロードマップ",
        "チェックリスト",
        "初心者向け",
        "副業",
        "成功",
        "活用",
        "方法",
        "コツ",
        "比較",
        "まとめ",
    ]

    # -------------------------
    # 強い区切り
    # -------------------------

    for mark in priority_marks:

        start = 0

        while True:

            index = title.find(
                mark,
                start,
            )

            if index == -1:
                break

            split_at = index + len(mark)

            if 0 < split_at < len(title):
                break_positions.append(
                    (
                        split_at,
                        3,
                    )
                )

            start = split_at

    # -------------------------
    # 意味区切り
    # -------------------------

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

            if 0 < split_at < len(title):
                break_positions.append(
                    (
                        split_at,
                        2,
                    )
                )

            start = split_at

    # 重複除去
    break_positions = list(
        {
            position: priority
            for position, priority
            in break_positions
        }.items()
    )

    # =========================
    # 2行候補を作る
    # =========================

    candidates_2 = []

    for split_at, priority in break_positions:

        left = title[:split_at].strip()
        right = title[split_at:].strip()

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
            left_width <= max_width
            and right_width <= max_width
        ):

            max_line_width = max(
                left_width,
                right_width,
            )

            balance = abs(
                left_width - right_width
            )

            candidates_2.append(
                (
                    priority,
                    max_line_width,
                    balance,
                    [
                        left,
                        right,
                    ],
                )
            )

    # 2行で収まるなら採用
    if candidates_2:

        candidates_2.sort(
            key=lambda x: (
                -x[0],
                x[1],
                x[2],
            )
        )

        return candidates_2[0][3]

    # =========================
    # 3行候補を作る
    # =========================

    candidates_3 = []

    positions = [
        position
        for position, _ in break_positions
    ]

    for first in positions:

        for second in positions:

            if second <= first:
                continue

            line1 = title[:first].strip()
            line2 = title[first:second].strip()
            line3 = title[second:].strip()

            if not line1 or not line2 or not line3:
                continue

            widths = [
                measure_line(
                    draw,
                    [(line1, False)],
                    font,
                    letter_spacing,
                ),
                measure_line(
                    draw,
                    [(line2, False)],
                    font,
                    letter_spacing,
                ),
                measure_line(
                    draw,
                    [(line3, False)],
                    font,
                    letter_spacing,
                ),
            ]

            # 3行すべてがパネル内に収まる
            if max(widths) <= max_width:

                max_line_width = max(widths)

                min_line_width = min(widths)

                balance = (
                    max_line_width
                    - min_line_width
                )

                # 3行とも極端に短くならないようにする
                if min_line_width < max_width * 0.25:
                    balance += max_width

                priority_score = 0

                # 強い区切りを高評価
                for position, priority in break_positions:

                    if position == first:
                        priority_score += priority * 2

                    if position == second:
                        priority_score += priority * 2

                candidates_3.append(
                    (
                        priority_score,
                        max_line_width,
                        balance,
                        [
                            line1,
                            line2,
                            line3,
                        ],
                    )
                )

    # 3行の意味分割が見つかった場合
    if candidates_3:

        candidates_3.sort(
            key=lambda x: (
                -x[0],
                x[1],
                x[2],
            )
        )

        return candidates_3[0][3]

    # =========================
    # 最後の手段
    # 文字数ベース
    # =========================

    length = len(title)

    # まず2行を試す
    for ratio in [
        0.4,
        0.45,
        0.5,
        0.55,
        0.6,
    ]:

        split_at = int(
            length * ratio
        )

        left = title[:split_at].strip()
        right = title[split_at:].strip()

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
            left_width <= max_width
            and right_width <= max_width
        ):
            return [
                left,
                right,
            ]

    # 最終手段：3行
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
