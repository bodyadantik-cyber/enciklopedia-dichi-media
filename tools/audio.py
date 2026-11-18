"""Music/SFX bed for a spec: python3 audio.py SPEC.json bed.wav
Dark drone pad + rumble, riser before each boom, boom hits, whooshes at scene cuts,
heartbeat in the last scene. Then mix with mix.sh (voice ducks the bed)."""
import sys, json, wave
import numpy as np
from numpy.fft import rfft, irfft, rfftfreq

spec = json.load(open(sys.argv[1], encoding="utf-8"))
SR = 48000; TOT = spec["total"]; N = int(SR * TOT)
t = np.arange(N) / SR
rng = np.random.default_rng(3)

def filt(x, lo=None, hi=None):
    X = rfft(x); f = rfftfreq(len(x), 1 / SR); m = np.ones_like(f)
    if hi: m *= 1 / (1 + (f / hi) ** 4)
    if lo: m *= 1 - 1 / (1 + (f / lo) ** 4)
    return irfft(X * m, len(x))

noise = rng.normal(0, 1, N)
rumble = filt(noise, hi=120) * 3
env = np.clip(t / 2.0, 0, 1) * np.clip((TOT - t) / 2.5, 0, 1)
out = np.zeros(N)
for fr, amp in [(55, 0.5), (82.41, 0.3), (110, 0.25), (130.81, 0.15), (164.8, 0.08)]:
    lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * t + fr)
    out += amp * lfo * np.sin(2 * np.pi * fr * t + 0.3 * np.sin(2 * np.pi * 0.2 * t))
out = out * 0.18 * env + rumble * 0.05 * env
hiss = filt(noise, lo=300, hi=3000)
crack = filt(noise, hi=2500)
for b in spec.get("booms", []):
    if b > 2:
        out += hiss * 0.05 * np.exp(-((t - b) / 2.5) ** 2) * (t < b)
    m = (t >= b) & (t < b + 4); tt = t[m] - b
    g = 0.6 if b < 0.5 else 1.0
    out[m] += g * (np.sin(2 * np.pi * (45 + 60 * np.exp(-tt * 8)) * tt) * np.exp(-tt * 1.3) * 0.9
                   + crack[m] * np.exp(-tt * 9) * 1.5 + rumble[m] * np.exp(-tt * 0.9) * 4)
wh = filt(noise, lo=400, hi=5000)
for sc in spec["scenes"][1:]:
    c = sc[0]
    if any(abs(c - b) < 0.6 for b in spec.get("booms", [])):
        continue
    m = (t > c - 0.6) & (t < c + 0.3); tt = t[m] - (c - 0.6)
    out[m] += wh[m] * np.sin(np.pi * tt / 0.9) ** 2 * 0.08
for lab in spec.get("labels", []):
    c = lab[0] + 0.05
    m = (t >= c) & (t < c + 0.6); tt = t[m] - c
    out[m] += np.sin(2 * np.pi * 60 * tt) * np.exp(-tt * 10) * 0.4
last = spec["scenes"][-1][0]
for k in range(4):
    for d in (0, 0.28):
        c = last + 0.15 + k * 1.0 + d
        m = (t >= c) & (t < c + 0.4); tt = t[m] - c
        out[m] += np.sin(2 * np.pi * 50 * tt) * np.exp(-tt * 14) * 0.45
out = out / np.max(np.abs(out)) * 0.9
st = (np.stack([out, out], 1) * 32767).astype(np.int16)
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
