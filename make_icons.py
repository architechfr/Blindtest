import os, math
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(OUT, exist_ok=True)

def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

# Degrade ciel -> coucher de soleil -> sol (t sur la hauteur)
STOPS = [
    (0.00, (12, 5, 48)),
    (0.42, (58, 10, 99)),
    (0.55, (138, 30, 116)),
    (0.61, (255, 72, 107)),
    (0.635, (255, 154, 60)),
    (0.64, (28, 7, 56)),
    (1.00, (10, 1, 24)),
]

def sky_color(t):
    for i in range(len(STOPS) - 1):
        t0, c0 = STOPS[i]; t1, c1 = STOPS[i + 1]
        if t0 <= t <= t1:
            return lerp(c0, c1, (t - t0) / (t1 - t0) if t1 > t0 else 0)
    return STOPS[-1][1]

def make(size):
    SS = 4
    S = size * SS
    img = Image.new("RGB", (S, S))
    px = img.load()
    for y in range(S):
        c = sky_color(y / S)
        for x in range(S):
            px[x, y] = c
    d = ImageDraw.Draw(img, "RGBA")

    cx = S / 2
    horizon = S * 0.64

    # ---- Soleil ----
    r = S * 0.27
    sy = horizon - r * 0.5  # centre
    sun = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sun)
    for yy in range(int(sy - r), int(sy + r)):
        t = (yy - (sy - r)) / (2 * r)
        col = lerp((255, 246, 176), (255, 46, 154), t)
        sd.line([(0, yy), (S, yy)], fill=col + (255,))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse([cx - r, sy - r, cx + r, sy + r], fill=255)
    img.paste(sun, (0, 0), Image.composite(Image.new("L", (S, S), 255), Image.new("L", (S, S), 0), mask))
    # bandes sombres (moitie basse)
    band = (28, 7, 56)
    bm = ImageDraw.Draw(img, "RGBA")
    yy = sy + r * 0.05
    step = r * 0.16
    while yy < sy + r:
        bm.rectangle([cx - r, yy, cx + r, yy + r * 0.06], fill=band + (255,))
        yy += step
    # re-masque pour garder le disque
    disk = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(disk).ellipse([cx - r, sy - r, cx + r, sy + r], fill=(255, 255, 255, 255))

    # ---- Grille (sol) ----
    grid = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    lw = max(2, int(S * 0.006))
    # lignes horizontales (espacement croissant)
    for i in range(9):
        t = i / 8
        y = horizon + (S - horizon) * (t ** 2)
        gd.line([(0, y), (S, y)], fill=(34, 211, 238, 150), width=lw)
    # lignes verticales convergentes
    for i in range(-7, 8):
        x_bottom = cx + i * (S * 0.55 / 7)
        gd.line([(x_bottom, S), (cx, horizon)], fill=(255, 46, 154, 130), width=lw)
    g2 = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(g2).rectangle([0, horizon, S, S], fill=(255, 255, 255, 255))
    grid = Image.composite(grid, Image.new("RGBA", (S, S), (0, 0, 0, 0)), g2.split()[3])
    img = Image.alpha_composite(img.convert("RGBA"), grid)

    # ---- Casque audio (hero) ----
    hp = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hp)
    hcx, hcy = cx, S * 0.45
    bw, bh = S * 0.205, S * 0.185
    band_w = int(S * 0.052)
    # arceau (arc haut)
    for col, wd in [((28, 7, 56, 255), band_w + int(S * 0.022)), ((255, 255, 255, 255), band_w)]:
        hd.arc([hcx - bw, hcy - bh, hcx + bw, hcy + bh], start=180, end=360, fill=col, width=wd)
    # ecouteurs
    cup_w, cup_h = S * 0.105, S * 0.20
    for sx in (hcx - bw, hcx + bw):
        x0, y0 = sx - cup_w / 2, hcy - S * 0.01
        d_rect = [x0, y0, x0 + cup_w, y0 + cup_h]
        hd.rounded_rectangle([d_rect[0] - S * 0.012, d_rect[1] - S * 0.012, d_rect[2] + S * 0.012, d_rect[3] + S * 0.012],
                             radius=int(cup_w * 0.5), fill=(28, 7, 56, 255))
        hd.rounded_rectangle(d_rect, radius=int(cup_w * 0.45), fill=(255, 255, 255, 255))
    # lueur
    glow = hp.filter(ImageFilter.GaussianBlur(int(S * 0.02)))
    img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, hp)

    img = img.convert("RGB").resize((size, size), Image.LANCZOS)
    return img

for s in (512, 192):
    make(s).save(os.path.join(OUT, f"icon-{s}.png"))
    print("wrote", f"icon-{s}.png")
print("done")
