# -*- coding: utf-8 -*-
"""
RETRO CAFE × اسنپ‌فود — ساخت ریلز تبلیغاتی ۱۰۸۰×۱۹۲۰

اجرا:
    python render.py still 2.0 6.7 ...   → PNG برای بازبینی
    python render.py video               → MP4 نهایی
"""
import os
import sys
import math
import subprocess
import shutil

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance

from render_lib import (
    CREAM, CREAM_DEEP, INK, INK_SOFT, MUTED, RED, RED_DEEP, RED_DARK, GOLD,
    GOLD_DEEP, WOOD, WHITE, SNAP, SNAP_DEEP, BUILD, ROOT, HERE,
    F, fa, money, text_img, text_size, wrap, shape,
    clamp, ease_out, ease_in_out, back_out, prog, paste,
    rounded_mask, shadow_from, make_card, photo_card, pill, icon,
    sunburst, stripes, grain_tiles, vignette, fit_cover, gradient, logo_mark,
)

W, H = 1080, 1920
FPS = 30
MG = 82

# ══════════════════ محتوای تبلیغ (همه از index.html) ══════════════════
DISHES = [
    dict(name="برگر ویژه رترو", price=590, tag="پیشنهاد ویژه",
         desc="برگر گوشت مخصوص، پنیر، سس دودی و سیب‌زمینی",
         img="images/items/برگر ویژه رترو.jpg"),
    dict(name="سیب ویژه", price=435, tag="پیشنهاد ویژه",
         desc="سیب‌زمینی با سس مخصوص، پنیر و مخلفات",
         img="images/items/سیب ویژه.jpg"),
    dict(name="پاستا آلفردو", price=490, tag="",
         desc="فتوچینی با سس خامه‌ای آلفردو، قارچ و مرغ",
         img="images/items/پاستا آلفردو.jpg"),
    dict(name="پنیری مرغ گریل", price=545, tag="",
         desc="ساندویچ مرغ گریل با پنیر آب‌شده",
         img="images/items/پنیری مرغ گریل.jpg"),
    dict(name="سالاد سزار", price=460, tag="",
         desc="کاهو، مرغ گریل، نان تست و سس سزار",
         img="images/items/سالاد سزار.jpg"),
    dict(name="شیک نوتلا", price=300, tag="",
         desc="نوتلا اصل، بستنی وانیلی، فندق و شیر",
         img="images/items/شیک نوتلا.jpg"),
]

VIBE = [
    dict(img="images/items/کاپوچینو.jpg", t1="قهوه‌ی دست‌ساز", t2="تازه دم، هر بار",
         pan=(0.30, 0.25), z=(1.17, 1.04)),
    dict(img="images/items/آیس لاته.jpg", t1="نوشیدنی خنک", t2="برای روزهای گرم",
         pan=(0.30, 0.20), z=(1.17, 1.04)),
    dict(img="images/space/space-window-table-portrait.jpg",
         t1="فضای گرم و دنج", t2="بنشین، نفس بکش، کیف کن",
         pan=(0.15, -0.85), z=(1.02, 1.10)),
]

# ══════════════════ زمان‌بندی ══════════════════
S_INTRO = dict(start=0.00, dur=5.20)
S_FOOD_DUR = 2.00
S_FOOD = dict(start=S_INTRO["dur"], dur=S_FOOD_DUR * len(DISHES))
VIBE_DURS = [1.60, 1.90, 3.40]          # قهوه / خنک / فضا
S_VIBE = dict(start=S_FOOD["start"] + S_FOOD["dur"], dur=sum(VIBE_DURS))
S_REVEAL = dict(start=S_VIBE["start"] + S_VIBE["dur"], dur=6.50)
S_OUTRO = dict(start=S_REVEAL["start"] + S_REVEAL["dur"], dur=6.30)
TOTAL = S_OUTRO["start"] + S_OUTRO["dur"]
XFADE = 0.32

print(f"[timeline] food={S_FOOD['start']:.2f} vibe={S_VIBE['start']:.2f} "
      f"reveal={S_REVEAL['start']:.2f} outro={S_OUTRO['start']:.2f} "
      f"total={TOTAL:.2f}s", file=sys.stderr)

