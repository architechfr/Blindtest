"""Icones de l'app : cassette audio (K7) sur fond Synthwave."""
import os
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(OUT, exist_ok=True)

STOPS = [
    (0.00, (12, 5, 48)),
    (0.42, (58, 10, 99)),
    (0.55, (138, 30, 116)),
    (0.61, (255, 72, 107)),
    (0.635, (255, 154, 60)),
    (0.64, (28, 7, 56)),
    (1.00, (10, 1, 24)),
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


def make(size):
    SS = 4
    S = size * SS
    img = Image.new("RGB", (S, S))
    px = img.load()
    for y in range(S):
        c = sky(y / S)
        for x in range(S):
            px[x, y] = c

    cx = S / 2
    horizon = S * 0.66

    # --- Soleil ---
    r = S * 0.26
    sy = horizon - r * 0.55
    sun = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sun)
    for yy in range(int(sy - r), int(sy + r)):
        t = (yy - (sy - r)) / (2 * r)
        sd.line([(0, yy), (S, yy)], fill=lerp((255, 246, 176), (255, 46, 154), t) + (255,))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse([cx - r, sy - r, cx + r, sy + r], fill=255)
    img.paste(sun.convert("RGB"), (0, 0), mask)

    # --- Grille ---
    grid = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    lw = max(2, int(S * 0.006))
    for i in range(9):
        t = i / 8
        y = horizon + (S - horizon) * (t ** 2.1)
        gd.line([(0, y), (S, y)], fill=(34, 211, 238, 130), width=lw)
    for i in range(-8, 9):
        xb = cx + i * (S * 0.55 / 6)
        gd.line([(xb, S), (cx, horizon)], fill=(255, 46, 154, 110), width=lw)
    clip = Image.new("L", (S, S), 0)
    ImageDraw.Draw(clip).rectangle([0, horizon, S, S], fill=255)
    img = Image.alpha_composite(
        img.convert("RGBA"),
        Image.composite(grid, Image.new("RGBA", (S, S), (0, 0, 0, 0)), clip),
    )

    # --- Cassette K7 (hero) ---
    k7 = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    kd = ImageDraw.Draw(k7)
    bw, bh = S * 0.62, S * 0.40           # corps
    bx, by = cx - bw / 2, S * 0.50 - bh / 2 + S * 0.04
    rad = int(S * 0.045)

    kd.rounded_rectangle([bx, by, bx + bw, by + bh], radius=rad, fill=(24, 8, 52, 255),
                         outline=(34, 211, 238, 255), width=max(3, int(S * 0.011)))

    # etiquette
    lx0, ly0 = bx + bw * 0.075, by + bh * 0.09
    lx1, ly1 = bx + bw * 0.925, by + bh * 0.45
    label = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ld = ImageDraw.Draw(label)
    for yy in range(int(ly0), int(ly1)):
        t = (yy - ly0) / max(1, (ly1 - ly0))
        ld.line([(lx0, yy), (lx1, yy)], fill=lerp((255, 46, 154), (34, 211, 238), t) + (235,))
    lmask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(lmask).rounded_rectangle([lx0, ly0, lx1, ly1], radius=int(S * 0.018), fill=255)
    k7 = Image.alpha_composite(k7, Image.composite(label, Image.new("RGBA", (S, S), (0, 0, 0, 0)), lmask))
    kd = ImageDraw.Draw(k7)
    # lignes d'ecriture
    kd.line([(lx0 + bw * 0.06, ly0 + (ly1 - ly0) * 0.36), (lx1 - bw * 0.06, ly0 + (ly1 - ly0) * 0.36)],
            fill=(255, 255, 255, 150), width=max(2, int(S * 0.008)))
    kd.line([(lx0 + bw * 0.06, ly0 + (ly1 - ly0) * 0.66), (lx1 - bw * 0.28, ly0 + (ly1 - ly0) * 0.66)],
            fill=(255, 255, 255, 110), width=max(2, int(S * 0.008)))

    # fenetre + bobines
    wx0, wy0 = bx + bw * 0.20, by + bh * 0.55
    wx1, wy1 = bx + bw * 0.80, by + bh * 0.88
    kd.rounded_rectangle([wx0, wy0, wx1, wy1], radius=int(S * 0.02), fill=(8, 2, 20, 255),
                         outline=(34, 211, 238, 200), width=max(2, int(S * 0.007)))
    ry = (wy0 + wy1) / 2
    rr = (wy1 - wy0) * 0.32
    for rx, col in ((wx0 + (wx1 - wx0) * 0.26, (255, 46, 154, 255)), (wx0 + (wx1 - wx0) * 0.74, (34, 211, 238, 255))):
        kd.ellipse([rx - rr, ry - rr, rx + rr, ry + rr], outline=col, width=max(3, int(S * 0.011)))
        kd.ellipse([rx - rr * 0.34, ry - rr * 0.34, rx + rr * 0.34, ry + rr * 0.34], fill=col)
    # bande magnetique entre les bobines
    kd.rectangle([wx0 + (wx1 - wx0) * 0.36, ry - rr * 0.30, wx0 + (wx1 - wx0) * 0.64, ry + rr * 0.30],
                 fill=(70, 30, 110, 255))

    glow = k7.filter(ImageFilter.GaussianBlur(int(S * 0.016)))
    img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, k7)

    return img.convert("RGB").resize((size, size), Image.LANCZOS)


for s in (512, 192):
    make(s).save(os.path.join(OUT, f"icon-{s}.png"))
    print("wrote", f"icon-{s}.png")
print("done")
