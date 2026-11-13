"""Shared drawing helpers for the Alfredo reel (1080x1920, PIL + numpy)."""
import os

import arabic_reshaper
import numpy as np
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))

RED = (192, 48, 31)
AMBER = (255, 182, 39)
CREAM = (255, 248, 238)
DARK = (42, 29, 19)
ACCENT = (184, 122, 22)
BRAND_RED = (142, 14, 24)     # new logo red

_RS = arabic_reshaper.ArabicReshaper(
    configuration={"delete_harakat": False, "support_ligatures": True})


def fa(text):
    """Shape + bidi-reorder Persian text for PIL (no raqm in this build)."""
    return get_display(_RS.reshape(text))


def pdigits(s):
    """Latin digits -> Persian digits (year/number typography)."""
    return str(s).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


_font_cache = {}


def font(name, size):
    key = (name, int(size))
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(os.path.join(HERE, name + ".ttf"), int(size))
    return _font_cache[key]


def f_fa(size, weight="Bold"):
    return font("Vazirmatn-" + weight, size)


def f_disp(size):
    return font("AlfaSlabOne-Latin", size)


def text_w(d, s, f):
    return d.textbbox((0, 0), s, font=f)[2]


def fit(s, ffn, maxw, start, floor=26, shaped=True):
    """Largest size <= start that keeps `s` within maxw."""
    size = start
    tmp = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    disp = fa(s) if shaped else s
    while size > floor and text_w(tmp, disp, ffn(size)) > maxw:
        size -= 2
    return ffn(size)


def rule(d, cx, y, w=210, color=AMBER, thick=5):
    d.line([cx - w / 2, y, cx + w / 2, y], fill=color + (255,), width=thick)


def center(d, s, f, cx, y, fill, shadow=None, shaped=True, anchor_center=True):
    disp = fa(s) if shaped else s
    w = text_w(d, disp, f)
    x = cx - w / 2 if anchor_center else cx
    if shadow:
        off, scol = shadow
        d.text((x + off, y + off), disp, font=f, fill=scol)
    d.text((x, y), disp, font=f, fill=fill)
    return w


def spaced(d, s, f, cx, y, fill, gap=0):
    disp = fa(s) if any("\u0600" <= c <= "\u06ff" for c in s) else s
    widths = [d.textbbox((0, 0), ch, font=f)[2] for ch in disp]
    total = sum(widths) + gap * (len(disp) - 1)
    x = cx - total / 2
    for ch, w in zip(disp, widths):
        d.text((x, y), ch, font=f, fill=fill)
        x += w + gap
    return total


_band_cache = {}


def band(img, y0, y1, color, a0=0, a1=210, gamma=1.4):
    """Vertical gradient scrim, alpha eased with `gamma`. Cached per box."""
    key = (img.size, y0, y1, color, a0, a1, gamma)
    if key not in _band_cache:
        h = max(1, y1 - y0)
        u = np.linspace(0, 1, h) ** gamma
        col = np.zeros((h, 1, 4), np.float32)
        col[..., :3] = np.array(color, np.float32)
        col[..., 3] = (a0 + (a1 - a0) * u)[:, None] * 255
        _band_cache[key] = Image.fromarray(col.astype(np.uint8), "RGBA")
    img.alpha_composite(_band_cache[key], (0, max(0, y0)))


def vignette(img, strength=0.55, feather=1.6):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, H / 2
    r = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2) / 1.414
    m = np.clip((r ** feather) * strength, 0, 1)
    a = (m * 255).astype(np.uint8)
    v = np.zeros((H, W, 4), np.uint8)
    v[..., 3] = a
    img.alpha_composite(Image.fromarray(v, "RGBA"))


def grain(img, amount=8, seed=0):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, amount, (H // 2, W // 2)).astype(np.float32)
    n = np.repeat(np.repeat(n, 2, 0), 2, 1)[:H, :W]
    rgb = np.asarray(img.convert("RGB"), np.float32) + n[..., None]
    return np.clip(rgb, 0, 255).astype(np.uint8)


def kenburns(im, u, zoom=0.10, dx=0.0, dy=0.0, rot=0.0):
    """Crop-and-scale a still into WxH with a slow push."""
    iw, ih = im.size
    s = max(W / iw, H / ih) * (1 + zoom * u)
    nw, nh = int(iw * s) + 2, int(ih * s) + 2
    big = im.resize((nw, nh), Image.LANCZOS)
    if rot:
        big = big.rotate(rot * u, resample=Image.BICUBIC, expand=False)
    maxx, maxy = max(0, nw - W), max(0, nh - H)
    x = int(maxx * (0.5 + dx * (u - 0.5) * 2))
    y = int(maxy * (0.5 + dy * (u - 0.5) * 2))
    return big.crop((x, y, x + W, y + H))


def still(path, u=0.5, zoom=0.10, dx=0.0, dy=0.0, rot=0.0):
    im = Image.open(os.path.join(HERE, "img", path)).convert("RGB")
    return kenburns(im, u, zoom, dx, dy, rot)


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def fade_io(u, dur, fin=0.35, fout=0.35):
    """Local-time fade in/out, 0..1."""
    return min(1.0, u / fin if fin else 1, (dur - u) / fout if fout else 1)


def ease_out(u):
    u = min(1.0, max(0.0, u))
    return 1 - (1 - u) ** 3


def card(size, radius, fill, alpha=225, border=None, bw=3):
    w, h = size
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius, fill=fill + (alpha,),
                        outline=(border + (255,)) if border else None, width=bw)
    return lay


def shadowed(lay, blur=18, alpha=150, off=(0, 10)):
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, alpha), (0, 0), lay.split()[3])
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    return sh


def paste_soft(img, lay, cx, cy, blur=18, alpha=150, off=(0, 10)):
    x = int(cx - lay.width / 2)
    y = int(cy - lay.height / 2)
    sh = shadowed(lay, blur, alpha, off)
    img.alpha_composite(sh, (x + off[0], y + off[1]))
    img.alpha_composite(lay, (x, y))