# ══════════════════ ابزار تصویر ══════════════════
_cache = {}
_grain = grain_tiles(3, (W, H), strength=9)
_vig = vignette((W, H), strength=0.40, power=2.3)
_vig_soft = vignette((W, H), strength=0.22, power=2.0)


def load_photo(rel, overscan=1.22, max_h=2600):
    key = (rel, overscan, max_h)
    if key in _cache:
        return _cache[key]
    im = Image.open(os.path.join(ROOT, rel)).convert("RGB")
    if im.height > max_h:
        im = im.resize((int(im.width * max_h / im.height), max_h), Image.LANCZOS)
    im = fit_cover(im, (int(W * overscan), int(H * overscan)))
    _cache[key] = im
    return im


def ken_burns(base, p, zoom0=1.06, zoom1=1.18, pan=(0.0, 0.0)):
    p = clamp(p)
    z = zoom0 + (zoom1 - zoom0) * p
    cw, ch = W / z, H / z
    cx = base.width / 2 + pan[0] * (base.width - cw) / 2 * (0.5 - p) * 2
    cy = base.height / 2 + pan[1] * (base.height - ch) / 2 * (0.5 - p) * 2
    cx = min(max(cx, cw / 2), base.width - cw / 2)
    cy = min(max(cy, ch / 2), base.height - ch / 2)
    box = (int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))
    return base.crop(box).resize((W, H), Image.BICUBIC)


def finish(img, t, grain=True, vig=None):
    if vig is not None:
        rgb = Image.composite(img.convert("RGB"),
                              Image.new("RGB", (W, H), (10, 5, 2)), vig)
        img = rgb.convert("RGBA")
    if grain:
        g = _grain[int(t * 15) % len(_grain)]
        img = ImageChops.overlay(img.convert("RGB"),
                                 Image.merge("RGB", (g, g, g))).convert("RGBA")
    return img


def bottom_fade(img, top=0.42, alpha=215, color=(18, 9, 3)):
    img.alpha_composite(gradient((W, H), [
        (0.0, color + (0,)), (top, color + (0,)),
        (min(1.0, top + 0.30), color + (int(alpha * .60),)), (1.0, color + (alpha,))]))
    return img


def top_fade(img, bottom=0.30, alpha=200, color=(18, 9, 3)):
    img.alpha_composite(gradient((W, H), [
        (0.0, color + (alpha,)), (bottom, color + (0,)), (1.0, color + (0,))]))
    return img


def glow(img, box, color=(255, 178, 66), a=30, blur=130):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse(box, fill=tuple(color) + (a,))
    img.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur)))
    return img


