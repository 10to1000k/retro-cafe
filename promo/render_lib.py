# -*- coding: utf-8 -*-
"""
ابزارهای مشترک ساخت ویدئو — متن فارسی، کارت، آیکون، بافت
Shared helpers for the RETRO CAFE promo reel.
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
import arabic_reshaper
from bidi.algorithm import get_display
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # retro-cafe/
BUILD = os.path.join(HERE, "build")
FONT_SRC = os.path.join(ROOT, "fonts")
FONT_DIR = os.path.join(BUILD, "fonts")
os.makedirs(FONT_DIR, exist_ok=True)
os.makedirs(BUILD, exist_ok=True)

# ─────────── پالت رترو (هم‌خوان با index.html) ───────────
CREAM      = (255, 248, 238)
CREAM_DEEP = (245, 233, 216)
INK        = (42, 29, 19)
INK_SOFT   = (107, 87, 69)
MUTED      = (160, 138, 115)
RED        = (214, 58, 47)
RED_DEEP   = (192, 48, 31)
RED_DARK   = (158, 46, 31)
GOLD       = (255, 182, 39)
GOLD_DEEP  = (184, 122, 22)
WOOD       = (138, 90, 43)
WHITE      = (255, 255, 255)
SNAP       = (236, 19, 141)      # صورتی اسنپ‌فود
SNAP_DEEP  = (200, 10, 116)

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


# ─────────── فونت ───────────
_FONT_NAMES = {
    "regular": "Vazirmatn-Regular",
    "medium":  "Vazirmatn-Medium",
    "bold":    "Vazirmatn-Bold",
    "brand":   "AlfaSlabOne-Latin",
}
_font_cache = {}


def font_path(key):
    """woff2 مخزن را یک‌بار به ttf تبدیل می‌کند (Pillow نمی‌تواند woff2 بخواند)."""
    name = _FONT_NAMES[key]
    out = os.path.join(FONT_DIR, name + ".ttf")
    if not os.path.exists(out):
        f = TTFont(os.path.join(FONT_SRC, name + ".woff2"))
        f.flavor = None
        f.save(out)
    return out


def F(key, size):
    k = (key, size)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(font_path(key), size)
    return _font_cache[k]


# ─────────── متن فارسی ───────────
def fa(s):
    """تبدیل ارقام لاتین به فارسی"""
    return "".join(FA_DIGITS[int(c)] if c.isdigit() else c for c in str(s))


def money(v):
    """۵۹۰ → ۵۹۰٬۰۰۰ تومان  (مثل خود منو)"""
    n = int(v) * 1000 if v < 10000 else int(v)
    return fa(f"{n:,}").replace(",", "٬") + " تومان"


_reshape_cache = {}


def shape(txt):
    if txt not in _reshape_cache:
        _reshape_cache[txt] = get_display(arabic_reshaper.reshape(txt), base_dir="R")
    return _reshape_cache[txt]


def text_size(txt, key, size, tracking=0, rtl=True):
    f = F(key, size)
    s = shape(txt) if rtl else txt
    if tracking:
        w = sum(f.getlength(c) for c in s) + tracking * (len(s) - 1)
        return int(math.ceil(w)), size
    box = f.getbbox(s)
    return int(box[2] - box[0]), int(box[3] - box[1])


_text_cache = {}


def text_img(txt, key, size, color, tracking=0, rtl=True, pad=8, stroke=0,
             stroke_color=None):
    ck = (txt, key, size, tuple(color), tracking, rtl, pad, stroke,
          tuple(stroke_color) if stroke_color else None)
    if ck in _text_cache:
        return _text_cache[ck]
    f = F(key, size)
    s = shape(txt) if rtl else txt
    if tracking:
        w = int(sum(f.getlength(c) for c in s) + tracking * (len(s) - 1))
        h = int(size * 1.7)
        img = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        x = float(pad)
        for c in s:
            d.text((x, pad), c, font=f, fill=tuple(color) + (255,),
                   stroke_width=stroke, stroke_fill=stroke_color)
            x += f.getlength(c) + tracking
        _text_cache[ck] = img
        return img

    box = f.getbbox(s)
    w, h = box[2] - box[0], box[3] - box[1]
    img = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((pad - box[0], pad - box[1]), s, font=f, fill=tuple(color) + (255,),
           stroke_width=stroke, stroke_fill=stroke_color)
    _text_cache[ck] = img
    return img


def wrap(txt, key, size, max_w):
    """شکستن متن در عرض مشخص"""
    f = F(key, size)
    words, lines, cur = txt.split(" "), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if f.getlength(shape(trial)) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ─────────── کمکی‌های انیمیشن ───────────
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def back_out(x, s=1.7):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def prog(t, start, dur):
    """پیشرفت ۰..۱ یک انیمیشن که در زمان start شروع می‌شود"""
    if dur <= 0:
        return 1.0 if t >= start else 0.0
    return clamp((t - start) / dur)


def paste(canvas, img, center, alpha=1.0, scale=1.0, anchor="center"):
    """چسباندن تصویر RGBA با کدری و مقیاس"""
    if alpha <= 0.004 or img is None:
        return
    if abs(scale - 1.0) > 0.002:
        w = max(1, int(img.width * scale))
        h = max(1, int(img.height * scale))
        img = img.resize((w, h), Image.LANCZOS)
    if alpha < 0.996:
        img = img.copy()
        a = img.getchannel("A").point(lambda v: int(v * alpha))
        img.putalpha(a)
    if anchor == "center":
        x = int(center[0] - img.width / 2)
        y = int(center[1] - img.height / 2)
    elif anchor == "topcenter":
        x = int(center[0] - img.width / 2)
        y = int(center[1])
    elif anchor == "left":
        x, y = int(center[0]), int(center[1] - img.height / 2)
    else:  # right
        x, y = int(center[0] - img.width), int(center[1] - img.height / 2)
    canvas.alpha_composite(img, (x, y))


def rounded_mask(size, radius, ss=1):
    m = Image.new("L", (size[0] * ss, size[1] * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        [0, 0, size[0] * ss - 1, size[1] * ss - 1], radius=radius * ss, fill=255)
    if ss > 1:
        m = m.resize(size, Image.LANCZOS)
    return m


def shadow_from(mask, blur=26, spread=(8, 14), opacity=110, color=(0, 0, 0)):
    pad = blur * 2
    w, h = mask.width + pad * 2, mask.height + pad * 2
    base = Image.new("L", (w, h), 0)
    base.paste(mask, (pad + spread[0], pad + spread[1]))
    base = base.filter(ImageFilter.GaussianBlur(blur))
    a = base.point(lambda v: int(v * opacity / 255))
    sh = Image.new("RGBA", (w, h), tuple(color) + (0,))
    sh.putalpha(a)
    return sh


def make_card(size, radius=34, fill=CREAM, content=None, shadow=True,
              shadow_op=105, blur=30, spread=(0, 16), outline=None, ow=3):
    """کارت گرد با سایه. content(body) روی مختصات خودِ کارت نقاشی می‌کند.
    برمی‌گرداند (تصویر نهایی, لنگر مرکز کارت)"""
    w, h = size
    fc = tuple(fill)
    if len(fc) == 3:
        fc = fc + (255,)
    body = Image.new("RGBA", (w, h), fc)
    if content is not None:
        content(body)
    mask = rounded_mask((w, h), radius)
    if outline:
        ImageDraw.Draw(body).rounded_rectangle(
            [ow // 2, ow // 2, w - 1 - ow // 2, h - 1 - ow // 2],
            radius=radius, outline=tuple(outline) + (255,), width=ow)
    body.putalpha(mask)

    if not shadow:
        return body, (w / 2, h / 2)
    sh = shadow_from(mask, blur=blur, spread=spread, opacity=shadow_op)
    out = Image.new("RGBA", (sh.width, sh.height), (0, 0, 0, 0))
    out.alpha_composite(sh)
    ox = sh.width // 2 - w // 2 + spread[0]
    oy = sh.height // 2 - h // 2 + spread[1]
    out.alpha_composite(body, (ox, oy))
    return out, (ox + w / 2, oy + h / 2)


def photo_card(photo, size, radius=40, border=0, border_color=CREAM,
               shadow_op=140, blur=34, spread=(0, 22)):
    """عکس داخل قاب گرد (کادر کرمی اختیاری)"""
    w, h = size
    if border:
        w, h = w + border * 2, h + border * 2
    mask = rounded_mask((w, h), radius)
    body = Image.new("RGBA", (w, h), tuple(border_color) + (255,))
    inner = fit_cover(photo, (size[0], size[1]))
    body.alpha_composite(inner.convert("RGBA"), (border, border))
    body.putalpha(mask)
    # خط موی طلایی
    ImageDraw.Draw(body).rounded_rectangle(
        [1, 1, w - 2, h - 2], radius=radius,
        outline=(255, 210, 140, 90), width=2)
    sh = shadow_from(mask, blur=blur, spread=spread, opacity=shadow_op)
    out = Image.new("RGBA", (sh.width, sh.height), (0, 0, 0, 0))
    out.alpha_composite(sh)
    ox = sh.width // 2 - w // 2 + spread[0]
    oy = sh.height // 2 - h // 2 + spread[1]
    out.alpha_composite(body, (ox, oy))
    return out, (ox + w / 2, oy + h / 2)


def pill(txt, key="bold", size=34, fg=WHITE, bg=SNAP, padx=34, pady=16,
         radius=None, tracking=0, shadow=True):
    tw, th = text_size(txt, key, size, tracking)
    w, h = tw + padx * 2, max(th + pady * 2, size + pady * 2)
    r = radius if radius is not None else h // 2
    mask = rounded_mask((w, h), r)
    bgc = tuple(bg)
    if len(bgc) == 3:
        bgc = bgc + (255,)
    body = Image.new("RGBA", (w, h), bgc)
    body.putalpha(mask)
    t = text_img(txt, key, size, fg, tracking=tracking)
    body.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2))
    if not shadow:
        return body, (w // 2, h // 2)
    sh = shadow_from(mask, blur=16, spread=(0, 8), opacity=70, color=(90, 30, 10))
    out = Image.new("RGBA", (sh.width, sh.height), (0, 0, 0, 0))
    out.alpha_composite(sh)
    out.alpha_composite(body, (sh.width // 2 - w // 2, sh.height // 2 - h // 2 + 8))
    return out, (w // 2, h // 2 + 8)


# ─────────── آیکون‌های خطی (۴ برابر رندر، بعد کوچک) ───────────
def icon(kind, size, fg=WHITE, bg=None, sw=6):
    ss = 4
    S = size * ss
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if bg:
        d.ellipse([0, 0, S - 1, S - 1], fill=tuple(bg) + (255,))
    c = tuple(fg) + (255,)
    w = sw * ss
    p = int(S * 0.26)
    if kind == "phone":
        d.rounded_rectangle([p + S * .02, p, S - p - S * .02, S - p], radius=S * .10,
                            outline=c, width=w)
        d.line([S * .44, S * .82, S * .56, S * .82], fill=c, width=int(w * .8))
    elif kind == "instagram":
        d.rounded_rectangle([p, p, S - p, S - p], radius=S * .13, outline=c, width=w)
        d.ellipse([S * .38, S * .38, S * .62, S * .62], outline=c, width=w)
        d.ellipse([S * .70, S * .27, S * .755, S * .325], fill=c)
    elif kind == "pin":
        d.ellipse([S * .32, S * .22, S * .68, S * .58], outline=c, width=w)
        d.line([S * .34, S * .53, S * .5, S * .80], fill=c, width=w)
        d.line([S * .66, S * .53, S * .5, S * .80], fill=c, width=w)
        d.ellipse([S * .45, S * .35, S * .55, S * .45], fill=c)
    elif kind == "clock":
        d.ellipse([p, p, S - p, S - p], outline=c, width=w)
        d.line([S * .5, S * .5, S * .5, S * .33], fill=c, width=w)
        d.line([S * .5, S * .5, S * .63, S * .56], fill=c, width=w)
    elif kind == "bag":
        d.rounded_rectangle([p, S * .38, S - p, S * .78], radius=S * .06,
                            outline=c, width=w)
        d.arc([p + S * .06, S * .22, S - p - S * .06, S * .56], 180, 360, fill=c, width=w)
    elif kind == "star":
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            r = S * .30 if i % 2 == 0 else S * .13
            pts.append((S / 2 + r * math.cos(ang), S / 2 + r * math.sin(ang)))
        d.polygon(pts, fill=c)
    return img.resize((size, size), Image.LANCZOS)


# ─────────── بافت‌ها ───────────
def sunburst(size, center, color, alpha=14, rays=36, spread=1):
    """اشعه‌های رترو"""
    ss = 2
    W, H = size[0] * ss, size[1] * ss
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    cx, cy = center[0] * ss, center[1] * ss
    R = max(W, H) * 1.5
    for i in range(rays):
        a0 = (i * 2 * math.pi / rays) - math.pi / 2
        a1 = a0 + (math.pi / rays) * spread
        d.polygon([(cx, cy),
                   (cx + R * math.cos(a0), cy + R * math.sin(a0)),
                   (cx + R * math.cos(a1), cy + R * math.sin(a1))], fill=255)
    img = img.resize(size, Image.LANCZOS)
    out = Image.new("RGBA", size, tuple(color) + (0,))
    out.putalpha(img.point(lambda v: int(v * alpha / 255)))
    return out


def stripes(size, color, alpha=8, step=22, angle=45):
    ss = 1
    img = Image.new("L", (size[0] * 2, size[1] * 2), 0)
    d = ImageDraw.Draw(img)
    W, H = img.size
    for x in range(-H, W + H, step * 2):
        d.line([(x, 0), (x + H, H)], fill=255, width=step // 2)
    img = img.rotate(angle, resample=Image.BILINEAR, expand=False)
    img = img.resize(size, Image.LANCZOS)
    out = Image.new("RGBA", size, tuple(color) + (0,))
    out.putalpha(img.point(lambda v: int(v * alpha / 255)))
    return out


def grain_tiles(n, size, strength=16):
    tiles = []
    h, w = size[1] // 2, size[0] // 2
    for i in range(n):
        rng = np.random.default_rng(1000 + i)
        a = rng.normal(128, strength, (h, w)).clip(0, 255).astype(np.uint8)
        tiles.append(Image.fromarray(a, "L").resize(size, Image.BILINEAR))
    return tiles


def vignette(size, strength=0.42, power=2.2):
    W, H = size
    y, x = np.ogrid[:H, :W]
    cx, cy = W / 2, H / 2
    r = np.sqrt(((x - cx) / (W * 0.62)) ** 2 + ((y - cy) / (H * 0.62)) ** 2)
    v = (1 - strength * np.clip(r, 0, 1) ** power).clip(0, 1)
    v = (v * 255).astype(np.uint8)
    return Image.fromarray(v, "L")


def fit_cover(im, size):
    tw, th = size
    s = max(tw / im.width, th / im.height)
    im2 = im.resize((max(1, int(im.width * s + 0.5)), max(1, int(im.height * s + 0.5))),
                    Image.LANCZOS)
    x = (im2.width - tw) // 2
    y = (im2.height - th) // 2
    return im2.crop((x, y, x + tw, y + th))


def gradient(size, stops, horizontal=False):
    """گرادیان عمودی/افقی از فهرست (موقعیت, رنگ)"""
    W, H = size
    n = H if not horizontal else W
    arr = np.zeros((n, 4), dtype=np.float32)
    stops = sorted(stops, key=lambda s: s[0])
    for i in range(n):
        p = i / max(1, n - 1)
        c = stops[-1][1]
        for j in range(len(stops) - 1):
            p0, c0 = stops[j]
            p1, c1 = stops[j + 1]
            if p0 <= p <= p1:
                k = (p - p0) / max(1e-6, (p1 - p0))
                c = tuple(c0[m] + (c1[m] - c0[m]) * k for m in range(4))
                break
        arr[i] = c
    band = Image.fromarray(arr.astype(np.uint8).reshape(n, 1, 4), "RGBA")
    if horizontal:
        band = band.resize((n, 1), Image.NEAREST).rotate(90, expand=True)
        band = band.resize((W, H), Image.BILINEAR)
    else:
        band = band.resize((W, H), Image.BILINEAR)
    return band


def logo_mark(size):
    path = os.path.join(BUILD, "logo-mark.png")
    if not os.path.exists(path):
        raise SystemExit("logo-mark.png missing — build assets first")
    im = Image.open(path).convert("RGBA")
    return im.resize((size, size), Image.LANCZOS)
