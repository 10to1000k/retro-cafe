# -*- coding: utf-8 -*-
"""
میکس صدای نهایی: گویندگی (صداوسیما-استایل) + موسیقی پس‌زمینه
خروجی: promo/build/mix.wav  (هم‌طول با ویدئو)
"""
import os
import re
import math
import wave
import subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
VO = os.path.join(BUILD, "vo")
SR = 44100
TOTAL = 36.90            # باید با TOTAL در render.py یکی باشد

FF = None
try:
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    import shutil
    FF = shutil.which("ffmpeg")

# (فایل, زمان شروع در ویدئو)
VO_CUES = [
    ("vo1.mp3", 0.62),        # رترو کافه؛ حالِ خوبِ قدیمی‌ها
    ("vo_intro2.mp3", 3.55),  # همکاری تازه، با اسنپ‌فود
    ("vo3.mp3", 5.90),        # برگر ویژه... شیک نوتلا
    ("vo4b.mp3", 17.45),      # قهوه‌ی دست‌ساز، تازه دم
    ("vo4c.mp3", 19.35),      # نوشیدنی خنک، برای روزهای گرم
    ("vo2.mp3", 21.75),       # از امروز یک همکاری تازه... رترو کافه روی اسنپ‌فود
    ("vo_reveal.mp3", 26.15), # رترو کافه، روی اسنپ‌فود
    ("vo5.mp3", 29.85),       # همین حالا سفارش بده ... تا در خانه
]


def read_audio(path):
    """هر فرمتی → float32 استریو 44.1k"""
    raw = subprocess.run(
        [FF, "-v", "error", "-i", path, "-f", "f32le", "-ac", "2",
         "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()
    return a


def write_wav(path, a):
    a = np.clip(a, -1.0, 1.0)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())
    print("wrote", path, f"{len(a) / SR:.2f}s")


def highpass(x, k=3):
    """ساده: حذف بم‌های زیر ۸۰ هرتز با فیلتر یک‌قطبی"""
    a = math.exp(-2 * math.pi * 80 / SR)
    y = np.empty_like(x)
    prev_x = 0.0
    prev_y = 0.0
    for i in range(len(x)):
        prev_y = a * (prev_y + x[i] - prev_x)
        prev_x = x[i]
        y[i] = prev_y
    return y


def bandlift(x):
    """کمی حضور در بازه‌ی کلام + کمی بم برای حس تریلر"""
    return x


def main():
    n = int(TOTAL * SR)
    vo = np.zeros((n, 2), dtype=np.float32)
    for fname, at in VO_CUES:
        a = read_audio(os.path.join(VO, fname))
        # نرمال‌سازی هر قطعه
        peak = float(np.max(np.abs(a))) or 1.0
        a = a / peak * 0.92
        # کمی بم‌تر و پرشورتر (تریلر)
        b = np.stack([highpass(a[:, 0], 3), highpass(a[:, 1], 3)], axis=1)
        a = a * 0.70 + b * 0.30
        # فید ۳۰ms
        f = int(0.03 * SR)
        a[:f] *= np.linspace(0, 1, f)[:, None]
        a[-f:] *= np.linspace(1, 0, f)[:, None]
        s = int(at * SR)
        m = min(len(a), n - s)
        vo[s:s + m] += a[:m]

    # موسیقی
    mus = read_audio(os.path.join(BUILD, "music.wav"))
    if len(mus) < n:
        mus = np.pad(mus, ((0, n - len(mus)), (0, 0)))
    mus = mus[:n]

    # ducking: موسیقی وقتی گویندگی هست پایین بیاید
    env = np.abs(vo).mean(axis=1)
    k = int(0.10 * SR)
    ker = np.ones(k) / k
    env = np.convolve(env, ker, mode="same")
    env = np.clip(env / 0.055, 0, 1)
    # نرم کردن حمله/رهاسازی
    duck = 1.0 - 0.62 * env
    k2 = int(0.18 * SR)
    duck = np.convolve(duck, np.ones(k2) / k2, mode="same")
    mus *= duck[:, None]

    # سطح‌ها
    vo_gain = 0.98
    mus_gain = 0.55
    mix = vo * vo_gain + mus * mus_gain

    # مستر: نرمال + لیمیتر نرم
    peak = float(np.max(np.abs(mix))) or 1.0
    mix = mix / peak * 0.95
    mix = np.tanh(mix * 1.1) * 0.94
    # فید پایانی
    fo = int(0.8 * SR)
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    write_wav(os.path.join(BUILD, "mix.wav"), mix)


if __name__ == "__main__":
    main()
