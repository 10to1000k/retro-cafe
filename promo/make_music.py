# -*- coding: utf-8 -*-
"""
ساخت موسیقی پس‌زمینه‌ی تبلیغ — لوپ گرم و رترو (بدون نمونه‌ی بیرونی)
خروجی: promo/build/music.wav  (44.1kHz, استریو)
"""
import math
import os
import wave
import numpy as np

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "music.wav")
DUR = 36.9             # هم‌طول با ویدئو
rng = np.random.default_rng(7)


def note_hz(name):
    names = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6,
             "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
    n, octv = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[n] + 12 * (octv - 4) - 9) / 12)


def env_ad(n, a, d, sr=SR):
    """AD envelope"""
    a = max(1, int(a * sr))
    d = max(1, int(d * sr))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    tail = np.exp(-np.linspace(0, 4, d))
    e[a:] = tail[: n - a] if len(tail) >= n - a else np.pad(tail, (0, n - a - len(tail)))
    return e


def pluck(freq, dur, amp=0.2, bright=0.5):
    """صدای شبیه گیتار/پیانوی گرم (جمع هارمونیک‌ها با فروپاشی سریع)"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k, (h, a) in enumerate([(1, 1.0), (2, .45), (3, .22), (4, .12), (5, .06)]):
        decay = 2.6 + k * 1.5 + (1 - bright) * 2
        out += a * np.sin(2 * np.pi * freq * h * t) * np.exp(-decay * t)
    out *= env_ad(n, 0.006, min(dur, 1.2))
    return out * amp


def bell(freq, dur, amp=0.12):
    n = int(dur * SR)
    t = np.arange(n) / SR
    m = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2.01 * t) \
        + 0.22 * np.sin(2 * np.pi * freq * 3.02 * t)
    return m * np.exp(-3.4 * t) * amp * env_ad(n, 0.004, dur)


def bass(freq, dur, amp=0.30):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.sin(2 * np.pi * freq * t) + 0.28 * np.sin(2 * np.pi * freq * 2 * t)
    return out * np.exp(-1.5 * t) * amp * env_ad(n, 0.012, dur)


def pad(freqs, dur, amp=0.055):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        out += np.sin(2 * np.pi * f * t + rng.uniform(0, 6))
        out += 0.5 * np.sin(2 * np.pi * f * 1.003 * t)     # دیتون نرم
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.22 * t)
    e = np.minimum(1, t / 0.9) * np.minimum(1, (dur - t) / 0.9).clip(0, 1)
    return out / len(freqs) * lfo * e * amp


def kick(amp=0.34):
    n = int(0.30 * SR)
    t = np.arange(n) / SR
    f = 118 * np.exp(-9 * t) + 46
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-11 * t) * amp


def snap(amp=0.12):
    """اسنپ/کلاپ نرم با نویز باند‌محدود"""
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    # فیلتر ساده‌ی بالاگذر
    hp = np.diff(np.concatenate([[0], noise]))
    return hp * np.exp(-38 * t) * amp


def hat(amp=0.045, dec=52):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    return rng.normal(0, 1, n) * np.exp(-dec * t) * amp


def vinyl(dur, amp=0.012):
    n = int(dur * SR)
    noise = rng.normal(0, 1, n)
    # باند‌پس ساده (میانگین متحرک)
    k = 24
    kern = np.ones(k) / k
    noise = np.convolve(noise, kern, mode="same")
    # ترک‌های تصادفی صفحه
    clicks = np.zeros(n)
    for pos in rng.choice(n, int(dur * 2.2), replace=False):
        L = rng.integers(40, 140)
        if pos + L < n:
            clicks[pos:pos + L] += rng.normal(0, 1, L) * np.linspace(1, 0, L)
    return (noise * 0.5 + clicks * 0.35) * amp


# ── آهنگ: Am – F – C – G  (لوپ ۴ ثانیه‌ای، ۹۰ bpm) ──
BEAT = 60 / 92
BAR = BEAT * 4
CHORDS = [
    ("A2", ["A3", "C4", "E4"], "A4"),
    ("F2", ["F3", "A3", "C4"], "C4"),
    ("C3", ["C4", "E4", "G4"], "E4"),
    ("G2", ["G3", "B3", "D4"], "D4"),
]

n_total = int(DUR * SR)
L = np.zeros(n_total)
R = np.zeros(n_total)


def clamp_pan(p):
    return max(-1.0, min(1.0, p))


def add(sig, at, pan=0.0, gain=1.0):
    start = int(at * SR)
    if start >= n_total:
        return
    s = sig[: n_total - start] * gain
    ang = (clamp_pan(pan) + 1) * math.pi / 4      # equal-power pan
    gl, gr = math.cos(ang), math.sin(ang)
    L[start:start + len(s)] += s * gl
    R[start:start + len(s)] += s * gr


def add_st(sig_l, sig_r, at, gain=1.0):
    start = int(at * SR)
    if start >= n_total:
        return
    m = min(len(sig_l), n_total - start)
    L[start:start + m] += sig_l[:m] * gain
    R[start:start + m] += sig_r[:m] * gain


# پد زمینه (کل طول)
b = 0.0
bi = 0
while b < DUR:
    root, triad, _ = CHORDS[bi % 4]
    freqs = [note_hz(n) for n in triad] + [note_hz(root) * 2]
    p = pad(freqs, min(BAR * 1.15, DUR - b + 0.4), amp=0.070)
    add(p, b, pan=0.0, gain=0.9)
    b += BAR
    bi += 1

# آرپژ + ملودی
b = 0.0
bi = 0
while b < DUR:
    root, triad, top = CHORDS[bi % 4]
    # آرپژ هشتم
    seq = [triad[0], triad[2], triad[1], triad[2], triad[0], triad[2], triad[1], triad[2]]
    for k, nm in enumerate(seq):
        at = b + k * BEAT / 2
        if at >= DUR:
            break
        add(pluck(note_hz(nm) * 2, 1.1, amp=0.085, bright=0.6), at,
            pan=-0.28 if k % 2 else 0.28)
    # ملودی بالای آرپژ
    mel = [top, None, triad[2], None, None, top, None, triad[1]]
    for k, nm in enumerate(mel):
        if nm is None:
            continue
        at = b + k * BEAT / 2 + 0.0
        if at >= DUR:
            break
        add(bell(note_hz(nm) * 2, 1.4, amp=0.052), at, pan=0.12)
    # بیس
    add(bass(note_hz(root) , BEAT * 1.7, amp=0.20), b)
    add(bass(note_hz(root), BEAT * 0.9, amp=0.13), b + BEAT * 2.4)
    b += BAR
    bi += 1

# درام نرم — از ثانیه ۴ وارد می‌شود، قبلش فقط تنه
beat_t = 0.0
k = 0
while beat_t < DUR:
    if beat_t >= 3.9:
        if k % 4 == 0:
            add(kick(0.30), beat_t, pan=0.0)
        if k % 4 == 2:
            add(snap(0.085), beat_t, pan=0.06)
        add(hat(0.030 if k % 2 == 0 else 0.020), beat_t, pan=0.18)
        add(hat(0.016, 70), beat_t + BEAT / 2, pan=-0.22)
    beat_t += BEAT
    k += 1

# صدای صفحه گرامافون در کل
v = vinyl(DUR, amp=0.020)
add(v, 0.0, pan=0.0)

# ── میکس و مسترینگ ──
mix = np.stack([L, R], axis=1)
# فیلتر گرم‌کننده‌ی ملایم (کمی کاهش تیزی)
k = 3
mix = np.apply_along_axis(lambda ch: np.convolve(ch, np.ones(k) / k, mode="same"), 0, mix)
# فید ورود/خروج
n = mix.shape[0]
fi = int(0.9 * SR)
fo = int(1.9 * SR)
env = np.ones(n)
env[:fi] = np.linspace(0, 1, fi) ** 1.6
env[-fo:] = np.linspace(1, 0, fo) ** 1.8
mix *= env[:, None]
# نرمال‌سازی + کمی گرمای تیوب
peak = np.max(np.abs(mix))
mix = mix / max(1e-9, peak) * 0.97
mix = np.tanh(mix * 1.25) * 0.92
mix *= 32767

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(mix.astype(np.int16).tobytes())
print("wrote", OUT, f"{DUR}s")
