"""Generic vertical-video renderer for «Энциклопедия дичи».

Usage:
  python3 render.py SPEC.json stills 0.5 7.0 14.2      # preview frames -> still_XX.jpg
  python3 render.py SPEC.json render START END out.mp4 # frames [START, END) at 30 fps

SPEC.json (all times in seconds, image paths relative to the spec file):
{
  "total": 52.0,                       # video length (voice length + ~2 s end card)
  "images": {"1": "img_01.png", ...},  # vertical images (9:16, any size >= 864x1536)
  "segments": [[s, e, [["WORD", "spoken form", hl], ...]], ...],
        # one entry per spoken phrase (from silencedetect); display words UPPERCASE,
        # numbers as digits ("1883"), spoken form used only for timing weight, hl=true -> yellow
  "scenes": [[s, e, img, zoom0, zoom1, [fx0, fy0], [fx1, fy1]], ...],
        # Ken Burns per scene; zoom 1.0..1.5; focus points normalized 0..1
  "labels": [[s, e, "TEXT", size, "red"|"dark"|"yellow"], ...],   # top plaques (y=260)
  "counters": [[s, e, t_anim_start, t_anim_dur, value, "fmt {} КМ", "subtitle"]],
  "booms": [t, ...],                   # flash + camera shake + chroma split
  "rings": [[s, e]],                   # optional expanding shock rings over the frame centre
  "end": {"t": 49.9, "l1": "ЧТО РАЗОБРАТЬ ДАЛЬШЕ?", "l2": "ПИШИ В КОММЕНТАХ"}
}
"""
import sys, os, math, subprocess, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf"

SPEC_PATH = sys.argv[1]
SPEC = json.load(open(SPEC_PATH, encoding="utf-8"))
BASE = os.path.dirname(os.path.abspath(SPEC_PATH))
TOTAL = SPEC["total"]

def font(size, weight="Black"):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f

# ---------------- captions timing ----------------
WORDS, CHUNKS = [], []
for (s, e, toks) in SPEC["segments"]:
    weights = [len(t[1].replace(" ", "")) + 2 for t in toks]
    tot = sum(weights)
    t = s
    idxs = []
    for tok, w in zip(toks, weights):
        d = (e - s) * w / tot
        WORDS.append([t, t + d, tok[0], bool(tok[2])])
        idxs.append(len(WORDS) - 1)
        t += d
    cur = []
    for i in idxs:
        txt = " ".join(WORDS[j][2] for j in cur + [i])
        if cur and (len(cur) >= 3 or len(txt) > 17):
            CHUNKS.append(cur); cur = []
        cur.append(i)
    if cur:
        CHUNKS.append(cur)
CHUNK_T = [(WORDS[c[0]][0], WORDS[c[-1]][1]) for c in CHUNKS]
END_T = SPEC.get("end", {}).get("t", TOTAL)
BOOMS = SPEC.get("booms", [])
SCENES = SPEC["scenes"]
XF = 0.25

SRC = {}
VIDEOS = SPEC.get("videos", {})   # {"v1": {"file": "clip.mp4", "speed": 1.0}} -> scene img key "v1"
VFRAMES = {}
def video_frames(key):
    if key not in VFRAMES:
        path = os.path.join(BASE, VIDEOS[key]["file"])
        d = path + ".frames"
        if not os.path.isdir(d) or not os.listdir(d):
            os.makedirs(d, exist_ok=True)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-vf", f"fps={FPS}",
                            "-q:v", "2", os.path.join(d, "f_%04d.jpg")], check=True)
        VFRAMES[key] = sorted(os.path.join(d, f) for f in os.listdir(d))
    return VFRAMES[key]