# ══════════════════ پیل اسنپ‌فود ══════════════════
def _snap_pill():
    txt = text_img("اسنپ‌فود", "bold", 60, WHITE)
    ic = icon("bag", 46, WHITE)
    padx, pady, gap = 42, 26, 20
    w = padx * 2 + ic.width + gap + txt.width
    h = max(txt.height, ic.height) + pady * 2
    mask = rounded_mask((w, h), h // 2)
    body = Image.new("RGBA", (w, h), SNAP + (255,))
    body.alpha_composite(gradient((w, h), [(0.0, (255, 255, 255, 52)),
                                           (0.6, (255, 255, 255, 0))]))
    body.putalpha(mask)
    body.alpha_composite(ic, (padx, (h - ic.height) // 2))
    body.alpha_composite(txt, (padx + ic.width + gap, (h - txt.height) // 2))
    sh = shadow_from(mask, blur=28, spread=(0, 16), opacity=120, color=(120, 8, 66))
    out = Image.new("RGBA", (sh.width, sh.height), (0, 0, 0, 0))
    out.alpha_composite(sh)
    ox, oy = sh.width // 2 - w // 2, sh.height // 2 - h // 2 + 16
    out.alpha_composite(body, (ox, oy))
    return out, (ox + w / 2, oy + h / 2)


SNAP_PILL = _snap_pill()


def snap_mark(size=132, bg=WHITE):
    """نشان کوچک: کیسه‌ی خرید روی دیسک صورتی — برای گوشه‌ی کارت‌ها"""
    ss = 3
    S = size * ss
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, S - 1, S - 1], fill=tuple(bg) + (255,))
    d.ellipse([S * .09, S * .09, S * .91, S * .91], fill=SNAP + (255,))
    ic = icon("bag", int(S * .40), WHITE)
    img.alpha_composite(ic.convert("RGBA"), (int(S * .30), int(S * .34)))
    return img.resize((size, size), Image.LANCZOS)


# ══════════════════ سکانس ۱ — هوک ══════════════════
def scene_intro(t, T):
    base = load_photo("images/hero.jpg", overscan=1.24)
    img = ken_burns(base, t / T, 1.02, 1.13, pan=(0.30, 0.12)).convert("RGBA")
    img = Image.blend(img, Image.new("RGBA", (W, H), (58, 26, 8, 255)), 0.12)
    img = top_fade(img, 0.44, alpha=210)
    img = bottom_fade(img, 0.48, alpha=232)
    img = glow(img, [W * .02, H * .55, W * .98, H * .95], a=32)

    # لوگو
    p = prog(t, 0.15, 0.70)
    if p > 0:
        sz = int(248 * (0.70 + 0.30 * back_out(p)))
        lm = logo_mark(sz)
        lm.putalpha(lm.getchannel("A").point(lambda v: int(v * ease_out(p))))
        paste(img, lm, (W / 2, 540))

    p = prog(t, 0.50, 0.65)
    if p > 0:
        ti = text_img("RETRO CAFE", "brand", 106, CREAM, tracking=6, rtl=False)
        paste(img, ti, (W / 2, 738 + (1 - ease_out(p)) * 26), alpha=ease_out(p))

    p = prog(t, 0.80, 0.50)
    if p > 0:
        wline = int(420 * ease_out(p))
        ln = Image.new("RGBA", (max(4, wline), 22), (0, 0, 0, 0))
        d = ImageDraw.Draw(ln)
        cx = ln.width // 2
        d.line([(0, 11), (cx - 24, 11)], fill=GOLD + (255,), width=3)
        d.line([(cx + 24, 11), (ln.width, 11)], fill=GOLD + (255,), width=3)
        d.polygon([(cx, 2), (cx + 9, 11), (cx, 20), (cx - 9, 11)], fill=GOLD + (255,))
        paste(img, ln, (W / 2, 820))

    p = prog(t, 0.95, 0.65)
    if p > 0:
        ti = text_img("حالِ خوبِ قدیمی‌ها", "bold", 76, CREAM)
        paste(img, ti, (W / 2, 912 + (1 - ease_out(p)) * 22), alpha=ease_out(p))

    # پیل اسنپ‌فود
    p = prog(t, 2.00, 0.60)
    if p > 0:
        im, _ = SNAP_PILL
        paste(img, im, (W / 2, 1090 + (1 - ease_out(p)) * 20),
              alpha=ease_out(p), scale=0.70 + 0.30 * back_out(p))

    # چیپ‌های پایین
    chips = ["قهوه‌ی دست‌ساز", "غذای گرم", "شیک و دسر"]
    ims = [pill(s, "medium", 33, CREAM, (26, 15, 7), padx=26, pady=13,
                shadow=False)[0] for s in chips]
    gap, total = 14, 0
    total = sum(i.width for i in ims) + gap * (len(ims) - 1)
    x = (W - total) / 2
    for i, im in enumerate(ims):
        pp = prog(t, 3.45 + i * 0.13, 0.42)
        if pp > 0:
            paste(img, im, (x + im.width / 2, 1352 + (1 - ease_out(pp)) * 24),
                  alpha=pp * .95)
        x += im.width + gap
    return finish(img, t, vig=_vig)


# ══════════════════ سکانس ۲ — غذاها ══════════════════
FOOD_CACHE = {}
PHOTO_BOX = (924, 962)
PHOTO_CY = 880
CARD_BOX = (924, 344)
CARD_CY = 1520


def food_assets(i):
    if i in FOOD_CACHE:
        return FOOD_CACHE[i]
    d = DISHES[i]
    raw = Image.open(os.path.join(ROOT, d["img"])).convert("RGB")

    # پس‌زمینه‌ی بلور — بزرگ‌تر از قاب تا لبه‌ی سیاه نبینیم
    bg = fit_cover(raw, (int(W * 1.45), int(H * 1.45))).filter(
        ImageFilter.GaussianBlur(30))

    pc, panc = photo_card(raw, PHOTO_BOX, radius=46, border=0,
                          shadow_op=155, blur=40, spread=(0, 26))

    name = text_img(d["name"], "bold", 62, INK)
    desc = text_img(d["desc"], "regular", 32, INK_SOFT)
    price, _ = pill(money(d["price"]), "bold", 36, INK, GOLD, padx=30, pady=14,
                    shadow=False)
    mark = snap_mark(96)
    lbl = text_img("سفارش از", "medium", 25, MUTED)

    cw, chh = CARD_BOX

    def content(body):
        rx = cw - 44
        paste(body, name, (rx - name.width / 2, 82))
        paste(body, desc, (rx - desc.width / 2, 174))
        # خط جداکننده‌ی مویی
        ImageDraw.Draw(body).line([44, 240, cw - 44, 240],
                                  fill=(238, 224, 205, 255), width=2)
        # پایین: قیمت راست، نشان اسنپ‌فود چپ
        paste(body, price, (rx - price.width / 2, 300))
        paste(body, mark, (72, 300))
        paste(body, lbl, (72 + 52 + 14 + lbl.width / 2, 300))

    card, canc = make_card((cw, chh), radius=40, fill=(255, 251, 245),
                           content=content, shadow=True, shadow_op=155,
                           blur=40, spread=(0, 24))

    tag = None
    if d["tag"]:
        tag, _ = pill(d["tag"], "bold", 33, INK, GOLD, padx=26, pady=12)

    FOOD_CACHE[i] = dict(raw=raw, blur=bg, photo=pc, photo_anchor=panc,
                         card=card, card_anchor=canc, tag=tag)
    return FOOD_CACHE[i]


def scene_food(t):
    i = min(len(DISHES) - 1, int(t / S_FOOD_DUR))
    lt = t - i * S_FOOD_DUR
    a = food_assets(i)
    p = clamp(lt / S_FOOD_DUR)

    z = 1.02 + 0.05 * p
    cw, ch = int(W * z), int(H * z)
    x0 = (a["blur"].width - cw) // 2
    y0 = (a["blur"].height - ch) // 2
    img = a["blur"].crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BICUBIC)
    img = img.convert("RGBA")
    img = Image.blend(img, Image.new("RGBA", (W, H), (24, 13, 6, 255)), 0.60)
    # ورود کوتاه از سیاهی — برش تیز بین آیتم‌ها
    d = clamp((lt - 0.02) / 0.14)
    if d < 1:
        img = Image.blend(Image.new("RGBA", (W, H), (14, 7, 3, 255)), img, d * d)
    img = top_fade(img, 0.26, alpha=175)
    img = bottom_fade(img, 0.66, alpha=150)

    # شماره آیتم — راست بالا
    num = fa(f"{i + 1}") + " / " + fa(f"{len(DISHES)}")
    nb, _ = pill(num, "bold", 32, CREAM, (14, 7, 3), padx=26, pady=12, shadow=False)
    paste(img, nb, (W - MG - nb.width / 2, 262), alpha=0.92)

    # برچسب پیشنهاد ویژه — چپ بالا
    if a["tag"] is not None:
        ptag = prog(lt, 0.16, 0.45)
        if ptag > 0:
            paste(img, a["tag"], (MG + a["tag"].width / 2, 262),
                  alpha=ease_out(ptag), scale=0.85 + 0.15 * back_out(ptag))

    # عنوان کوچک بالای عکس
    pt = prog(lt, 0.04, 0.45)
    if pt > 0:
        hd = text_img("از منوی رترو کافه", "medium", 30, (255, 232, 208))
        paste(img, hd, (W / 2, 352), alpha=ease_out(pt) * .8)

    # کارت عکس
    pp = prog(lt, 0.0, 0.60)
    if pp > 0:
        e = ease_out(pp)
        paste(img, a["photo"], (W / 2, PHOTO_CY + (1 - e) * 30),
              alpha=e, scale=0.92 + 0.08 * e)

    # کارت اطلاعات
    pc = prog(lt, 0.10, 0.55)
    if pc > 0:
        e = ease_out(pc)
        paste(img, a["card"], (W / 2, CARD_CY + (1 - e) * 62), alpha=e)

    # پانویس
    pf = prog(lt, 0.30, 0.50)
    if pf > 0:
        ft = text_img("سفارش آنلاین از اسنپ‌فود", "medium", 30, (255, 228, 200))
        paste(img, ft, (W / 2, 1764), alpha=ease_out(pf) * .70)
    return finish(img, t, vig=_vig_soft)


# ══════════════════ سکانس ۳ — حال‌وهوا ══════════════════
VIBE_CACHE = {}


def vibe_assets(i):
    if i in VIBE_CACHE:
        return VIBE_CACHE[i]
    d = VIBE[i]
    base = load_photo(d["img"], overscan=1.26, max_h=2400)
    VIBE_CACHE[i] = dict(base=base,
                         t1=text_img(d["t1"], "bold", 96, CREAM),
                         t2=text_img(d["t2"], "medium", 41, (255, 236, 212)))
    return VIBE_CACHE[i]


def scene_vibe(t):
    i, acc = 0, 0.0
    for k, d in enumerate(VIBE_DURS):
        if t < acc + d:
            i = k
            break
        acc += d
        i = k
    lt = t - acc
    a = vibe_assets(i)
    p = clamp(lt / VIBE_DURS[i])
    vb = VIBE[i]
    img = ken_burns(a["base"], p, vb["z"][0], vb["z"][1],
                    pan=vb.get("pan", (0.3, 0.2))).convert("RGBA")
    img = Image.blend(img, Image.new("RGBA", (W, H), (60, 30, 12, 255)), 0.10)
    img = ImageEnhance.Brightness(img).enhance(1.22)
    img = ImageEnhance.Contrast(img).enhance(1.06)
    img.alpha_composite(gradient((W, H), [
        (0.0, (20, 10, 4, 54)), (0.42, (20, 10, 4, 100)),
        (0.68, (20, 10, 4, 198)), (1.0, (20, 10, 4, 238))]))

    e3 = ease_out(prog(lt, 0.18, 0.40))
    if e3 > 0:
        ln = Image.new("RGBA", (max(4, int(78 * e3)), 8), (0, 0, 0, 0))
        ImageDraw.Draw(ln).rounded_rectangle([0, 0, ln.width - 1, 7], radius=4,
                                             fill=GOLD + (255,))
        paste(img, ln, (W / 2, 1368))

    e = ease_out(prog(lt, 0.06, 0.45))
    paste(img, a["t1"], (W / 2, 1452 - (1 - e) * 26), alpha=e)
    e2 = ease_out(prog(lt, 0.16, 0.45))
    paste(img, a["t2"], (W / 2, 1556 - (1 - e2) * 20), alpha=e2 * .95)
    return finish(img, t, vig=_vig_soft)


# ══════════════════ سکانس ۴ — رونمایی همکاری ══════════════════
REVEAL_CACHE = {}


def reveal_assets():
    if REVEAL_CACHE:
        return REVEAL_CACHE
    bg = Image.new("RGBA", (W, H), CREAM + (255,))
    bg.alpha_composite(sunburst((W, H), (W / 2, H * 0.36), GOLD, alpha=22, rays=40))
    bg.alpha_composite(stripes((W, H), RED, alpha=5, step=30))
    bg = glow(bg, [-W * .3, H * .02, W * 1.3, H * .62], color=(255, 200, 110), a=110,
              blur=170)
    bg = glow(bg, [-W * .2, H * .70, W * 1.2, H * 1.1], color=(255, 150, 200), a=40,
              blur=160)

    badge, _ = pill("همکاری جدید", "bold", 38, INK, GOLD, padx=32, pady=15)
    lm = logo_mark(210)
    h1a = text_img("حالا رترو کافه", "bold", 84, INK)
    h1b = text_img("روی اسنپ‌فود", "bold", 84, RED_DEEP)
    sub = text_img("سفارش آنلاین، ارسال تا درِ خانه", "medium", 43, INK_SOFT)
    band_t = text_img("تحویل سریع با پیک اسنپ‌فود", "bold", 40, WHITE)
    # نوار سه عکس گرد از منو — پایان‌بندی خوشمزه
    thumbs = []
    for d in (DISHES[0], DISHES[2], DISHES[5]):
        raw = Image.open(os.path.join(ROOT, d["img"])).convert("RGB")
        th, _ = photo_card(raw, (192, 192), radius=96, border=7,
                           border_color=(255, 249, 240), shadow_op=110,
                           blur=26, spread=(0, 12))
        thumbs.append(th)
    REVEAL_CACHE.update(bg=bg, badge=badge, logo=lm, h1a=h1a, h1b=h1b, sub=sub,
                        band_t=band_t, thumbs=thumbs)
    return REVEAL_CACHE


def scene_reveal(t, T):
    a = reveal_assets()
    img = a["bg"].copy()

    p = prog(t, 0.05, 0.45)
    if p > 0:
        paste(img, a["badge"], (W / 2, 322), alpha=ease_out(p),
              scale=0.72 + 0.28 * back_out(p))

    p4 = prog(t, 0.30, 0.55)
    if p4 > 0:
        paste(img, a["h1a"], (W / 2, 940 + (1 - ease_out(p4)) * 40), alpha=ease_out(p4))
    p5 = prog(t, 0.48, 0.55)
    if p5 > 0:
        paste(img, a["h1b"], (W / 2, 1060 + (1 - ease_out(p5)) * 40), alpha=ease_out(p5))
    p6 = prog(t, 1.00, 0.55)
    if p6 > 0:
        paste(img, a["sub"], (W / 2, 1178 + (1 - ease_out(p6)) * 26), alpha=ease_out(p6))

    # پیل «تحویل سریع با پیک» — پایین صفحه
    p7 = prog(t, 1.55, 0.50)
    if p7 > 0:
        e = ease_out(p7)
        ct, _ = pill("تحویل سریع با پیک اسنپ‌فود", "bold", 38, WHITE, SNAP,
                     padx=40, pady=20)
        paste(img, ct, (W / 2, 1300 + (1 - e) * 24), alpha=e,
              scale=0.84 + 0.16 * back_out(p7))
    p8 = prog(t, 1.95, 0.50)
    if p8 > 0:
        f = text_img("داخل منوی دیجیتال کافه هم پیدایش می‌کنی", "medium", 31, MUTED)
        paste(img, f, (W / 2, 1418 + (1 - ease_out(p8)) * 18), alpha=ease_out(p8) * .95)

    # ردیف لوگوها: اسنپ‌فود چپ، رترو راست (RTL) — دقیقاً روی جمله‌ی «رترو کافه، روی اسنپ‌فود»
    cy = 632
    p1 = prog(t, 2.62, 0.55)
    if p1 > 0:
        e = back_out(p1)
        paste(img, a["logo"], (W / 2 + 252 + (1 - e) * 170, cy),
              alpha=ease_out(p1), scale=0.78 + 0.22 * e)
    p2 = prog(t, 3.05, 0.55)
    if p2 > 0:
        e = back_out(p2)
        im, _ = SNAP_PILL
        paste(img, im, (W / 2 - 232 - (1 - e) * 190, cy),
              alpha=ease_out(p2), scale=(0.78 + 0.22 * e) * 0.92)
    p3 = prog(t, 3.62, 0.42)
    if p3 > 0:
        xs = text_img("×", "brand", 92, RED, rtl=False)
        paste(img, xs, (W / 2, cy - 8), alpha=ease_out(p3),
              scale=(0.45 + 0.55 * back_out(p3)) * (1 + 0.035 * math.sin(t * 5)))

    # سه عکس گرد منو در پایین
    for k, th in enumerate(a["thumbs"]):
        pt = prog(t, 3.95 + k * 0.16, 0.50)
        if pt > 0:
            e = back_out(pt)
            paste(img, th, (W / 2 + (k - 1) * 250, 1642 - (1 - ease_out(pt)) * 26),
                  alpha=ease_out(pt), scale=0.72 + 0.28 * e)

    for sx, sy, sd in [(196, 462, 2.75), (892, 448, 3.15), (238, 1112, 4.25),
                       (858, 1112, 4.45)]:
        p = prog(t, sd, 0.6)
        if 0 < p < 1:
            r = 7 + 11 * math.sin(p * math.pi)
            st = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
            dd = ImageDraw.Draw(st)
            dd.line([(40, 40 - r * 2.1), (40, 40 + r * 2.1)], fill=GOLD + (255,), width=5)
            dd.line([(40 - r * 2.1, 40), (40 + r * 2.1, 40)], fill=GOLD + (255,), width=5)
            paste(img, st, (sx, sy), alpha=math.sin(p * math.pi))
    return finish(img, t, vig=None)


# ══════════════════ سکانس ۵ — پایان و فراخوان ══════════════════
OUTRO_CACHE = {}


def outro_assets():
    if OUTRO_CACHE:
        return OUTRO_CACHE
    bg = gradient((W, H), [(0.0, (222, 74, 47, 255)), (0.45, RED_DEEP + (255,)),
                           (1.0, (124, 32, 21, 255))]).convert("RGBA")
    bg.alpha_composite(sunburst((W, H), (W / 2, H * 0.26), GOLD, alpha=26, rays=44))
    bg = glow(bg, [-W * .3, -H * .25, W * 1.3, H * .5], color=(255, 205, 120), a=95,
              blur=170)

    lm = logo_mark(230)
    brand = text_img("RETRO CAFE", "brand", 72, GOLD, tracking=5, rtl=False)
    cta = text_img("همین حالا سفارش بده", "bold", 80, CREAM)

    cw, chh = 928, 424

    def content(body):
        rows = [("pin", "آدرس", "نسیم شهر، خیابان اصلی، جنب درمانگاه قائم", 28),
                ("instagram", "اینستاگرام", "@Caferetro_ir", 33),
                ("phone", "تماس", "۰۹۳۶۹۱۹۲۲۹۷", 33)]
        y = 26
        d = ImageDraw.Draw(body)
        for k, (kind, label, val, vs) in enumerate(rows):
            if k:
                d.line([34, y - 4, cw - 34, y - 4], fill=(238, 224, 205, 255), width=2)
            ic = icon(kind, 52, RED_DEEP)
            paste(body, ic, (cw - 32 - 26, y + 54))
            lb = text_img(label, "medium", 26, MUTED)
            vv = text_img(val, "bold", vs, INK)
            paste(body, lb, (cw - 104 - lb.width / 2, y + 30))
            paste(body, vv, (cw - 104 - vv.width / 2, y + 78))
            y += 118

    infocard, canc = make_card((cw, chh), radius=38, fill=(255, 249, 240),
                               content=content, shadow_op=130, blur=40,
                               spread=(0, 24))

    hours = dict(
        ic=icon("clock", 40, GOLD),
        t=text_img("هر روز، ۱۰ صبح تا ۱۰ شب", "medium", 32, (255, 236, 214)),
    )
    OUTRO_CACHE.update(bg=bg, lm=lm, brand=brand, cta=cta, infocard=infocard,
                       hours=hours,
                       info_anchor=(cw / 2, chh / 2))
    return OUTRO_CACHE


def scene_outro(t, T):
    a = outro_assets()
    img = a["bg"].copy()

    p = prog(t, 0.15, 0.62)
    if p > 0:
        paste(img, a["lm"], (W / 2, 396), alpha=ease_out(p),
              scale=0.70 + 0.30 * back_out(p))
    p = prog(t, 0.45, 0.58)
    if p > 0:
        paste(img, a["brand"], (W / 2, 566 + (1 - ease_out(p)) * 20), alpha=ease_out(p))
    p = prog(t, 1.30, 0.60)
    if p > 0:
        paste(img, a["cta"], (W / 2, 676 + (1 - ease_out(p)) * 26), alpha=ease_out(p))
    p = prog(t, 1.65, 0.55)
    if p > 0:
        im, _ = SNAP_PILL
        paste(img, im, (W / 2, 800), alpha=ease_out(p),
              scale=0.74 + 0.26 * back_out(p))

    p = prog(t, 2.90, 0.68)
    if p > 0:
        e = ease_out(p)
        paste(img, a["infocard"], (W / 2, 1300 + (1 - e) * 64), alpha=e)

    p = prog(t, 3.35, 0.55)
    if p > 0:
        e = ease_out(p)
        h = a["hours"]
        gw = h["ic"].width + 14 + h["t"].width
        gx = (W - gw) / 2
        paste(img, h["ic"], (gx + h["ic"].width / 2, 1562 + (1 - e) * 16), alpha=e * .95)
        paste(img, h["t"], (gx + h["ic"].width + 14 + h["t"].width / 2,
                            1562 + (1 - e) * 16), alpha=e * .95)

    p = prog(t, 2.25, 0.55)
    if p > 0:
        lab = text_img("منوی دیجیتال:", "medium", 27, (255, 224, 192))
        url = text_img("10to1000k.github.io/retro-cafe", "bold", 30, CREAM, rtl=False)
        gap = 12
        total = url.width + gap + lab.width
        alpha = ease_out(p) * .92
        # RTL: برچسب راست، آدرس چپ
        paste(img, lab, (W / 2 + total / 2 - lab.width / 2, 1656), alpha=alpha * .95)
        paste(img, url, (W / 2 - total / 2 + url.width / 2, 1656), alpha=alpha)

    # فلش پایین
    p = prog(t, 4.60, 0.5)
    if 0 < p:
        bob = math.sin(t * 3.2) * 8
        ar = Image.new("RGBA", (70, 70), (0, 0, 0, 0))
        ImageDraw.Draw(ar).polygon([(35, 52), (12, 20), (58, 20)], fill=GOLD + (255,))
        paste(img, ar, (W / 2, 1740 + bob), alpha=ease_out(p) * .85)
    return finish(img, t, vig=None)


# ══════════════════ ترکیب ══════════════════
SCENES = [
    (S_INTRO, lambda lt, T: scene_intro(lt, T)),
    (S_FOOD, lambda lt, T: scene_food(lt)),
    (S_VIBE, lambda lt, T: scene_vibe(lt)),
    (S_REVEAL, lambda lt, T: scene_reveal(lt, T)),
    (S_OUTRO, lambda lt, T: scene_outro(lt, T)),
]


def render_frame(t):
    cur = len(SCENES) - 1
    for i, (sc, fn) in enumerate(SCENES):
        if sc["start"] <= t < sc["start"] + sc["dur"]:
            cur = i
            break
    sc, fn = SCENES[cur]
    img = fn(t - sc["start"], sc["dur"])

    end = sc["start"] + sc["dur"]
    if cur + 1 < len(SCENES) and t > end - XFADE:
        p = (t - (end - XFADE)) / XFADE
        sc2, fn2 = SCENES[cur + 1]
        img2 = fn2(t - sc2["start"], sc2["dur"])
        img = Image.blend(img, img2, ease_in_out(p))
    return img.convert("RGB")


def still(times, outdir=None):
    outdir = outdir or os.path.join(BUILD, "stills")
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for t in times:
        p = os.path.join(outdir, f"still_{t:05.2f}.png")
        render_frame(t).save(p, optimize=True)
        paths.append(p)
        print(p)
    return paths


def ffmpeg_path():
    ff = shutil.which("ffmpeg")
    if ff:
        return ff
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def video(out_path=None, audio=True):
    out_path = out_path or os.path.join(HERE, "retro-cafe-snappfood-reel.mp4")
    ff = ffmpeg_path()
    n = int(round(TOTAL * FPS))
    wav = os.path.join(BUILD, "mix.wav")
    has_audio = audio and os.path.exists(wav)

    cmd = [ff, "-hide_banner", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-"]
    if has_audio:
        cmd += ["-i", wav]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
            "-g", str(FPS * 2), "-movflags", "+faststart"]
    if has_audio:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += [out_path]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    try:
        for f in range(n):
            t = f / FPS
            proc.stdin.write(render_frame(t).tobytes())
            if f % 45 == 0:
                print(f"\r[render] {f}/{n} ({t:5.2f}s)", end="", file=sys.stderr, flush=True)
    finally:
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        proc.wait()
    print(f"\n[done] {out_path}", file=sys.stderr)
    if proc.returncode != 0:
        print(err[-3000:], file=sys.stderr)
        raise SystemExit(proc.returncode)
    return out_path


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "still":
        still([float(x) for x in args[1:]])
    else:
        video()
