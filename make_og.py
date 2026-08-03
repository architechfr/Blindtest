"""Genere l'image de partage (Open Graph 1200x630) — style Synthwave 80s."""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(OUT, exist_ok=True)

W, H = 1200, 630
SS = 2  # supersampling

STOPS = [
    (0.00, (5, 0, 10)),
    (0.28, (20, 6, 60)),
    (0.50, (90, 20, 110)),
    (0.62, (200, 40, 130)),
    (0.68, (255, 90, 110)),
    (0.72, (255, 160, 60)),
    (0.725, (20, 5, 40)),
    (1.00, (8, 1, 20)),
]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sky(t):
    for i in range(len(STOPS) - 1):
        t0, c0 = STOPS[i]
        t1, c1 = STOPS[i + 1]
        if t0 <= t <= t1:
            return lerp(c0, c1, (t - t0) / (t1 - t0) if t1 > t0 else 0)
    return STOPS[-1][1]


def font(size, bold=True):
    for name in (["arialbd.ttf", "segoeuib.ttf"] if bold else ["arial.ttf", "segoeui.ttf"]):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


w, h = W * SS, H * SS
img = Image.new("RGB", (w, h))
px = img.load()
for y in range(h):
    c = sky(y / h)
    for x in range(w):
        px[x, y] = c

horizon = h * 0.725
cx = w / 2

# --- Soleil ---
r = h * 0.30
sy = horizon - r * 0.42
sun = Image.new("RGBA", (w, h), (0, 0, 0, 0))
sd = ImageDraw.Draw(sun)
for yy in range(int(sy - r), int(sy + r)):
    t = (yy - (sy - r)) / (2 * r)
    sd.line([(0, yy), (w, yy)], fill=lerp((255, 246, 176), (255, 46, 154), t) + (255,))
mask = Image.new("L", (w, h), 0)
ImageDraw.Draw(mask).ellipse([cx - r, sy - r, cx + r, sy + r], fill=255)
img.paste(sun.convert("RGB"), (0, 0), mask)

# bandes horizontales sur la moitie basse du soleil
band = ImageDraw.Draw(img)
yy = sy + r * 0.06
while yy < sy + r:
    band.rectangle([cx - r, yy, cx + r, yy + r * 0.055], fill=(20, 5, 40))
    yy += r * 0.15
# on redecoupe le disque proprement
img2 = Image.new("RGB", (w, h))
p2 = img2.load()
for y in range(h):
    c = sky(y / h)
    for x in range(w):
        p2[x, y] = c
img2.paste(img, (0, 0), mask)
base = Image.new("RGB", (w, h))
pb = base.load()
for y in range(h):
    c = sky(y / h)
    for x in range(w):
        pb[x, y] = c
base.paste(img2, (0, 0), mask)
img = base

# --- Grille au sol ---
grid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
gd = ImageDraw.Draw(grid)
lw = max(2, int(w * 0.0022))
for i in range(11):
    t = i / 10
    y = horizon + (h - horizon) * (t ** 2.1)
    gd.line([(0, y), (w, y)], fill=(34, 211, 238, 140), width=lw)
for i in range(-14, 15):
    xb = cx + i * (w * 0.5 / 7)
    gd.line([(xb, h), (cx, horizon)], fill=(255, 46, 154, 120), width=lw)
clip = Image.new("L", (w, h), 0)
ImageDraw.Draw(clip).rectangle([0, horizon, w, h], fill=255)
img = Image.alpha_composite(img.convert("RGBA"), Image.composite(grid, Image.new("RGBA", (w, h), (0, 0, 0, 0)), clip))

d = ImageDraw.Draw(img)

# --- Titre ---
f_big = font(int(h * 0.155))
f_sub = font(int(h * 0.052))
f_tag = font(int(h * 0.040), bold=False)

title = "BLIND TEST"
tb = d.textbbox((0, 0), title, font=f_big)
tx, ty = cx - (tb[2] - tb[0]) / 2, h * 0.20

glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
ImageDraw.Draw(glow).text((tx, ty), title, font=f_big, fill=(255, 46, 154, 255))
img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(int(h * 0.022))))
d = ImageDraw.Draw(img)
d.text((tx + 4, ty + 5), title, font=f_big, fill=(120, 20, 90))
d.text((tx, ty), title, font=f_big, fill=(255, 255, 255))

sub = "M U S I C A L"
sb = d.textbbox((0, 0), sub, font=f_sub)
d.text((cx - (sb[2] - sb[0]) / 2, ty + (tb[3] - tb[1]) + h * 0.055), sub, font=f_sub, fill=(34, 211, 238))

tag = "Buzze  ·  Reponds  ·  Vote  ·  Le plus rapide gagne"
gb = d.textbbox((0, 0), tag, font=f_tag)
d.text((cx - (gb[2] - gb[0]) / 2, h * 0.845), tag, font=f_tag, fill=(255, 255, 255))

img.convert("RGB").resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "og-image.png"), quality=95)
print("wrote assets/og-image.png")