def load(i, trel=None):
    i = str(i)
    if i in VIDEOS:
        fr = video_frames(i)
        n = int((trel or 0) * VIDEOS[i].get("speed", 1.0) * FPS)
        n = min(max(n, 0), len(fr) - 1)
        key = (i, n)
        if key not in SRC:
            if len(SRC) > 40:
                for k in [k for k in SRC if isinstance(k, tuple)][:20]:
                    del SRC[k]
            SRC[key] = prep(Image.open(fr[n]).convert("RGB"))
        return SRC[key]
    if i not in SRC:
        SRC[i] = prep(Image.open(os.path.join(BASE, SPEC["images"][i])).convert("RGB"))
    return SRC[i]

def prep(im):
    if True:
        iw, ih = im.size
        # cover-crop to 9:16
        tr = W / H
        if iw / ih > tr:
            nw = int(ih * tr); im = im.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
        else:
            nh = int(iw / tr); im = im.crop((0, (ih - nh) // 2, iw, (ih - nh) // 2 + nh))
        im = im.resize((int(W * 1.5), int(H * 1.5)), Image.LANCZOS)
        a = np.asarray(im).astype(np.float32) / 255.0
        a = np.clip((a - 0.5) * 1.12 + 0.5, 0, 1)
        lum = a.mean(axis=2, keepdims=True)
        a = a * 0.9 + lum * 0.1
        a[..., 0] = np.clip(a[..., 0] * 1.04, 0, 1)
        a[..., 2] = np.clip(a[..., 2] * 0.98, 0, 1)
        return Image.fromarray((a * 255).astype(np.uint8))

def ease(x):
    x = min(max(x, 0), 1); return 0.5 - 0.5 * math.cos(math.pi * x)

def ease_out(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3

def scene_frame(sc, t, shake=(0, 0)):
    s, e, img, z0, z1, f0, f1 = sc
    pe = ease((t - s) / (e - s))
    z = z0 + (z1 - z0) * pe + 0.06 * max(0, 1 - (t - s) / 0.35) ** 2
    src = load(img, t - s)
    sw, sh = src.size
    cw, ch = W * 1.5 / z, H * 1.5 / z
    cx = (f0[0] + (f1[0] - f0[0]) * pe) * sw + shake[0] * 1.5
    cy = (f0[1] + (f1[1] - f0[1]) * pe) * sh + shake[1] * 1.5
    x0 = min(max(cx - cw / 2, 0), sw - cw)
    y0 = min(max(cy - ch / 2, 0), sh - ch)
    return np.asarray(src.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))).astype(np.float32)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
VIG = np.clip(1.15 - 0.45 * r ** 2, 0.35, 1.0)[..., None]
BAND = (1 - 0.35 * np.exp(-((yy - 1180) / 260) ** 2))[..., None]
rng = np.random.default_rng(1)
GRAIN = [np.kron(rng.normal(0, 7, (H // 2, W // 2)).astype(np.float32), np.ones((2, 2), np.float32))[..., None] for _ in range(6)]

FC = font(96, "Black")
CHUNK_CACHE = {}
def render_chunk(ci, active):
    key = (ci, active)
    if key in CHUNK_CACHE:
        return CHUNK_CACHE[key]
    words = [WORDS[j] for j in CHUNKS[ci]]
    space = 26
    sizes = [FC.getbbox(w[2]) for w in words]
    widths = [b[2] - b[0] for b in sizes]
    lines, cur, cw = [], [], 0
    for k, wd in enumerate(widths):
        if cur and cw + space + wd > 920:
            lines.append(cur); cur, cw = [], 0
        cw = cw + (space if cur else 0) + wd
        cur.append(k)
    lines.append(cur)
    lh = 118
    img = Image.new("RGBA", (W, lh * len(lines) + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for li, ln in enumerate(lines):
        tw = sum(widths[k] for k in ln) + space * (len(ln) - 1)
        x = (W - tw) / 2
        y = 30 + li * lh
        for k in ln:
            w = words[k]; j = CHUNKS[ci][k]
            if j == active:
                col = (255, 70, 40) if w[3] else (255, 214, 0)
            elif w[3]:
                col = (255, 214, 0)
            else:
                col = (255, 255, 255)
            d.text((x - sizes[k][0], y), w[2], font=FC, fill=col, stroke_width=9, stroke_fill=(0, 0, 0))
            x += widths[k] + space
    sh = img.split()[3].filter(ImageFilter.GaussianBlur(10))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow.putalpha(sh.point(lambda v: int(v * 0.6)))
    out = Image.alpha_composite(shadow, img)
    CHUNK_CACHE[key] = out
    return out

def overlay(base, rgba, x, y, scale=1.0, alpha=1.0):
    if scale != 1.0:
        ow, oh = rgba.width, rgba.height
        nw, nh = int(ow * scale), int(oh * scale)
        rgba = rgba.resize((nw, nh), Image.BILINEAR)
        x += (ow - nw) / 2; y += (oh - nh) / 2
    a = np.asarray(rgba).astype(np.float32) / 255.0
    x, y = int(round(x)), int(round(y))
    h, w = a.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0:
        return
    sub = a[y0 - y:y1 - y, x0 - x:x1 - x]
    al = sub[..., 3:4] * alpha
    base[y0:y1, x0:x1] = base[y0:y1, x0:x1] * (1 - al) + sub[..., :3] * 255 * al

STYLES = {"red": dict(col=(255, 255, 255), bg=(220, 30, 30, 235), weight="ExtraBold"),
          "dark": dict(col=(255, 255, 255), bg=(0, 0, 0, 170), weight="ExtraBold"),
          "yellow": dict(col=(255, 214, 0), bg=None, weight="Black")}
TXT_CACHE = {}
def timg(txt, size, style="dark"):
    key = (txt, size, style)
    if key in TXT_CACHE:
        return TXT_CACHE[key]
    st = STYLES[style]
    f = font(size, st["weight"])
    # auto-shrink to fit 960 px
    while f.getbbox(txt)[2] - f.getbbox(txt)[0] > 900 and size > 28:
        size -= 2; f = font(size, st["weight"])
    b = f.getbbox(txt)
    stroke = 0 if st["bg"] else max(6, size // 12)
    pad = (28, 14)
    img = Image.new("RGBA", (b[2] - b[0] + 2 * pad[0] + 2 * stroke, b[3] - b[1] + 2 * pad[1] + 2 * stroke), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if st["bg"]:
        d.rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=18, fill=st["bg"])
    d.text((pad[0] + stroke - b[0], pad[1] + stroke - b[1]), txt, font=f, fill=st["col"], stroke_width=stroke, stroke_fill=(0, 0, 0))
    TXT_CACHE[key] = img
    return img

def shake_at(t):
    amp = 0
    for k, bt in enumerate(BOOMS):
        a0, dur = (26, 1.2) if k == 0 and bt < 0.5 else (46, 2.0)
        if bt <= t < bt + dur:
            amp = max(amp, a0 * (1 - (t - bt) / dur) ** 2)
    hx = 4 * math.sin(t * 1.7) + 3 * math.sin(t * 2.9 + 1)
    hy = 4 * math.cos(t * 1.3) + 3 * math.sin(t * 3.7 + 2)
    if amp:
        n = rng.normal(0, 1, 2); return (hx + n[0] * amp, hy + n[1] * amp)
    return (hx, hy)

def flash_at(t):
    v = 0
    for bt in BOOMS:
        if bt <= t < bt + 0.7:
            v = max(v, (1 - (t - bt) / 0.7) ** 2)
    return v

def fade(t, s, e, a=0.3):
    return ease_out((t - s) / a) * (1 - ease((t - (e - 0.35)) / 0.35))

def frame(n):
    t = n / FPS
    sh = shake_at(t)
    idx = [k for k, sc in enumerate(SCENES) if sc[0] <= t < sc[1]]
    k = idx[0] if idx else len(SCENES) - 1
    img = scene_frame(SCENES[k], t, sh)
    if k + 1 < len(SCENES) and t > SCENES[k][1] - XF:
        a = (t - (SCENES[k][1] - XF)) / XF
        img = img * (1 - a) + scene_frame(SCENES[k + 1], SCENES[k + 1][0], sh) * a
    fl = flash_at(t)
    if fl > 0.05:
        off = int(18 * fl)
        img[..., 0] = np.roll(img[..., 0], off, axis=1)
        img[..., 2] = np.roll(img[..., 2], -off, axis=1)
    img = img * VIG * BAND
    if fl > 0:
        img = img * (1 - fl) + np.array([255, 235, 200], np.float32) * fl
    img += GRAIN[n % len(GRAIN)]

    for (s, e) in SPEC.get("rings", []):
        if s <= t < e:
            a = fade(t, s, e, 0.4)
            rr = np.sqrt((xx - W / 2) ** 2 + (yy - H * 0.48) ** 2)
            ring = np.zeros((H, W), np.float32)
            for q in range(3):
                R = ((t - s) * 260 + q * 330) % 990
                ring += np.exp(-((rr - R) / 10) ** 2) * (1 - R / 990)
            img += ring[..., None] * np.array([255, 190, 90], np.float32) * 0.9 * a
    for (s, e, txt, size, style) in SPEC.get("labels", []):
        if s <= t < e:
            lab = timg(txt, size, style)
            sc = 1 + 0.12 * max(0, 1 - (t - s) / 0.25)
            overlay(img, lab, (W - lab.width) / 2, 260, scale=sc, alpha=fade(t, s, e))
    for (s, e, t0, dur, val, fmt, sub) in SPEC.get("counters", []):
        if s <= t < e:
            p = ease_out((t - t0) / dur)
            v = val * p
            v = int(round(v)) if val < 1000 else int(round(v / 10) * 10)
            txt = fmt.format(f"{v:,}".replace(",", " "))
            a = fade(t, s, e)
            lab = timg(txt, 120, "yellow")
            overlay(img, lab, (W - lab.width) / 2, 230, alpha=a)
            if sub:
                l2 = timg(sub, 40, "dark")
                overlay(img, l2, (W - l2.width) / 2, 400, alpha=a)
    end = SPEC.get("end")
    if end and t >= end["t"]:
        a = ease_out((t - end["t"]) / 0.4)
        img *= (1 - 0.45 * a)
        l1 = timg(end["l1"], 60, "yellow")
        l2 = timg(end["l2"], 56, "red")
        sc = 1 + 0.12 * max(0, 1 - (t - end["t"]) / 0.3)
        overlay(img, l1, (W - l1.width) / 2, 800, scale=sc, alpha=a)
        overlay(img, l2, (W - l2.width) / 2, 950, alpha=a)
    if t < END_T:
        for ci, (c0, c1) in enumerate(CHUNK_T):
            if c0 - 0.05 <= t < c1 + 0.12:
                active = None
                for j in CHUNKS[ci]:
                    if WORDS[j][0] <= t < WORDS[j][1] + 0.02:
                        active = j
                ci_img = render_chunk(ci, active)
                pp = (t - c0 + 0.05) / 0.12
                sc = 0.82 + 0.18 * ease_out(pp) + 0.04 * math.sin(min(pp, 1) * math.pi)
                overlay(img, ci_img, 0, 1100 - ci_img.height / 2, scale=sc)
                break
    return np.clip(img, 0, 255).astype(np.uint8)

if __name__ == "__main__":
    mode = sys.argv[2]
    if mode == "stills":
        for tt in [float(x) for x in sys.argv[3:]]:
            Image.fromarray(frame(int(tt * FPS))).save(f"still_{tt:05.2f}.jpg", quality=90)
    elif mode == "render":
        a, b, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                              "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for n in range(a, b):
            p.stdin.write(frame(n).tobytes())
        p.stdin.close()
        sys.exit(p.wait())
