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

    BASE_FONT_SIZE = 86
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
):
    """
    日本語として自然な意味のまとまりを優先して
    タイトルを2〜3行に分割する。

    優先順位
    1. 【】部分を独立
    2. 記号の直後
    3. 文節・意味のまとまり
    4. 複合語を壊さない
    5. 2〜3行のバランス
    """

    title = title.strip()

    letter_spacing = font.size * 0.015

    # =====================================================
    # 1. 1行で収まる場合
    # =====================================================

    if measure_line(
        draw,
        [(title, False)],
        font,
        letter_spacing,
    ) <= max_width:
        return [title]

    # =====================================================
    # 2. 【】部分を先頭行として独立
    # =====================================================

    bracket_match = re.match(
        r"^(【[^】]+】)(.*)$",
        title,
    )

    if bracket_match:

        prefix = bracket_match.group(1).strip()
        remaining = bracket_match.group(2).strip()

        if remaining:

            # 残りを2行以内に分割
            remaining_lines = _split_title_body(
                remaining,
                font,
                draw,
                max_width,
            )

            if len(remaining_lines) <= 2:
                return [prefix] + remaining_lines

    # =====================================================
    # 3. 通常タイトル
    # =====================================================

    return _split_title_body(
        title,
        font,
        draw,
        max_width,
    )


def _split_title_body(
    title,
    font,
    draw,
    max_width,
):
    """
    タイトル本文を2〜3行に分割する。
    意味のまとまりを最優先する。
    """

    letter_spacing = font.size * 0.015

    # =====================================================
    # 改行禁止パターン
    # =====================================================

    forbidden_before = [
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

        # 接続語
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

    # =====================================================
    # 改行候補を作成
    # =====================================================

    candidates = []

    for index in range(1, len(title)):

        left = title[:index].strip()
        right = title[index:].strip()

        if not left or not right:
            continue

        # -------------------------------------------------
        # 文字幅
        # -------------------------------------------------

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

        # =================================================
        # 改行禁止位置
        # =================================================

        forbidden = False

        for word in forbidden_before:
            if right.startswith(word):
                forbidden = True
                break

        if forbidden:
            continue

        # =================================================
        # スコア
        # =================================================

        score = 0

        # -------------------------------------------------
        # 基本：左右の幅を近づける
        # -------------------------------------------------

        score += abs(
            left_width - right_width
        )

        # -------------------------------------------------
        # 記号の直後を強く優先
        # -------------------------------------------------

        if left[-1:] in [
            "！",
            "？",
            "：",
            "。",
            "、",
            "｜",
        ]:
            score -= 1200

        # -------------------------------------------------
        # 助詞の直後を優先
        # -------------------------------------------------

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
        ]

        if left[-1:] in particles:
            score -= 500

        # -------------------------------------------------
        # 意味のまとまり
        # -------------------------------------------------

        semantic_marks = [
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
        ]

        for mark in semantic_marks:

            if left.endswith(mark):
                score -= 700

        # =================================================
        # 複合語の途中を避ける
        # =================================================

        compound_patterns = [
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
        ]

        for word in compound_patterns:

            start = index - len(word)

            if start >= 0:

                segment = title[start:index]

                if segment and word.startswith(segment):
                    score += 2000

        # =================================================
        # 候補保存
        # =================================================

        candidates.append(
            (
                score,
                left,
                right,
            )
        )

    # =====================================================
    # 2行候補
    # =====================================================

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
    # 3行分割
    # =====================================================

    best = None

    for i in range(1, len(title) - 1):

        line1 = title[:i].strip()

        if not line1:
            continue

        # -------------------------------------------------
        # 1行目の幅
        # -------------------------------------------------

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

            # -------------------------------------------------
            # 各行の幅
            # -------------------------------------------------

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

            # -------------------------------------------------
            # 助詞・記号などから始まる行を禁止
            # -------------------------------------------------

            if any(
                line2.startswith(word)
                for word in forbidden_before
            ):
                continue

            if any(
                line3.startswith(word)
                for word in forbidden_before
            ):
                continue

            # -------------------------------------------------
            # 行末が不自然な場合
            # -------------------------------------------------

            if line1[-1:] in [
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
            ]:
                continue

            if line2[-1:] in [
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
            ]:
                continue

            # =================================================
            # スコア
            # =================================================

            max_width_value = max(
                width1,
                width2,
                width3,
            )

            min_width_value = min(
                width1,
                width2,
                width3,
            )

            score = (
                max_width_value
                - min_width_value
            )

            # -------------------------------------------------
            # 記号直後
            # -------------------------------------------------

            if line1[-1:] in [
                "！",
                "？",
                "：",
                "。",
                "、",
                "｜",
            ]:
                score -= 1200

            if line2[-1:] in [
                "！",
                "？",
                "：",
                "。",
                "、",
                "｜",
            ]:
                score -= 1200

            # -------------------------------------------------
            # 意味のまとまり
            # -------------------------------------------------

            for mark in semantic_marks:

                if line1.endswith(mark):
                    score -= 700

                if line2.endswith(mark):
                    score -= 700

            # -------------------------------------------------
            # 複合語分断チェック
            # -------------------------------------------------

            for word in compound_patterns:

                # line1の末尾が複合語の途中
                for k in range(1, len(word)):

                    if line1.endswith(word[:k]):
                        score += 2000

                # line2の末尾が複合語の途中
                for k in range(1, len(word)):

                    if line2.endswith(word[:k]):
                        score += 2000

            # -------------------------------------------------
            # 候補
            # -------------------------------------------------

            candidate = (
                score,
                line1,
                line2,
                line3,
            )

            if best is None or score < best[0]:
                best = candidate

    # =====================================================
    # 3行が見つかった場合
    # =====================================================

    if best:
        return [
            best[1],
            best[2],
            best[3],
        ]

    # =====================================================
    # 最終手段
    # =====================================================

    # それでも分割できない場合は、
    # できるだけ自然な位置を探す。

    middle = len(title) // 2

    candidates = []

    for offset in range(len(title)):

        for index in [
            middle - offset,
            middle + offset,
        ]:

            if index <= 0 or index >= len(title):
                continue

            left = title[:index].strip()
            right = title[index:].strip()

            if not left or not right:
                continue

            if any(
                right.startswith(word)
                for word in forbidden_before
            ):
                continue

            candidates.append(
                (
                    abs(index - middle),
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

    return [title]


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
