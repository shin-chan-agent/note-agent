from PIL import Image, ImageDraw, ImageFilter


# ========================================
# Ver.1 アイキャッチ背景設定
# ========================================

WIDTH = 1520
HEIGHT = 800


def create_eyecatch_background(
    output_path,
    category="AIチャット",
):
    """
    Ver.1のアイキャッチ背景を生成する。

    Args:
        output_path: 保存先
        category: 画像カテゴリ
    """

    # ------------------------------------
    # カテゴリ別の背景色
    # ------------------------------------

    category_colors = {
        "AIチャット": {
            "top": (238, 248, 255),
            "bottom": (195, 225, 250),
            "accent": (70, 170, 220),
        },

        "AI画像・デザイン": {
            "top": (240, 248, 255),
            "bottom": (205, 220, 250),
            "accent": (90, 160, 220),
        },

        "動画編集・ショート動画": {
            "top": (235, 248, 255),
            "bottom": (185, 225, 245),
            "accent": (50, 175, 220),
        },

        "AI副業・マネタイズ": {
            "top": (242, 249, 255),
            "bottom": (200, 225, 245),
            "accent": (70, 150, 210),
        },

        "AI自動化・業務効率化": {
            "top": (238, 250, 250),
            "bottom": (190, 230, 235),
            "accent": (50, 165, 185),
        },
    }

    colors = category_colors.get(
        category,
        category_colors["AIチャット"],
    )

    # ------------------------------------
    # ベース画像
    # ------------------------------------

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        colors["top"],
    )

    pixels = image.load()

    top = colors["top"]
    bottom = colors["bottom"]

    # ------------------------------------
    # 縦方向グラデーション
    # ------------------------------------

    for y in range(HEIGHT):
        ratio = y / (HEIGHT - 1)

        r = int(top[0] * (1 - ratio) + bottom[0] * ratio)
        g = int(top[1] * (1 - ratio) + bottom[1] * ratio)
        b = int(top[2] * (1 - ratio) + bottom[2] * ratio)

        for x in range(WIDTH):
            pixels[x, y] = (r, g, b)

    # ------------------------------------
    # ガラス風タイトル保護エリア
    # ------------------------------------

    glass = Image.new(
        "RGBA",
        (WIDTH, HEIGHT),
        (0, 0, 0, 0),
    )

    glass_draw = ImageDraw.Draw(glass)

    ellipse_box = (
        170,
        145,
        WIDTH - 170,
        HEIGHT - 145,
    )

    # 外側の柔らかい光
    glow = Image.new(
        "RGBA",
        (WIDTH, HEIGHT),
        (0, 0, 0, 0),
    )

    glow_draw = ImageDraw.Draw(glow)

    glow_draw.ellipse(
        ellipse_box,
        fill=(*colors["accent"], 28),
    )

    glow = glow.filter(
        ImageFilter.GaussianBlur(35)
    )

    image = Image.alpha_composite(
        image.convert("RGBA"),
        glow,
    )

    # ------------------------------------
    # ガラスパネル
    # ------------------------------------

    glass_draw.ellipse(
        ellipse_box,
        fill=(255, 255, 255, 42),
        outline=(255, 255, 255, 90),
        width=2,
    )

    # ------------------------------------
    # 内側の光
    # ------------------------------------

    inner_box = (
        ellipse_box[0] + 15,
        ellipse_box[1] + 15,
        ellipse_box[2] - 15,
        ellipse_box[3] - 15,
    )

    glass_draw.ellipse(
        inner_box,
        outline=(*colors["accent"], 30),
        width=2,
    )

    image = Image.alpha_composite(
        image,
        glass,
    )

    # ------------------------------------
    # 抽象的な光のライン
    # ------------------------------------

    lines = Image.new(
        "RGBA",
        (WIDTH, HEIGHT),
        (0, 0, 0, 0),
    )

    line_draw = ImageDraw.Draw(lines)

    accent = colors["accent"]

    line_draw.arc(
        (-250, 120, 650, 900),
        205,
        325,
        fill=(*accent, 45),
        width=3,
    )

    line_draw.arc(
        (950, -150, 1750, 650),
        20,
        140,
        fill=(*accent, 35),
        width=3,
    )

    lines = lines.filter(
        ImageFilter.GaussianBlur(1)
    )

    image = Image.alpha_composite(
        image,
        lines,
    )

    # ------------------------------------
    # 保存
    # ------------------------------------

    image.convert("RGB").save(
        output_path,
        quality=95,
    )