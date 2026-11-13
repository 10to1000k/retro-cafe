"""Scene painters. Each returns an RGBA 1080x1920 frame for absolute time t."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from lib import (ACCENT, AMBER, BRAND_RED, CREAM, DARK, HERE, H, RED, W, band,
                 card, center, ease, ease_out, f_disp, f_fa, fa, fit, pdigits,
                 paste_soft, rule, still, text_w)
from logo import badge, lockup, mark

# ---------------------------------------------------------------- utilities

def scrim(img, top=0.0, bottom=1.0):
    band(img, 0, int(H * 0.34), (12, 8, 5), 0, int(235 * top))
    band(img, int(H * 0.50), H, (12, 8, 5), 0, int(250 * bottom))


def kicker(d, s, cx, y, size=42, fill=AMBER, alpha=255):
    f = fit(s, f_fa, 820, size)
    center(d, s, f, cx, y, fill + (alpha,))


def year_mark(img, year, cx=W / 2, cy=300, size=230, color=AMBER, weight="Bold"):
    """Persian-digit year in Vazirmatn (AlfaSlab has no Persian glyphs)."""
    d = ImageDraw.Draw(img, "RGBA")
    f = f_fa(size, weight)
    s = pdigits(year)
    w = text_w(d, s, f)
    d.text((cx - w / 2 + 6, cy + 9), s, font=f, fill=(0, 0, 0, 150))
    d.text((cx - w / 2, cy), s, font=f, fill=color + (255,))
    return d


def tile(fn, w, h, zoom=1.0, dy=0.0):
    src = Image.open(os.path.join(HERE, "img", fn)).convert("RGB")
    s = max(w / src.width, h / src.height) * zoom
    im = src.resize((int(src.width * s) + 2, int(src.height * s) + 2), Image.LANCZOS)
    x = (im.width - w) // 2
    y = int((im.height - h) // 2 + dy * (im.height - h) / 2)
    return im.crop((x, y, x + w, y + h))


# ---------------------------------------------------------------- scenes

def s_hook(t, a, b):
    u, dur = t - a, b - a
    img = still("hero_alfredo.png", ease(u / dur), zoom=0.13, dy=-0.15).convert("RGBA")
    scrim(img, 1.0, 1.0)
    d = ImageDraw.Draw(img, "RGBA")

    k = ease_out((u - 0.12) / 0.8)
    if k > 0:
        kicker(d, "کافه رترو تقدیم می‌کند", W / 2, int(H * 0.112), size=40,
               alpha=int(250 * k))

    p = ease_out((u - 0.28) / 1.0)
    ty = int(H * 0.168 + (1 - p) * 34)
    f = fit("پاستا آلفردو", f_fa, 760, 148)
    center(d, "پاستا آلفردو", f, W / 2, ty, CREAM + (int(255 * p),),
           shadow=(6, (0, 0, 0, int(175 * p))))
    if p > 0.35:
        rule(d, W / 2, ty + int(f.size * 1.36), 300, AMBER)
        kicker(d, "داستان واقعی‌اش از رم شروع می‌شود", W / 2,
               ty + int(f.size * 1.52), size=44)
    return img


def s_rome(t, a, b):
    u, dur = t - a, b - a
    img = still("rome1914.png", ease(u / dur), zoom=0.12, dx=-0.12).convert("RGBA")
    scrim(img, 0.85, 1.0)
    year_mark(img, 1914, cy=int(H * 0.175), size=215, color=AMBER)
    d = ImageDraw.Draw(img, "RGBA")
    p = ease_out((u - 0.35) / 0.9)
    if p > 0:
        f = fit("رم، ایتالیا", f_fa, 780, 84)
        center(d, "رم، ایتالیا", f, W / 2, int(H * 0.295 + (1 - p) * 24),
               CREAM + (int(255 * p),))
        kicker(d, "یک تراتوریای کوچک خانوادگی", W / 2, int(H * 0.365), size=45,
               alpha=int(230 * p))
    return img


def s_dilelio(t, a, b):
    u, dur = t - a, b - a
    img = still("fork_twirl.png", ease(u / dur), zoom=0.11, dy=0.12).convert("RGB")
    img = img.convert("RGBA")
    scrim(img, 0.8, 1.0)
    p = ease_out((u - 0.2) / 0.9)
    lay = card((880, 500), 40, (26, 17, 11), 228)
    cy = int(H * 0.665)
    paste_soft(img, lay, W / 2, cy, blur=26, alpha=175)
    d = ImageDraw.Draw(img, "RGBA")
    dx = int((1 - p) * 34)
    top = cy - 250
    f = fit("آلفردو دی لیلیو", f_fa, 760, 100)
    center(d, "آلفردو دی لیلیو", f, W / 2 + dx, top + 52, CREAM + (255,))
    rule(d, W / 2, top + 52 + int(f.size * 1.46), 200, AMBER)
    f2 = fit("و همسرش، آرمیدا", f_fa, 700, 58)
    center(d, "و همسرش، آرمیدا", f2, W / 2 + dx, top + 68 + int(f.size * 1.70),
           AMBER + (255,))
    center(d, "آشپزی که برای عشقش آشپزی کرد",
           fit("آشپزی که برای عشقش آشپزی کرد", f_fa, 720, 44),
           W / 2 + dx, top + 68 + int(f.size * 1.70) + 104, CREAM + (190,))
    return img


def s_three(t, a, b):
    u, dur = t - a, b - a
    bg = still("butter_parmesan.png", ease(u / dur), zoom=0.10).convert("RGBA")
    img = Image.blend(bg, Image.new("RGBA", bg.size, DARK + (255,)), 0.64)
    d = ImageDraw.Draw(img, "RGBA")
    p = ease_out((u - 0.1) / 0.8)
    f = fit("فقط سه چیز", f_fa, 840, 124)
    center(d, "فقط سه چیز", f, W / 2, int(H * 0.205), CREAM + (int(255 * p),),
           shadow=(5, (0, 0, 0, 175)))
    rule(d, W / 2, int(H * 0.205 + f.size * 1.42), 240, AMBER)

    tiles = [("ing_butter.png", "کره"), ("ing_parmesan.png", "پنیر پارمزان"),
             ("ing_water.png", "آب پاستا")]
    top, th, gap = int(H * 0.385), 300, 34
    tw = (880 - gap * 2) // 3
    for i, (fn, label) in enumerate(tiles):
        q = ease_out((u - 0.4 - i * 0.2) / 0.7)
        if q <= 0:
            continue
        x = (W - 880) // 2 + i * (tw + gap)
        y = top + int((1 - q) * 44)
        src = tile(fn, tw, th, zoom=1.0 + 0.06 * (1 - q), dy=0.0)
        mask = card((tw, th), 26, (0, 0, 0), 255).split()[3]
        img.paste(src, (x, y), mask)
        d.rounded_rectangle([x - 2, y - 2, x + tw + 1, y + th + 1], 28,
                            outline=AMBER + (200,), width=3)
        pf = fit(label, f_fa, tw - 26, 44)
        pill_w = min(tw - 12, text_w(d, fa(label), pf) + 48)
        py = y + th - 54
        d.rounded_rectangle([x + (tw - pill_w) // 2, py, x + (tw + pill_w) // 2, py + 66],
                            33, fill=(14, 9, 5, 235))
        center(d, label, pf, x + tw / 2, py + 9, CREAM + (255,))
    if u > 1.9:
        q = ease_out((u - 1.9) / 0.8)
        center(d, "و چیزی بیشتر لازم نیست", fit("و چیزی بیشتر لازم نیست", f_fa, 800, 52),
               W / 2, top + th + 96, CREAM + (int(215 * q),))
    return img


def s_nosugar(t, a, b):
    u, dur = t - a, b - a
    bg = still("fork_twirl.png", ease(u / dur), zoom=0.09, dx=0.1).convert("RGBA")
    img = Image.blend(bg, Image.new("RGBA", bg.size, DARK + (255,)), 0.58)
    d = ImageDraw.Draw(img, "RGBA")

    words = ["بدون خامه", "بدون سیر"]
    f = fit("بدون خامه", f_fa, 820, 100)
    for i, w in enumerate(words):
        yy = int(H * 0.205) + i * 152
        center(d, w, f, W / 2, yy, CREAM + (238,),
               shadow=(5, (0, 0, 0, 165)))
        q = ease_out((u - 0.45 - i * 0.45) / 0.5)
        if q > 0:
            ww = text_w(d, fa(w), f)
            y = yy + f.size * 0.60
            half = (ww / 2 + 18) * q
            d.line([W / 2 - half, y, W / 2 + half, y], fill=RED + (255,), width=13)

    q = ease_out((u - 1.85) / 0.8)
    if q > 0:
        fy = int(H * 0.525)
        f2 = fit("فتوچینی آلفردو", f_fa, 900, 128)
        center(d, "فتوچینی آلفردو", f2, W / 2, fy, AMBER + (int(255 * q),),
               shadow=(6, (0, 0, 0, int(175 * q))))
        rule(d, W / 2, fy + int(f2.size * 1.42), 280, CREAM)
        center(d, "همین سه چیز، این اسم را ساخت",
               fit("همین سه چیز، این اسم را ساخت", f_fa, 780, 46),
               W / 2, fy + int(f2.size * 1.62), CREAM + (int(205 * q),))
    return img


def s_glam(t, a, b):
    u, dur = t - a, b - a
    img = still("glam1927.png", ease(u / dur), zoom=0.14, dx=-0.08).convert("RGBA")
    scrim(img, 0.55, 0.35)
    band(img, int(H * 0.56), int(H * 0.86), (14, 9, 6), 0, 205, 1.0)
    band(img, int(H * 0.82), H, (10, 6, 4), 205, 250, 1.8)
    year_mark(img, 1927, cy=int(H * 0.115), size=185, color=AMBER)

    d = ImageDraw.Draw(img, "RGBA")
    p = ease_out((u - 0.45) / 0.9)
    if p > 0:
        cy = int(H * 0.60)
        f = fit("داگلاس فیربنکس", f_fa, 800, 86)
        center(d, "مری پیکفورد", f, W / 2, cy, CREAM + (int(255 * p),),
               shadow=(4, (0, 0, 0, 175)))
        center(d, "و داگلاس فیربنکس", f, W / 2, cy + int(f.size * 1.34),
               CREAM + (int(255 * p),), shadow=(4, (0, 0, 0, 175)))
        q = ease_out((u - 1.5) / 0.9)
        if q > 0:
            center(d, "دو ستاره سینمای صامت",
                   fit("دو ستاره سینمای صامت", f_fa, 780, 46),
                   W / 2, cy + int(f.size * 2.95), AMBER + (int(245 * q),),
                   shadow=(4, (0, 0, 0, int(200 * q))))
    return img


def s_world(t, a, b):
    u, dur = t - a, b - a
    base = still("hero_alfredo.png", 0.4, zoom=0.05).convert("RGBA")
    img = Image.blend(base, Image.new("RGBA", base.size, (18, 12, 8, 255)), 0.74)
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy, R = W / 2, int(H * 0.375), 285

    # wireframe globe: parallels + meridians, spun slowly
    for i in range(1, 5):                       # parallels
        yy = cy - R + 2 * R * i / 5
        rx = R * math.sqrt(max(0.02, 1 - ((yy - cy) / R) ** 2))
        d.ellipse([cx - rx, yy - rx * 0.13, cx + rx, yy + rx * 0.13],
                  outline=AMBER + (110,), width=2)
    spin = u * 0.35
    for i in range(6):                          # meridians
        ang = spin + i * math.pi / 6
        rx = abs(R * math.cos(ang))
        if rx < 6:
            continue
        al = int(60 + 90 * abs(math.sin(ang)))
        d.ellipse([cx - rx, cy - R, cx + rx, cy + R],
                  outline=AMBER + (al,), width=2)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=AMBER + (170,), width=3)

    # Rome dot + pulses travelling outward
    d.ellipse([cx - 9, cy - 22, cx + 9, cy - 4], fill=RED + (255,))
    d.ellipse([cx - 13, cy - 26, cx + 13, cy], outline=CREAM + (150,), width=2)
    for i in range(8):
        q = (u * 0.85 + i / 8) % 1
        rad = R * (0.15 + 0.9 * q)
        ang = -2.2 + i * 0.78
        px, py = cx + math.cos(ang) * rad, cy + math.sin(ang) * rad * 0.9
        al = int(220 * (1 - q) ** 1.4)
        r = 3 + 3 * q
        d.ellipse([px - r, py - r, px + r, py + r], fill=CREAM + (al,))

    b = badge(132)
    img.alpha_composite(b, (int(cx - 66), int(cy - 66)))
    d = ImageDraw.Draw(img, "RGBA")
    p = ease_out((u - 0.15) / 0.9)
    f = fit("از رم تا تمام دنیا", f_fa, 860, 92)
    center(d, "از رم تا تمام دنیا", f, W / 2, int(H * 0.665), CREAM + (int(255 * p),),
           shadow=(5, (0, 0, 0, 160)))
    return img


def s_usa(t, a, b):
    u, dur = t - a, b - a
    bg = still("butter_parmesan.png", ease(u / dur), zoom=0.10, dx=0.1).convert("RGBA")
    img = Image.blend(bg, Image.new("RGBA", bg.size, (20, 12, 7, 255)), 0.62)
    p = ease_out((u - 0.15) / 0.7)

    box = Image.new("RGBA", (870, 360), (0, 0, 0, 0))
    bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([8, 8, 861, 351], 26, outline=AMBER + (255,), width=9)
    bd.rounded_rectangle([30, 30, 839, 329], 18, outline=AMBER + (110,), width=3)
    f = fit("نسخه آمریکایی", f_fa, 700, 100)
    center(bd, "نسخه آمریکایی", f, 435, 92, AMBER + (255,))
    center(bd, "۱۹۵۰", f_fa(56), 435, 238, CREAM + (225,))
    box = box.rotate(-6, resample=Image.BICUBIC, expand=False)
    box.putalpha(box.split()[3].point(lambda v: int(v * p)))
    img.alpha_composite(box, (int(W / 2 - 435), int(H * 0.36 - 180)))

    d = ImageDraw.Draw(img, "RGBA")
    q = ease_out((u - 0.85) / 0.9)
    if q > 0:
        f2 = fit("خامه اضافه شد", f_fa, 800, 72)
        center(d, "خامه اضافه شد", f2, W / 2, int(H * 0.625), CREAM + (int(255 * q),))
        center(d, "و سس، غلیظ و سفید شد", fit("و سس، غلیظ و سفید شد", f_fa, 800, 46),
               W / 2, int(H * 0.625) + int(f2.size * 1.55), CREAM + (int(190 * q),))
    return img


def s_retro1(t, a, b):
    u, dur = t - a, b - a
    img = still("hero_alfredo.png", ease(u / dur), zoom=0.15, dy=0.10).convert("RGBA")
    scrim(img, 0.5, 1.0)
    cy = int(H * 0.635)
    lay = card((900, 520), 44, (24, 16, 10), 230)
    paste_soft(img, lay, W / 2, cy, blur=28, alpha=185)
    d = ImageDraw.Draw(img, "RGBA")
    top = cy - 260
    b = badge(104)
    img.alpha_composite(b, (int(W / 2 - 52), top + 34))
    d = ImageDraw.Draw(img, "RGBA")
    f = fit("فتوچینی آلفردو", f_fa, 800, 88)
    center(d, "فتوچینی آلفردو", f, W / 2, top + 168, CREAM + (255,))
    rule(d, W / 2, top + 168 + int(f.size * 1.46), 230, AMBER)
    items = "قارچ تازه\u200f • \u200fمرغ گریل\u200f • \u200fسس پارمزان"
    center(d, items, fit(items, f_fa, 800, 44), W / 2,
           top + 168 + int(f.size * 1.70), AMBER + (255,))
    center(d, "همان داستان، در کافه رترو",
           fit("همان داستان، در کافه رترو", f_fa, 760, 42),
           W / 2, top + 168 + int(f.size * 1.70) + 82, CREAM + (200,))
    return img


def s_retro2(t, a, b):
    u, dur = t - a, b - a
    yy = np.linspace(0, 1, H)[:, None, None]
    arr = np.ones((H, W, 1), np.float32) * ((1 - yy) * 0.95 + 0.32)
    base = Image.fromarray(
        np.clip(np.array((30, 19, 12), np.float32) * arr, 0, 255).astype(np.uint8),
        "RGB").convert("RGBA")
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([W / 2 - 470, 300, W / 2 + 470, 1120],
                                 fill=(126, 70, 26, 95))
    base.alpha_composite(halo.filter(ImageFilter.GaussianBlur(95)))
    img = base

    p = ease_out((u - 0.12) / 1.0)
    lw = int(860 * (0.95 + 0.05 * p))
    lay = lockup(lw, mode="dark")
    lay.putalpha(lay.split()[3].point(lambda v: int(v * p)))
    img.alpha_composite(lay, (int(W / 2 - lw / 2), int(468 + (1 - p) * 28)))

    d = ImageDraw.Draw(img, "RGBA")
    q = ease_out((u - 0.75) / 0.9)
    if q > 0:
        rule(d, W / 2, 902, 320, AMBER)
        center(d, "کافه رترو، نسیم شهر", fit("کافه رترو، نسیم شهر", f_fa, 880, 62),
               W / 2, 940, CREAM + (int(240 * q),))
        center(d, "هر روز، ده صبح تا ده شب", fit("هر روز، ده صبح تا ده شب", f_fa, 800, 50),
               W / 2, 1036, AMBER + (int(235 * q),))
        center(d, "جنب درمانگاه قائم", fit("جنب درمانگاه قائم", f_fa, 800, 44),
               W / 2, 1116, CREAM + (int(195 * q),))
        cw, ch, gap = 380, 92, 26
        x0 = (W - (cw * 2 + gap)) / 2
        for i, txt in enumerate(["@Caferetro_ir", "۰۹۳۶۹۱۹۲۲۹۷"]):
            cx = x0 + i * (cw + gap) + cw / 2
            cy = 1246
            d.rounded_rectangle([cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2],
                                ch / 2, outline=AMBER + (int(200 * q),), width=3)
            f = f_disp(38) if i == 0 else f_fa(44, "Medium")
            center(d, txt, f, cx, cy - (26 if i == 0 else 23),
                   CREAM + (int(240 * q),), shaped=(i != 0))
    return img


SCENES = [
    ("hook", s_hook), ("rome", s_rome), ("dilelio", s_dilelio),
    ("three", s_three), ("nosugar", s_nosugar), ("glam", s_glam),
    ("world", s_world), ("usa", s_usa), ("retro1", s_retro1), ("retro2", s_retro2),
]
