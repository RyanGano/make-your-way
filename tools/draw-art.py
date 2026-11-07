"""Generates the line-art illustrations in art/.

Every drawing is plain strokes. Colours come from CSS classes in style.css
(.thin, .accent, .fill, .fill-accent, .paper), so the art follows light and dark mode.
Usage: python tools/draw-art.py
"""
import math
import os
import random

OUT = os.path.join(os.path.dirname(__file__), "..", "art")
W, H = 600, 320


def svg(name, label, *parts):
    body = "\n".join(p for p in parts if p)
    doc = (f'<svg class="lineart" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
           f'role="img" aria-label="{label}">\n{body}\n</svg>\n')
    with open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8") as f:
        f.write(doc)


def path(d, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<path{c} d="{d}"/>'


def line(x1, y1, x2, y2, cls=""):
    return path(f"M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}", cls)


def circle(cx, cy, r, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<circle{c} cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}"/>'


def ellipse(cx, cy, rx, ry, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<ellipse{c} cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}"/>'


def rect(x, y, w, h, cls="", r=0):
    c = f' class="{cls}"' if cls else ""
    return f'<rect{c} x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}"/>'


def poly(points, cls="", closed=False):
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in points) + (" Z" if closed else "")
    return path(d, cls)


def waves(y, x0, x1, amp=4, wl=28, cls="thin"):
    d = f"M{x0} {y}"
    x = x0
    up = True
    while x < x1:
        nx = min(x + wl / 2, x1)
        d += f" Q{(x + nx) / 2:.1f} {y - amp if up else y + amp} {nx:.1f} {y}"
        x = nx
        up = not up
    return path(d, cls)


def wave_field(y0, y1, x0, x1, rows, seed, cls="thin"):
    rnd = random.Random(seed)
    out = []
    for i in range(rows):
        y = y0 + (y1 - y0) * i / max(1, rows - 1)
        a = rnd.uniform(x0, x0 + 80)
        while a < x1 - 40:
            b = min(a + rnd.uniform(40, 120), x1)
            out.append(waves(y, a, b, amp=2 + i * 0.4, wl=18 + i * 2, cls=cls))
            a = b + rnd.uniform(20, 70)
    return "\n".join(out)


def fog(y0, y1, seed, n=7, x0=0, x1=W):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        y = rnd.uniform(y0, y1)
        a = rnd.uniform(x0, x1 - 120)
        b = a + rnd.uniform(80, 220)
        out.append(line(a, y, min(b, x1), y, "thin"))
    return "\n".join(out)


def hatch(x0, y0, x1, y1, gap=7, cls="thin", slope=1.0):
    """Diagonal hatching clipped to a rectangle."""
    out = []
    w, h = x1 - x0, y1 - y0
    k = -h
    while k < w:
        ax, ay = x0 + k, y1
        bx, by = x0 + k + h / slope, y0
        # clip to the rectangle
        if ax < x0:
            ay -= (x0 - ax) * slope
            ax = x0
        if bx > x1:
            by += (bx - x1) * slope
            bx = x1
        if ax < bx and ay > by:
            out.append(line(ax, ay, bx, by, cls))
        k += gap
    return "\n".join(out)


def dots(n, x0, y0, x1, y1, seed, rmin=1.2, rmax=2.6, cls="fill-accent"):
    rnd = random.Random(seed)
    return "\n".join(circle(rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(rmin, rmax), cls) for _ in range(n))


def dots_in(n, fn, seed, rmin=1.2, rmax=2.6, cls="fill-accent"):
    """Scatter dots where fn(x, y) is true."""
    rnd = random.Random(seed)
    out = []
    tries = 0
    while len(out) < n and tries < n * 50:
        tries += 1
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        if fn(x, y):
            out.append(circle(x, y, rnd.uniform(rmin, rmax), cls))
    return "\n".join(out)


def stars(n, seed, y1=150):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = rnd.uniform(10, W - 10), rnd.uniform(10, y1)
        s = rnd.uniform(1.5, 3.5)
        out.append(path(f"M{x - s:.1f} {y:.1f} L{x + s:.1f} {y:.1f} M{x:.1f} {y - s:.1f} L{x:.1f} {y + s:.1f}", "thin"))
    return "\n".join(out)


def rays(cx, cy, r0, r1, n, cls="accent", start=0, spread=360):
    out = []
    for i in range(n):
        a = math.radians(start + spread * i / (n if spread == 360 else max(1, n - 1)))
        out.append(line(cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + r1 * math.cos(a), cy + r1 * math.sin(a), cls))
    return "\n".join(out)


def lighthouse(x, base, top, w_base=34, w_top=22, lamp=True, lit=False):
    """A tapered tower with gallery and lamp room. x is the centre."""
    parts = [
        poly([(x - w_base / 2, base), (x - w_top / 2, top), (x + w_top / 2, top), (x + w_base / 2, base)]),
        # bands
        line(x - (w_base + w_top) / 4 - 1, (base + top) / 2, x + (w_base + w_top) / 4 + 1, (base + top) / 2, "thin"),
        line(x - w_top / 2 - 6, top, x + w_top / 2 + 6, top),
        line(x - w_top / 2 - 6, top - 4, x + w_top / 2 + 6, top - 4, "thin"),
        rect(x - w_top / 2 + 2, top - 22, w_top - 4, 18),
        line(x, top - 22, x, top - 4, "thin"),
        path(f"M{x - w_top / 2:.1f} {top - 22:.1f} Q{x:.1f} {top - 38:.1f} {x + w_top / 2:.1f} {top - 22:.1f}"),
        line(x, top - 33, x, top - 40),
        rect(x - 3, base - 16, 6, 16, "thin"),
    ]
    if lit:
        parts.append(circle(x, top - 13, 4, "fill-accent"))
    return "\n".join(parts)


def tree(x, base, h, w, cls=""):
    """A simple engraved-looking conifer."""
    out = [line(x, base, x, base - h * 0.25, cls)]
    tiers = 4
    for i in range(tiers):
        ty = base - h * 0.2 - i * h * 0.2
        tw = w * (1 - i / (tiers + 1))
        out.append(path(f"M{x - tw / 2:.1f} {ty:.1f} Q{x:.1f} {ty - h * 0.08:.1f} {x:.1f} {ty - h * 0.3:.1f} "
                        f"Q{x:.1f} {ty - h * 0.08:.1f} {x + tw / 2:.1f} {ty:.1f}", cls))
    return "\n".join(out)


def crow_shape(x, y, s=1.0, flip=False):
    """A perched crow; (x, y) is where the feet touch."""
    f = -1 if flip else 1
    def P(px, py):
        return f"{x + f * px * s:.1f} {y + py * s:.1f}"
    body = (f"M{P(-4, 0)} L{P(-2, -10)} Q{P(-18, -14)} {P(-30, -6)} L{P(-46, 2)} L{P(-28, -2)} "
            f"Q{P(-14, -4)} {P(-4, -12)} Q{P(4, -26)} {P(10, -30)} Q{P(18, -34)} {P(22, -28)} L{P(32, -26)} "
            f"L{P(22, -22)} Q{P(18, -12)} {P(6, -8)} Z")
    return "\n".join([
        path(body, "fill"),
        line(x + f * -2 * s, y, x + f * -6 * s, y + 5 * s, "thin"),
        line(x + f * 2 * s, y - 1, x + f * 3 * s, y + 5 * s, "thin"),
    ])


# ---------------------------------------------------------------- Gull Rock

def gull(x, y, s=1.0):
    return path(f"M{x - 9 * s:.1f} {y:.1f} Q{x - 4 * s:.1f} {y - 6 * s:.1f} {x:.1f} {y:.1f} "
                f"Q{x + 4 * s:.1f} {y - 6 * s:.1f} {x + 9 * s:.1f} {y:.1f}", "thin")


def island(x0, x1, y, h):
    return path(f"M{x0} {y} Q{x0 + 30} {y - h * 0.6} {x0 + (x1 - x0) * 0.35:.1f} {y - h} "
                f"Q{x0 + (x1 - x0) * 0.6:.1f} {y - h * 1.1:.1f} {x1 - 30} {y - h * 0.5:.1f} L{x1} {y}")


def draw_gull_rock():
    svg("mailboat", "A small motor boat in fog approaching a rocky island with a dark lighthouse",
        fog(30, 150, 1, 9),
        island(330, 560, 210, 50),
        lighthouse(450, 165, 70, 22, 14),
        rect(395, 172, 34, 20, "thin"),
        path("M392 172 L412 160 L432 172", "thin"),
        # boat
        path("M60 238 Q70 262 120 266 L250 266 Q286 262 300 232 Z"),
        line(70 , 248, 296, 244, "thin"),
        rect(150, 206, 70, 32),
        rect(160, 214, 16, 12, "thin"), rect(186, 214, 16, 12, "thin"),
        line(210, 206, 210, 160), line(210, 170, 240, 186, "thin"),
        path("M222 206 L222 192 L232 192 L232 206", "thin"),
        path("M96 228 Q100 224 104 228 Q112 218 120 232", "thin"),
        wave_field(250, 310, 0, W, 6, 2),
        waves(270, 40, 140, 3, 14), waves(272, 260, 340, 3, 14),
        gull(110, 90), gull(140, 76, 0.8), gull(520, 110, 0.7),
    )

    svg("cottage-kitchen", "A kitchen table with an abandoned supper and an open logbook, a cat waiting by the window",
        # window with tower
        rect(370, 40, 150, 120), line(445, 40, 445, 160, "thin"), line(370, 100, 520, 100, "thin"),
        lighthouse(410, 160, 62, 16, 10),
        fog(50, 150, 3, 4, 372, 518),
        # table
        line(40, 210, 340, 210), line(40, 216, 340, 216, "thin"),
        line(70, 216, 64, 300), line(310, 216, 316, 300),
        # bowl + spoon
        path("M80 196 Q105 222 130 196 Z"), ellipse(105, 196, 25, 5, "thin"), line(118, 192, 140, 176, "thin"),
        # mug with steam gone
        rect(150, 178, 24, 30), path("M174 186 Q186 190 174 200", "thin"),
        # loaf
        path("M190 208 Q195 186 225 188 Q240 192 240 208 Z"), line(205, 192, 202, 206, "thin"), line(220, 190, 218, 206, "thin"),
        # open log
        path("M250 206 L262 186 L300 190 L300 210 Z"), path("M300 190 L338 186 L346 206 L300 210", ""),
        line(268, 194, 294, 196, "thin"), line(266, 199, 294, 201, "thin"), line(306, 196, 334, 194, "thin"), line(306, 201, 336, 199, "thin"),
        # pushed-back chair
        poly([(360, 300), (368, 230), (410, 232), (404, 300)]), line(368, 230, 376, 180), line(410, 232, 416, 184),
        line(376, 180, 416, 184), line(372, 205, 413, 208, "thin"),
        # cat
        path("M470 300 Q462 250 482 236 L478 220 L488 230 Q496 226 504 230 L512 220 L510 238 Q528 252 520 300 Z"),
        path("M520 296 Q548 292 546 270", ""),
        circle(490, 242, 1.6, "fill"), circle(504, 242, 1.6, "fill"),
        line(440, 300, 580, 300, "thin"),
        ellipse(450, 296, 16, 4, "thin"),
    )

    lens_rows = []
    for i in range(9):
        y = 70 + i * 22
        w = 70 + 40 * math.sin(math.pi * (i + 0.5) / 9)
        lens_rows.append(ellipse(300, y, w, 8, "thin"))
    svg("lamp-lens", "The great lighthouse lens, lit, with beams sweeping out",
        rays(300, 160, 130, 290, 4, "accent", start=-25, spread=50),
        rays(300, 160, 130, 290, 4, "accent", start=155, spread=50),
        path("M230 60 Q300 20 370 60"),
        "\n".join(lens_rows),
        line(230, 60, 222, 250), line(370, 60, 378, 250),
        line(260, 58, 254, 252, "thin"), line(340, 58, 346, 252, "thin"), line(300, 50, 300, 255, "thin"),
        circle(300, 160, 14, "accent"), circle(300, 160, 6, "fill-accent"),
        rect(200, 255, 200, 16), line(180, 271, 420, 271), line(190, 271, 180, 300), line(410, 271, 420, 300),
        # window frames
        line(40, 20, 40, 300, "thin"), line(130, 20, 130, 300, "thin"), line(470, 20, 470, 300, "thin"), line(560, 20, 560, 300, "thin"),
        line(0, 300, W, 300),
    )

    svg("sea-cave", "The black mouth of a sea cave, with waves running in",
        path("M0 60 Q40 40 90 56 Q150 30 200 70 L230 120 Q260 90 300 92 Q350 94 380 130 L410 80 Q470 40 540 60 Q580 70 600 64"),
        path("M120 250 Q130 170 180 140 Q240 104 300 106 Q370 110 410 160 Q446 206 450 250"),
        path("M160 250 Q170 190 210 166 Q260 138 300 140 Q348 144 380 180 Q404 212 408 250", "thin"),
        hatch(200, 160, 400, 250, 9, "thin"),
        path("M0 250 L120 250 M450 250 L600 250"),
        path("M0 120 Q40 140 60 200 L70 250", "thin"), path("M600 120 Q560 150 548 200 L540 250", "thin"),
        hatch(0, 70, 110, 248, 12, "thin", 0.7), hatch(470, 80, 600, 248, 12, "thin", 0.7),
        wave_field(262, 310, 0, W, 5, 4),
        path("M180 250 Q220 236 260 250 Q300 238 340 250 Q380 240 420 250", ""),
        path("M60 250 Q72 236 92 238 Q108 230 120 250", "thin"), path("M470 250 Q484 232 506 240 Q520 236 530 250", "thin"),
    )

    svg("rowing-fog", "A small rowing boat in thick fog, a lighthouse beam passing overhead",
        path("M300 40 L20 90 M300 40 L20 20", "accent"),
        lighthouse(560, 90, 40, 10, 7, lit=True),
        fog(40, 200, 5, 12),
        path("M170 232 Q190 262 260 264 L360 264 Q410 260 430 228 Z"),
        line(184 , 242, 424, 238, "thin"),
        # rower
        path("M290 228 L292 196 Q300 184 312 192 L318 228"), circle(302, 178, 10),
        line(296 , 206, 250, 216), line(312, 206, 358, 214),
        line(250, 216, 170, 262), line(358, 214, 450, 260),
        ellipse(166, 266, 10, 3, "thin"), ellipse(454, 262, 10, 3, "thin"),
        wave_field(268, 310, 0, W, 4, 6),
    )

    svg("reef-lantern", "A lantern on a pole wedged among jagged reef rocks, foam pouring between them",
        rays(330, 92, 22, 60, 12, "accent"),
        circle(330, 92, 14, "accent"), path("M322 80 L338 80 L342 104 L318 104 Z"), line(330, 76, 330, 70),
        line(330, 104, 342, 230), line(336, 104, 348, 230, "thin"),
        poly([(0, 260), (40, 220), (70, 236), (110, 190), (150, 240), (190, 226), (230, 260)]),
        poly([(250, 260), (290, 210), (320, 228), (360, 180), (400, 236), (440, 206), (480, 260)]),
        poly([(470, 260), (510, 230), (540, 244), (570, 214), (600, 236)]),
        hatch(80, 200, 140, 258, 8, "thin"), hatch(340, 196, 400, 258, 8, "thin"),
        path("M230 262 Q238 248 250 262 M460 262 Q468 246 478 262", "thin"),
        wave_field(266, 312, 0, W, 5, 7),
        path("M0 262 Q60 252 120 262 Q180 270 240 262 Q300 254 360 262 Q420 270 480 262 Q540 254 600 262"),
    )

    svg("flare", "A red distress flare bursting over the rocks at night",
        stars(30, 8, 120),
        circle(300, 80, 10, "fill-accent"),
        rays(300, 80, 18, 70, 16, "accent"),
        path("M300 92 Q296 160 290 230", "accent"),
        path("M0 230 Q60 196 120 214 Q180 180 240 206 Q290 220 330 196 Q400 170 460 210 Q520 190 600 214 L600 320 L0 320 Z"),
        hatch(0, 236, 600, 320, 10, "thin"),
        # three figures
        circle(250, 182, 7), path("M243 210 L246 190 L254 190 L257 210 M246 194 L236 172 M254 194 L262 204"),
        circle(350, 172, 8), path("M340 206 L344 182 L356 182 L360 206"),
        circle(392, 184, 7), path("M385 210 L388 192 L396 192 L399 210"),
    )

    ship = [
        path("M120 220 Q140 250 210 254 L420 254 Q470 248 490 214 Z", "thin"),
        line(230, 220, 230, 50, "thin"), line(330, 220, 330, 40, "thin"), line(420, 216, 420, 70, "thin"),
        line(490, 214, 560, 170, "thin"),
    ]
    for mx, top in ((230, 60), (330, 50), (420, 80)):
        for i, w in enumerate((44, 54, 60)):
            y = top + 10 + i * 46
            ship.append(path(f"M{mx - w} {y} Q{mx} {y + 8} {mx + w} {y} L{mx + w - 4} {y + 38} Q{mx} {y + 46} {mx - w + 4} {y + 38} Z", "thin"))
    svg("ghost-ship", "The faint outline of an old sailing ship in the fog, lanterns glowing along her rail",
        "\n".join(ship),
        "\n".join(circle(150 + i * 46, 214, 3.5, "fill-accent") for i in range(7)),
        circle(560, 168, 5, "fill-accent"),
        fog(30, 280, 9, 14),
        wave_field(266, 312, 0, W, 4, 10),
    )

    svg("dawn-tower", "Gull Rock lighthouse at dawn, the keeper's cottage below and gulls overhead",
        circle(470, 230, 46, "accent"),
        rays(470, 230, 56, 84, 9, "accent", start=190, spread=160),
        line(0, 236, W, 236, "thin"),
        path("M120 236 Q150 200 200 190 Q260 170 330 176 Q390 186 420 236"),
        hatch(140, 196, 410, 234, 10, "thin"),
        lighthouse(250, 182, 40, 36, 22, lit=True),
        rect(300, 160, 70, 26), path("M294 160 L335 136 L376 160"), rect(320, 168, 10, 10, "thin"), rect(346, 168, 12, 18, "thin"),
        line(356, 140, 356, 128, "thin"), line(352, 128, 360, 128, "thin"),
        gull(120, 80), gull(150, 64, 0.8), gull(380, 70, 0.9), gull(560, 100, 0.7),
        wave_field(250, 310, 0, W, 6, 11),
    )


# ---------------------------------------------------------------- The Map That Drew Itself

def mountain_with_dome(cx, base, peak, half):
    return "\n".join([
        path(f"M{cx - half} {base} L{cx - 30} {peak + 26} L{cx} {peak} L{cx + 34} {peak + 30} L{cx + half} {base}"),
        path(f"M{cx - 30} {peak + 26} L{cx - 18} {peak + 60} M{cx + 34} {peak + 30} L{cx + 24} {peak + 70}", "thin"),
        path(f"M{cx - 14} {peak + 2} Q{cx} {peak - 20} {cx + 14} {peak + 2} Z"),
        line(cx, peak - 12, cx, peak - 20, "thin"),
    ])


def draw_inkwold():
    road = "M150 300 Q200 250 180 220 Q160 190 230 170 Q300 150 280 120 Q262 92 340 84"
    svg("map-shop", "A map pinned to a drawing table, an ink road drawing itself toward a library on a mountain",
        # table edge in perspective
        poly([(40, 300), (90, 60), (510, 60), (560, 300)], closed=True),
        circle(100, 70, 4, "fill"), circle(500, 70, 4, "fill"), circle(70, 290, 4, "fill"), circle(530, 290, 4, "fill"),
        path(road, "accent"),
        mountain_with_dome(380, 140, 80, 60),
        "\n".join(tree(x, y, 30, 18, "thin") for x, y in ((120, 170), (138, 186), (160, 168), (420, 240), (440, 252))),
        waves(250, 230, 380, 4, 24), waves(262, 250, 400, 4, 24),
        path("M440 110 Q470 120 480 160", "thin"),
        # blank edge creeping
        path("M490 70 Q470 140 512 200 Q480 240 540 290", "thin"),
        # pen
        line(330, 40, 420, 20), path("M330 40 L320 46 L326 36 Z", "fill"),
        circle(150, 300, 3, "fill-accent"),
    )

    svg("crow", "A large crow perched on a signpost whose arms are blank",
        line(300, 300, 300, 120), line(306, 300, 306, 120, "thin"),
        poly([(180, 140), (420, 140), (440, 156), (420, 172), (180, 172)], closed=True),
        poly([(190, 190), (420, 190), (420, 222), (190, 222), (170, 206)], closed=True),
        crow_shape(318, 140, 2.0),
        path("M0 300 Q150 290 300 300 Q450 310 600 296", "thin"),
        path("M240 300 Q250 288 262 300 M330 300 Q344 284 356 300 M380 300 Q390 292 400 300", "thin"),
    )

    trunks = []
    rnd = random.Random(12)
    for i in range(12):
        x = 20 + i * 52 + rnd.uniform(-10, 10)
        if 240 < x < 360:
            continue
        w = rnd.uniform(16, 30)
        trunks.append(path(f"M{x:.1f} 320 Q{x + 4:.1f} 160 {x:.1f} 0 M{x + w:.1f} 320 Q{x + w - 4:.1f} 160 {x + w:.1f} 0"))
        trunks.append(hatch(x + 2, 0, x + w - 2, 320, 9, "thin"))
    svg("whisperwood", "Tall dark trees crowding a narrow pale path",
        "\n".join(trunks),
        path("M260 320 Q290 240 296 180 Q300 120 302 60"), path("M340 320 Q314 240 308 180 Q304 120 304 60"),
        "\n".join(path(f"M{x} {y} q6 -8 12 0 q-6 8 -12 0", "thin") for x, y in ((220, 60), (380, 50), (420, 110), (180, 120), (240, 200), (370, 220))),
        path("M246 300 q-10 -20 4 -26 q10 4 0 14", "thin"), path("M356 290 q10 -20 -4 -26 q-10 4 0 14", "thin"),
    )

    svg("lantern-hollow", "A feast table in a ring of trees, golden lights floating above it",
        "\n".join(tree(x, 230, 140, 70) for x in (40, 120, 480, 560)),
        ellipse(300, 260, 250, 40, "thin"),
        rect(170, 206, 260, 10), line(190, 216, 190, 256), line(410, 216, 410, 256),
        line(220, 206, 220, 176, "thin"), line(300, 206, 300, 170, "thin"), line(380, 206, 380, 176, "thin"),
        "\n".join(circle(x, y, 3, "fill-accent") for x, y in ((220, 172), (300, 166), (380, 172))),
        path("M240 206 Q260 186 280 206 Z"), path("M320 206 Q330 190 350 192 Q362 196 360 206 Z"),
        "\n".join(circle(x, y, r, "accent") + circle(x, y, 2, "fill-accent")
                  for x, y, r in ((200, 90, 9), (260, 60, 8), (330, 80, 10), (400, 56, 8), (440, 110, 9), (160, 130, 7), (300, 120, 7))),
        # a waiting figure rooted at the table
        circle(300, 176, 0.1), path("M140 256 Q150 220 150 196 M150 196 Q144 180 152 172", "thin"),
        path("M130 256 Q138 270 120 286 M150 256 Q156 276 146 292", "thin"),
    )

    svg("ferry", "A hooded ferryman on a flat boat with a lantern, crossing a wide dark river",
        line(0, 150, W, 150, "thin"),
        path("M0 150 Q80 130 140 142 Q220 124 300 140 Q380 120 460 138 Q540 126 600 140", "thin"),
        path("M160 220 L440 220 L420 240 L180 240 Z"),
        line(410, 220, 410, 100), path("M402 100 L418 100 L420 124 L400 124 Z"), circle(410, 112, 4, "fill-accent"),
        rays(410, 112, 14, 30, 8, "accent"),
        # hooded figure
        path("M270 220 L276 150 Q290 116 304 150 L310 220 Z"), path("M278 150 Q290 132 302 150", "thin"),
        ellipse(290, 152, 8, 10, "paper"),
        line(304 , 170, 350, 290),
        wave_field(250, 312, 0, W, 6, 13),
        "\n".join(ellipse(x, y, 16, 5, "thin") for x, y in ((100, 270), (520, 284), (230, 298))),
    )

    svg("crossroads", "A signpost at a crossroads, a mountain rising behind with a domed library at its peak",
        mountain_with_dome(330, 230, 40, 220),
        hatch(200, 120, 300, 228, 12, "thin"),
        line(0, 230, W, 230, "thin"),
        path("M0 300 Q200 260 300 250 Q400 240 600 270"), path("M300 250 L250 320 M300 250 L380 320"),
        line(300, 250, 300, 160), poly([(240, 168), (300, 168), (300, 186), (240, 186), (230, 177)], closed=True),
        poly([(300, 192), (366, 192), (376, 201), (366, 210), (300, 210)], closed=True),
        # the Blank: road stops dead at a hard edge
        path("M520 120 L520 320", "thin"), path("M526 120 L526 320", "thin"),
        path("M470 274 L520 268"), path("M500 230 L500 196 Q490 180 500 166 M500 196 Q512 184 516 176", "thin"),
    )

    towers = []
    for x, h in ((60, 150), (110, 200), (160, 130), (210, 230), (270, 170), (320, 120)):
        towers.append(path(f"M{x - 18} 300 L{x - 14} {300 - h} L{x} {300 - h - 30} L{x + 14} {300 - h} L{x + 18} 300", "thin"))
        towers.append(line(x, 300 - h - 30, x, 300 - h - 44, "thin"))
        for y in range(300 - h + 20, 296, 26):
            towers.append(rect(x - 6, y, 12, 14, "thin"))
    svg("glass-city", "A city of thin glass towers, a cable car climbing on its wire toward the mountain",
        "\n".join(towers),
        line(210, 40, 600, 0 + 10), line(210, 40, 210, 70, "thin"),
        line(420, 24, 420, 40), rect(398, 40, 44, 30, "accent"), line(408, 46, 408, 64, "thin"), line(432, 46, 432, 64, "thin"),
        path("M440 300 L520 120 L600 160", ""), hatch(470, 160, 600, 300, 12, "thin"),
        line(0, 300, W, 300),
        rays(260, 200, 0, 0, 0),
    )

    stair = "M120 300 L260 280 L150 250 L290 230 L180 200 L320 180 L210 150 L340 130 L240 100 L360 80"
    svg("ink-stair", "A zigzag stair cut into a cliff, a stone hut and a goat on a ledge halfway up",
        path("M60 320 L100 200 L160 120 L230 60 L300 40 L380 60 L440 140 L520 220 L560 320"),
        path(stair), path(stair.replace("M120 300", "M126 306"), "thin"),
        # hut on ledge
        rect(390, 172, 50, 34), path("M384 172 L415 150 L446 172"), rect(406, 186, 12, 20, "thin"), line(430, 156, 430, 144),
        path("M430 140 q6 -8 0 -16 q-6 -8 0 -16", "thin"),
        # goat
        path("M460 206 L462 190 Q472 184 486 188 L490 180 L494 186 L492 196 L488 206 M466 206 L466 196 M482 206 L482 196"),
        # clouds
        path("M0 80 Q30 60 60 76 Q90 56 130 78 Q150 70 170 84", "thin"), path("M420 40 Q450 20 490 36 Q520 22 560 40 Q580 34 600 44", "thin"),
        crow_shape(380, 80, 0.7),
    )

    shelves = []
    for i in range(6):
        y = 60 + i * 40
        shelves.append(line(20, y, 150, y, "thin"))
        shelves.append(line(450, y, 580, y, "thin"))
        for x in range(26, 146, 9):
            shelves.append(line(x, y - 4, x, y - 30, "thin"))
        for x in range(456, 576, 9):
            shelves.append(line(x, y - 4, x, y - 30, "thin"))
    svg("library-dome", "Inside the great library: curving shelves of maps, a round desk under the dome",
        path("M150 300 L150 90 Q300 -20 450 90 L450 300"),
        path("M190 90 Q300 10 410 90", "thin"), line(300 , 14, 300, 40, "thin"),
        "\n".join(shelves),
        ellipse(300, 250, 90, 18), line(214, 252, 220, 300), line(386, 252, 380, 300),
        path("M300 232 L300 196 M284 196 L316 196 L308 180 L292 180 Z"), circle(300, 210, 0.1),
        rays(300, 196, 8, 30, 7, "accent", start=40, spread=100),
        path("M250 246 L290 240 L296 252 L256 258 Z", "thin"), line(330, 244, 360, 230), line(340, 248, 368, 236, "accent"),
        line(0, 300, W, 300),
    )

    svg("the-blank", "A drawn landscape that simply stops at a clean white edge",
        path("M0 220 Q60 180 120 196 Q180 210 240 170 Q290 140 330 160"),
        "\n".join(tree(x, y, 60, 30) for x, y in ((50, 210), (90, 200), (200, 196), (260, 166))),
        path("M0 280 Q80 250 160 262 Q240 276 330 244"),
        hatch(0, 230, 330, 300, 14, "thin"),
        path("M120 300 Q160 270 200 262 Q260 250 330 252", "accent"),
        # half a tree at the edge
        line(330, 120, 330, 300), line(330, 120, 330, 300),
        path("M330 160 Q310 150 300 130 M330 180 Q306 176 292 166 M330 140 Q318 126 316 110", "thin"),
        line(336, 40, 336, 300, "thin"),
        # a small figure facing the white
        circle(440, 214, 7), path("M432 258 L436 226 L444 226 L448 258 M436 232 L426 246 M444 232 L452 246"),
        circle(470, 240, 0.1),
    )


# ---------------------------------------------------------------- The Long Quiet

def porthole(cx, cy, r):
    return "\n".join([circle(cx, cy, r), circle(cx, cy, r - 8, "thin"),
                      "\n".join(circle(cx + (r - 4) * math.cos(a), cy + (r - 4) * math.sin(a), 1.6, "fill")
                                for a in [i * math.pi / 4 for i in range(8)])])


def sub(cx, cy, s=1.0, lit=True):
    out = [
        path(f"M{cx - 60 * s:.1f} {cy:.1f} Q{cx - 60 * s:.1f} {cy - 30 * s:.1f} {cx - 20 * s:.1f} {cy - 32 * s:.1f} "
             f"L{cx + 40 * s:.1f} {cy - 30 * s:.1f} Q{cx + 66 * s:.1f} {cy - 24 * s:.1f} {cx + 66 * s:.1f} {cy:.1f} "
             f"Q{cx + 66 * s:.1f} {cy + 24 * s:.1f} {cx + 30 * s:.1f} {cy + 28 * s:.1f} L{cx - 30 * s:.1f} {cy + 28 * s:.1f} "
             f"Q{cx - 60 * s:.1f} {cy + 26 * s:.1f} {cx - 60 * s:.1f} {cy:.1f} Z"),
        path(f"M{cx + 6 * s:.1f} {cy - 30 * s:.1f} Q{cx + 30 * s:.1f} {cy - 62 * s:.1f} {cx + 56 * s:.1f} {cy - 20 * s:.1f}", "thin"),
        line(cx - 60 * s, cy, cx - 80 * s, cy - 8 * s), line(cx - 60 * s, cy, cx - 80 * s, cy + 8 * s),
        line(cx - 80 * s, cy - 8 * s, cx - 80 * s, cy + 8 * s),
        path(f"M{cx - 10 * s:.1f} {cy + 28 * s:.1f} L{cx - 4 * s:.1f} {cy + 44 * s:.1f} L{cx + 10 * s:.1f} {cy + 48 * s:.1f}", "thin"),
        path(f"M{cx + 20 * s:.1f} {cy + 28 * s:.1f} L{cx + 26 * s:.1f} {cy + 42 * s:.1f} L{cx + 40 * s:.1f} {cy + 44 * s:.1f}", "thin"),
        circle(cx - 20 * s, cy - 6 * s, 5 * s, "thin"), circle(cx - 2 * s, cy - 6 * s, 5 * s, "thin"),
    ]
    if lit:
        out.append(circle(cx + 66 * s, cy, 4 * s, "fill-accent"))
        out.append(path(f"M{cx + 70 * s:.1f} {cy - 4 * s:.1f} L{cx + 200 * s:.1f} {cy - 40 * s:.1f} "
                        f"M{cx + 70 * s:.1f} {cy + 4 * s:.1f} L{cx + 200 * s:.1f} {cy + 50 * s:.1f}", "accent"))
    return "\n".join(out)


def draw_long_quiet():
    svg("sickbay", "A sick bay bed with a drip stand beside it and a porthole onto black water",
        porthole(440, 110, 56),
        dots(10, 400, 70, 480, 150, 14, 1, 2),
        # bed
        rect(80, 200, 260, 20), line(90, 220, 90, 290), line(330, 220, 330, 290),
        path("M80 200 L80 160 M340 200 L340 176"), rect(92, 182, 60, 18, "thin", 6),
        path("M150 200 Q200 186 250 196 Q300 204 330 196", "thin"),
        # drip stand
        line(380, 290, 380, 120), line(366, 120, 394, 120), path("M372 124 L388 124 L386 160 L374 160 Z"),
        path("M380 160 Q360 210 300 200", "thin"),
        line(360, 290, 400, 290), line(0, 296, W, 296, "thin"),
        # cabinets
        rect(500, 190, 80, 100), line(540, 190, 540, 290, "thin"), circle(534, 240, 2, "fill"), circle(546, 240, 2, "fill"),
    )

    ribs = []
    for i in range(6):
        t = i / 6
        x0, x1 = 60 + 200 * t, 540 - 200 * t
        y0, y1 = 20 + 110 * t, 300 - 110 * t
        ribs.append(path(f"M{x0:.1f} {y1:.1f} L{x0:.1f} {y0 + 40 * (1 - t):.1f} Q{(x0 + x1) / 2:.1f} {y0 - 10 * (1 - t):.1f} "
                         f"{x1:.1f} {y0 + 40 * (1 - t):.1f} L{x1:.1f} {y1:.1f}", "" if i == 0 else "thin"))
    svg("corridor", "A long station corridor in near darkness, lit only by strip lights along the floor",
        "\n".join(ribs),
        line(60, 300, 260, 190, "thin"), line(540, 300, 340, 190, "thin"),
        "\n".join(line(70 + i * 30, 296 - i * 16.5, 82 + i * 30, 290 - i * 16.5, "accent") for i in range(6)),
        "\n".join(line(530 - i * 30, 296 - i * 16.5, 518 - i * 30, 290 - i * 16.5, "accent") for i in range(6)),
        rect(270, 130, 60, 60, "thin", 10), circle(300, 160, 12, "thin"),
        path("M120 150 L170 150 L170 260 L120 270 Z", "thin"),
        porthole(470, 150, 22),
    )

    wave = "M150 110"
    for i in range(40):
        x = 150 + i * 7.5
        y = 110 + 34 * math.sin(i * 0.55) * math.sin(i * 0.12 + 0.4)
        wave += f" L{x:.1f} {y:.1f}"
    svg("operations", "A curved console of screens, the main screen showing the signal's waveform",
        rect(130, 50, 340, 120, "", 6), path(wave, "accent"),
        line(140, 110, 460, 110, "thin"),
        rect(30, 80, 86, 70, "thin", 4), rect(484, 80, 86, 70, "thin", 4),
        path("M40 130 L60 110 L80 120 L104 96", "thin"), path("M494 120 Q520 90 560 120", "thin"),
        path("M20 230 Q300 170 580 230 L580 250 Q300 192 20 250 Z"),
        "\n".join(rect(90 + i * 46, 214 - 12 * math.sin(math.pi * (i + 0.5) / 10), 18, 8, "thin", 2) for i in range(10)),
        # empty chairs
        path("M140 300 L150 266 L200 266 L206 300 M150 266 L144 236 L194 236 L200 266"),
        path("M400 300 L404 266 L454 266 L464 300 M404 266 L410 236 L460 236 L454 266"),
    )

    tanks = []
    for i, x in enumerate((40, 180, 320, 460)):
        tanks.append(rect(x, 130, 110, 80))
        tanks.append(line(x, 146, x + 110, 146, "thin"))
        tanks.append(dots(26, x + 6, 152, x + 104, 204, 20 + i, 1, 2.4))
    svg("lab", "Glass sample tanks along a lab bench, each full of tiny glowing points",
        "\n".join(tanks),
        line(20, 210, 580, 210), line(20, 218, 580, 218, "thin"),
        line(40, 218, 40, 300), line(560, 218, 560, 300),
        # a circle-in-circle shape formed by lights in one tank
        circle(375, 175, 16, "accent"), circle(375, 175, 6, "accent"),
        # plants above
        "\n".join(path(f"M{x} 100 Q{x - 10} 70 {x - 22} 64 M{x} 100 Q{x + 6} 66 {x + 20} 58 M{x} 100 L{x} 120", "thin") for x in (90, 250, 410, 530)),
        "\n".join(circle(x, y, 2, "fill-accent") for x, y in ((80, 76), (262, 70), (420, 66), (520, 74))),
        line(20, 120, 580, 120, "thin"),
    )

    svg("reactor", "A squat reactor wrapped in pipes, warning signs on its side",
        path("M220 300 L220 90 Q300 60 380 90 L380 300"), ellipse(300, 90, 80, 16, "thin"),
        line(220, 150, 380, 150, "thin"), line(220, 240, 380, 240, "thin"),
        poly([(300, 168), (322, 208), (278, 208)], closed=True), line(300, 180, 300, 196, "thin"), circle(300, 202, 1.6, "fill"),
        path("M380 120 L460 120 Q480 120 480 140 L480 300"), path("M380 132 L452 132 Q468 132 468 148 L468 300", "thin"),
        path("M220 200 L140 200 Q120 200 120 180 L120 40"), path("M220 212 L132 212 Q108 212 108 188 L108 40", "thin"),
        circle(114, 120, 14), line(104, 120, 124, 120, "thin"),
        rect(500, 160, 70, 90, "", 4), circle(535, 190, 14, "thin"), line(535, 190, 545, 180, "accent"),
        rect(512, 220, 46, 14, "thin"),
        line(0, 300, W, 300),
    )

    svg("moonpool", "A round pool of open ocean in the station floor, glowing from below, a small submarine in its cradle",
        ellipse(300, 230, 240, 60), ellipse(300, 230, 220, 50, "thin"),
        dots_in(90, lambda x, y: ((x - 300) / 210) ** 2 + ((y - 232) / 46) ** 2 < 1, 15),
        line(40, 150, 560, 150), line(40, 162, 560, 162, "thin"),
        "\n".join(line(x, 150, x, 196, "thin") for x in range(60, 560, 50)),
        sub(420, 100, 0.55, lit=False),
        line(420, 40, 420, 82, "thin"), line(400, 40, 440, 40), line(0, 40, W, 40, "thin"),
        rect(110, 112, 40, 26, "thin"), line(116, 118, 144, 118, "thin"),
    )

    body = lambda x, y: (((x - 300) / 46) ** 2 + ((y - 170) / 70) ** 2 < 1) or (((x - 300) / 26) ** 2 + ((y - 76) / 28) ** 2 < 1)
    svg("visitor", "A tall figure made of tiny lights rising from the glowing water",
        ellipse(300, 250, 260, 50), ellipse(300, 250, 240, 40, "thin"),
        dots_in(220, body, 16, 1, 2.6),
        dots_in(60, lambda x, y: ((x - 300) / 230) ** 2 + ((y - 252) / 36) ** 2 < 1, 17),
        path("M260 140 Q200 150 170 190 Q160 210 150 230", "accent"), path("M340 140 Q400 150 430 190 Q440 210 452 230", "accent"),
        path("M170 190 q-12 4 -16 16 M170 190 q-4 12 -14 18", "thin"), path("M430 190 q12 4 16 16 M430 190 q4 12 14 18", "thin"),
        line(40, 140, 120, 140), line(480, 140, 560, 140),
    )

    svg("remora", "A small submarine descending through black water, its lights cutting a path, glowing specks all around",
        sub(240, 150, 1.2),
        dots(70, 0, 0, W, H, 18, 1, 2.2),
        "\n".join(line(x, y, x, y + 6, "thin") for x, y in ((60, 60), (110, 250), (480, 40), (540, 230), (380, 290), (160, 30))),
    )

    chimneys = []
    for x, h, w in ((80, 150, 30), (170, 210, 40), (420, 180, 36), (510, 130, 28)):
        chimneys.append(path(f"M{x - w / 2} 300 Q{x - w / 3} {300 - h / 2} {x - 8} {300 - h} L{x + 8} {300 - h} Q{x + w / 3} {300 - h / 2} {x + w / 2} 300"))
        chimneys.append(path(f"M{x} {300 - h} Q{x - 14} {300 - h - 30} {x + 4} {300 - h - 56} Q{x + 18} {300 - h - 80} {x} {300 - h - 104}", "thin"))
    svg("vents", "Hydrothermal chimneys on the sea floor, glowing coral towers and a clear dome sheltering a submarine",
        "\n".join(chimneys),
        path("M200 300 Q200 190 300 186 Q400 190 400 300", "accent"),
        sub(300, 268, 0.5, lit=False),
        "\n".join(path(f"M{x} 300 L{x} {300 - h} M{x} {300 - h * 0.6} L{x - 10} {300 - h * 0.8} M{x} {300 - h * 0.5} L{x + 12} {300 - h * 0.7}", "thin")
                  for x, h in ((130, 60), (230, 40), (370, 50), (460, 70), (560, 50))),
        dots(80, 0, 20, W, 290, 19, 1, 2.2),
        line(0, 300, W, 300),
    )

    bands = []
    for i, (y, a) in enumerate(((60, 0.25), (85, 0.5), (110, 0.65), (140, 0.62), (165, 0.45))):
        bands.append(path(f"M{430 - 150 * math.sqrt(max(0.0, 1 - ((y - 120) / 150) ** 2)):.1f} {y} "
                          f"Q430 {y + 10} {430 + 150 * math.sqrt(max(0.0, 1 - ((y - 120) / 150) ** 2)):.1f} {y}", "thin"))
    svg("europa-sky", "Jupiter hanging huge over the cracked ice plain of Europa, a small lander on the surface",
        stars(40, 21, 200),
        path("M280 200 A150 150 0 0 1 580 200"), "\n".join(bands), ellipse(470, 150, 18, 8, "accent"),
        line(0, 200, W, 200),
        path("M0 230 L80 222 L140 240 L220 226 M300 260 L360 236 L440 250 L520 230 L600 244 M40 290 L130 270 L200 300 M380 300 L460 280 L560 296", "thin"),
        # lander
        path("M120 200 L130 176 L170 176 L180 200 Z"), path("M130 176 L138 156 L162 156 L170 176"), line(150, 156, 150, 136),
        path("M142 136 Q150 128 158 136", "thin"),
        line(124, 196, 108, 214), line(176, 196, 192, 214), line(102, 214, 114, 214), line(186, 214, 198, 214),
    )


def draw_favicon():
    with open(os.path.join(OUT, "favicon.svg"), "w", encoding="utf-8") as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#f7f1e5"/>'
                '<g fill="none" stroke="#9a3b25" stroke-width="2.4" stroke-linecap="round"><path d="M5 27 C10 21, 8 14, 16 12 S 23 5, 27 5"/>'
                '<path d="M16 12 C 20 16, 22 21, 27 25"/></g><circle cx="27" cy="5" r="2.4" fill="#9a3b25"/><circle cx="27" cy="25" r="2.4" fill="#9a3b25"/></svg>\n')


# ---------------------------------------------------------------- Second batch: one drawing per passage

def person(x, gy, s=1.0, cls="", arms=None):
    """A simple standing figure; (x, gy) is the ground point. arms = (left_dx, left_dy, right_dx, right_dy)."""
    hy = gy - 60 * s
    la = arms or (-12, 22, 12, 22)
    return "\n".join([
        circle(x, hy, 7 * s, cls),
        path(f"M{x - 6 * s:.1f} {gy:.1f} L{x - 3 * s:.1f} {hy + 30 * s:.1f} M{x + 6 * s:.1f} {gy:.1f} L{x + 3 * s:.1f} {hy + 30 * s:.1f}", cls),
        path(f"M{x - 3 * s:.1f} {hy + 30 * s:.1f} L{x - 5 * s:.1f} {hy + 10 * s:.1f} L{x + 5 * s:.1f} {hy + 10 * s:.1f} L{x + 3 * s:.1f} {hy + 30 * s:.1f}", cls),
        line(x - 5 * s, hy + 12 * s, x + la[0] * s, hy + 12 * s + la[1] * s, cls),
        line(x + 5 * s, hy + 12 * s, x + la[2] * s, hy + 12 * s + la[3] * s, cls),
    ])


def launch(cx, cy, s=1.0, light=True):
    out = [
        path(f"M{cx - 90 * s:.1f} {cy:.1f} L{cx + 70 * s:.1f} {cy:.1f} Q{cx + 100 * s:.1f} {cy - 4 * s:.1f} {cx + 110 * s:.1f} {cy - 22 * s:.1f} "
             f"L{cx - 90 * s:.1f} {cy - 22 * s:.1f} Z"),
        rect(cx - 30 * s, cy - 46 * s, 50 * s, 24 * s),
        rect(cx - 22 * s, cy - 40 * s, 14 * s, 10 * s, "thin"), rect(cx - 2 * s, cy - 40 * s, 14 * s, 10 * s, "thin"),
        line(cx - 86 * s, cy - 12 * s, cx + 100 * s, cy - 12 * s, "thin"),
    ]
    if light:
        out.append(circle(cx + 86 * s, cy - 28 * s, 5 * s, "fill-accent"))
    return "\n".join(out)


def draw_more_gull_rock():
    page = [line(300, 60, 300, 280, "thin")]
    for i in range(9):
        y = 90 + i * 20
        page.append(line(110, y, 280 - (i % 3) * 20, y + 2, "thin"))
        page.append(line(320, y + 2, 490 - ((i + 1) % 3) * 30, y, "thin"))
    svg("logbook", "The keeper's log open on the table, entries crowding toward the last page",
        path("M80 280 L100 60 Q200 50 300 64 Q400 50 500 60 L520 280 Q410 268 300 284 Q190 268 80 280 Z"),
        "\n".join(page),
        path("M340 250 L350 236 L400 240 L420 252", "accent"),
        line(470, 120, 560, 40), path("M470 120 L462 130 L466 116 Z", "fill"),
        circle(140, 300, 0.1),
    )

    rail, steps = [], []
    for i in range(0, 161):
        t = i / 10
        rail.append((300 + 120 * math.sin(t), 310 - t * 18))
    for i in range(32):
        t = i / 2
        x, y = 300 + 120 * math.sin(t), 310 - t * 18
        front = math.cos(t) > 0
        steps.append(line(300, y - 8, x, y, "" if front else "thin"))
        steps.append(line(x, y, x, y - 18, "thin"))
    svg("tower-stairs", "An iron spiral staircase winding up inside the tower",
        poly(rail, "thin"),
        "\n".join(steps),
        line(300, 320, 300, 0),
        path("M140 320 L160 0 M460 320 L440 0"),
        rect(380, 100, 22, 46, "thin", 10),
    )

    svg("davy", "A boy in a wool hat sitting on the rocks clutching his ankle, a small skiff tucked behind him",
        path("M0 250 Q80 200 160 220 Q240 190 330 214 Q420 180 520 210 L600 200 L600 320 L0 320 Z"),
        hatch(0, 240, 600, 320, 11, "thin"),
        # skiff
        path("M380 196 Q390 214 430 214 L500 214 Q526 210 536 192 Z"),
        # boy sitting
        circle(250, 150, 9), path("M241 146 Q250 132 259 146 Z", "fill"),
        path("M244 160 L240 196 L280 196"), path("M256 160 L262 186"), line(244, 170, 268, 192),
        path("M280 196 L292 210", ""),
        fog(40, 120, 22, 6),
    )

    svg("gallery", "Two small figures on the lighthouse gallery, pointing out to sea as the beam sweeps across",
        path("M300 140 L600 60 M300 140 L600 220", "accent"),
        path("M200 320 L220 140 L380 140 L400 320"),
        line(170, 140, 430, 140), line(170, 110, 430, 110),
        "\n".join(line(x, 110, x, 140, "thin") for x in range(180, 430, 20)),
        rect(250, 60, 100, 50), path("M250 60 Q300 20 350 60"), circle(300, 85, 10, "fill-accent"),
        person(220, 140, 0.8, arms=(-10, 18, 40, -10)),
        person(190, 140, 0.6),
        fog(160, 300, 23, 8),
    )

    svg("signal-lamp", "Hands working the shutter of a signal lamp, dots and dashes of light going out into the fog",
        rect(150, 140, 120, 80, "", 10), circle(270, 180, 30), circle(270, 180, 22, "thin"),
        line(170, 220, 170, 250), line(230, 220, 230, 250), line(150, 250, 250, 250),
        path("M190 140 Q200 110 220 120 L226 140", ""),
        "\n".join(circle(x, 180, 4, "fill-accent") for x in (330, 350)),
        line(380, 180, 420, 180, "accent"), circle(450, 180, 4, "fill-accent"), line(480, 180, 520, 180, "accent"),
        circle(550, 180, 4, "fill-accent"),
        fog(40, 300, 24, 8, 300, 600),
        path("M120 300 L130 200 Q150 196 160 220", "thin"),
    )

    svg("boathouse", "The boathouse door standing open, the slipway empty and scraped",
        rect(100, 120, 200, 140), path("M90 120 L200 60 L310 120"),
        rect(150, 170, 100, 90), hatch(152, 172, 248, 258, 8, "thin"),
        poly([(150, 260), (120, 320), (330, 320), (250, 260)]),
        path("M170 270 Q180 300 160 320 M210 270 Q214 300 220 320", "thin"),
        line(320, 260, 600, 260), wave_field(270, 312, 330, 600, 4, 25),
        circle(360, 250, 10), line(350, 250, 330, 230, "thin"),
        "\n".join(line(120 + i * 22, 130, 120 + i * 22, 165, "thin") for i in range(8)),
        fog(30, 110, 26, 5),
    )

    svg("radio", "An old radio telephone in its cabinet, valves glowing, a heavy handset off the hook",
        rect(150, 40, 300, 240), line(150, 80, 450, 80),
        rect(180, 100, 140, 70, "", 4), path("M190 160 L210 120 L230 150 L250 110 L270 140 L290 125 L310 135", "thin"),
        circle(370, 130, 26), line(370, 130, 386, 112, "accent"),
        "\n".join(circle(x, 210, 12) for x in (200, 250, 300)),
        "\n".join(circle(x, 60, 6, "fill-accent") for x in (190, 220, 250)),
        rect(330, 190, 100, 70, "thin"),
        path("M470 200 Q520 180 540 220 Q550 250 520 270 L500 250 Q520 230 500 214 Z"),
        path("M430 220 Q460 260 500 250", "thin"),
    )

    svg("ada-hollow", "A small grey-haired woman wedged in a hollow among the reef rocks, spray rising around her",
        path("M0 320 L40 200 L120 160 L200 180 L240 120 L330 110 L400 150 L470 130 L560 190 L600 320"),
        path("M200 220 Q260 170 330 190 Q380 210 390 260 L200 260 Z"),
        hatch(40, 200, 200, 318, 12, "thin"), hatch(400, 200, 590, 318, 12, "thin"),
        circle(290, 210, 10), path("M282 204 Q290 194 300 204", "thin"),
        path("M276 224 L270 260 M304 224 L320 256 L360 252"), line(284, 236, 314, 236),
        "\n".join(path(f"M{x} {y} q4 -10 0 -18", "thin") for x, y in ((100, 150), (170, 150), (430, 120), (520, 160))),
        rays(330, 92, 10, 30, 8, "accent"), circle(330, 92, 6, "fill-accent"), line(330, 98, 336, 112),
    )

    svg("launch-searchlight", "A grey motor launch idling in the fog, its searchlight sweeping the rocks",
        path("M386 196 L60 120 M386 196 L60 260", "accent"),
        launch(300, 220, 1.0),
        wave_field(228, 312, 0, W, 5, 27),
        poly([(0, 230), (30, 190), (70, 210), (110, 180), (150, 230)]), hatch(20, 190, 140, 228, 9, "thin"),
        person(270, 172, 0.5), person(310, 172, 0.5),
        fog(20, 160, 28, 8),
    )

    crates = []
    for x, y, w, h in ((120, 200, 100, 70), (220, 210, 80, 60), (150, 140, 80, 60), (330, 230, 70, 40)):
        crates.append(rect(x, y, w, h))
        crates.append(line(x, y, x + w, y + h, "thin"))
        crates.append(line(x + w, y, x, y + h, "thin"))
    svg("crates", "Stolen crates stacked in the back of the cave, lit by a hanging lantern",
        path("M0 0 Q120 60 200 40 Q300 20 400 50 Q500 70 600 0"),
        path("M0 320 L0 260 Q100 270 300 270 Q500 270 600 250 L600 320"),
        "\n".join(crates),
        line(460, 40, 460, 90, "thin"), path("M450 90 L470 90 L474 120 L446 120 Z"), circle(460, 106, 4, "fill-accent"),
        rays(460, 106, 18, 50, 10, "accent"),
        "\n".join(person(x, 270, 0.9) for x in (480, 520, 560)),
        path("M168 180 L178 168 M200 180 L210 168", "thin"),
    )

    svg("moored-launch", "The wreckers' launch tied up in a dark inlet, a key glinting on the dashboard",
        launch(300, 230, 1.3, light=False),
        path("M0 140 L80 120 L120 160 L100 240 L0 250 Z"), path("M600 140 L520 130 L480 170 L500 240 L600 250 Z"),
        hatch(0, 140, 100, 248, 10, "thin"), hatch(500, 140, 600, 248, 10, "thin"),
        line(90, 200, 190, 216, "thin"),
        circle(296, 158, 4, "fill-accent"), line(300, 158, 312, 158, "accent"),
        wave_field(240, 312, 0, W, 5, 29),
    )

    svg("reef-flare", "A red flare hanging over the reef, a motor launch drifting with its engine dead",
        circle(320, 70, 9, "fill-accent"), rays(320, 70, 16, 64, 14, "accent"),
        stars(20, 30, 110),
        launch(380, 236, 0.8, light=False),
        poly([(0, 250), (60, 200), (110, 230), (160, 190), (220, 250)]), hatch(40, 200, 200, 248, 9, "thin"),
        person(120, 214, 0.6), circle(80, 214, 0.1),
        line(140, 190, 120, 160, "thin"),
        wave_field(250, 312, 0, W, 5, 31),
    )

    svg("lifeboat", "An orange lifeboat and a police launch coming out of the fog together",
        path("M80 230 Q90 260 150 262 L300 262 Q336 258 350 220 Z", "accent"),
        rect(170, 196, 90, 24, "accent"), line(215, 196, 215, 150, "accent"), circle(215, 146, 5, "fill-accent"),
        launch(470, 240, 0.8),
        path("M440 200 L470 200", "thin"),
        fog(20, 190, 32, 10),
        wave_field(262, 312, 0, W, 4, 33),
    )

    svg("steamer", "The bow of a huge steamer looming over a tiny rowing boat",
        path("M220 0 L320 290 Q340 306 380 300 L600 290"),
        path("M240 0 L330 270", "thin"),
        "\n".join(circle(420 + i * 44, 130, 7) for i in range(4)),
        "\n".join(circle(400 + i * 50, 200, 7) for i in range(4)),
        line(300, 60, 600, 60), line(260, 30, 600, 30, "thin"),
        path("M60 262 Q70 280 110 282 L170 282 Q190 280 196 260 Z"),
        person(130, 262, 0.55, arms=(-20, -30, 10, 10)),
        line(112, 220, 104, 210, "accent"), rays(104, 210, 4, 16, 6, "accent"),
        wave_field(286, 314, 0, W, 3, 34),
        path("M300 300 Q260 290 230 300 Q200 310 170 300", "thin"),
    )

    svg("cat", "A ginger cat sitting calmly on a rock beside a flare pistol",
        path("M0 280 Q200 250 300 262 Q420 274 600 250 L600 320 L0 320 Z"), hatch(0, 270, 600, 320, 12, "thin"),
        path("M260 266 Q246 200 274 182 L268 156 L284 170 Q300 164 316 170 L332 156 L326 182 Q356 200 340 266 Z"),
        path("M340 260 Q380 256 386 226 Q390 210 376 206", ""),
        circle(288, 186, 2, "fill"), circle(312, 186, 2, "fill"), path("M296 196 L300 200 L304 196", "thin"),
        line(270, 196, 250, 192, "thin"), line(270, 200, 250, 204, "thin"), line(330, 196, 350, 192, "thin"), line(330, 200, 350, 204, "thin"),
        path("M420 262 L470 262 L476 252 L430 250 Z M440 262 L436 280 L450 280 L452 262"), circle(472, 256, 0.1),
        path("M290 230 Q300 240 310 230", "thin"),
    )

    ribs = []
    for i in range(7):
        x = 160 + i * 45
        ribs.append(path(f"M{x} 280 Q{x - 20} 220 {x + 6} {190 + abs(3 - i) * 8}"))
    svg("wreck", "The ribs of an old wooden hull under green water, a small brass lantern sinking toward it",
        line(0, 40, W, 40, "thin"), waves(40, 0, W, 4, 30),
        path("M140 280 Q300 300 470 280"),
        "\n".join(ribs),
        "\n".join(path(f"M{x} 300 q-8 -20 0 -40 q8 -20 0 -40", "thin") for x in (110, 500, 540)),
        path("M310 110 L324 110 L328 136 L306 136 Z"), line(317, 104, 317, 110), circle(317, 124, 4, "fill-accent"),
        "\n".join(circle(317 + dx, 90 - i * 18, 2 + i * 0.5, "thin") for i, dx in enumerate((4, -3, 6))),
        line(0, 300, W, 300, "thin"),
    )

    svg("gallery-night", "Two keepers sitting on the gallery at night with a flask of tea, the beam turning above them",
        stars(36, 35, 180),
        path("M300 90 L600 40 M300 90 L0 140", "accent"),
        rect(250, 60, 100, 50), path("M250 60 Q300 20 350 60"), circle(300, 85, 10, "fill-accent"),
        line(150, 200, 450, 200), line(150, 170, 450, 170),
        "\n".join(line(x, 170, x, 200, "thin") for x in range(160, 450, 20)),
        path("M220 320 L230 200 M380 320 L370 200"),
        circle(260, 146, 8), path("M248 200 L252 160 L268 160 L272 200"),
        circle(330, 146, 8), path("M318 200 L322 160 L338 160 L342 200"),
        rect(292, 180, 10, 18), path("M402 200 Q396 184 412 182 Q428 184 422 200 Z"),
    )


def draw_more_inkwold():
    svg("journal", "Orrin's journal, stuffed with loose pages, sketches and blots",
        path("M70 290 L90 50 Q190 40 300 58 Q410 40 510 50 L530 290 Q410 280 300 296 Q190 280 70 290 Z"),
        line(300, 58, 300, 296, "thin"),
        mountain_with_dome(180, 160, 80, 70),
        path("M110 200 Q150 190 170 230 Q200 260 250 240", "thin"),
        "\n".join(line(330, y, 480 - (y % 3) * 20, y, "thin") for y in range(90, 270, 18)),
        circle(460, 240, 10, "fill"), circle(476, 252, 4, "fill"),
        path("M140 60 L120 20 L180 30 L176 66", "thin"),
        path("M500 80 q10 -20 30 -10 q-10 20 -30 10", "thin"),
    )

    pots = "\n".join(circle(x, y, r) for x, y, r in ((210, 120, 14), (240, 110, 10), (300, 116, 12), (330, 122, 9)))
    svg("tinker", "A round tinker in a patchwork coat pushing a cart hung with pots and pans",
        rect(170, 140, 200, 70), line(170, 175, 370, 175, "thin"),
        circle(210, 228, 22), circle(330, 228, 22), circle(210, 228, 3, "fill"), circle(330, 228, 3, "fill"),
        pots, line(190, 140, 190, 100), line(350, 140, 350, 96), line(190, 100, 350, 96, "thin"),
        path("M370 160 L420 150"),
        circle(440, 120, 12), path("M420 230 Q414 180 426 140 Q440 132 456 140 Q470 180 462 230 Z"),
        hatch(424, 150, 460, 228, 8, "thin"),
        line(0, 250, W, 250, "thin"),
        "\n".join(tree(x, 250, 90, 40, "thin") for x in (50, 100, 540)),
    )

    svg("drawn-door", "A wobbly door drawn in the air in ink, the word DOOR written across its top",
        "\n".join(tree(x, 300, 200, 80, "thin") for x in (60, 140, 460, 540)),
        path("M240 300 Q236 200 244 100 L360 96 Q366 200 362 300"),
        path("M256 300 L260 120 L346 118 L348 300", "thin"),
        circle(334, 210, 6),
        f'<text x="300" y="88" text-anchor="middle" class="fill" style="font: 600 22px Fraunces, Georgia, serif; stroke: none">DOOR</text>',
        line(380, 120, 450, 60), path("M380 120 L372 130 L376 116 Z", "fill"),
        path("M260 300 L340 300", "accent"),
    )

    svg("memory-river", "Looking down into the river: a snowman, a birthday cake and a dog drift past under the surface",
        wave_field(20, 60, 0, W, 3, 40),
        circle(130, 170, 22, "thin"), circle(130, 130, 15, "thin"), path("M130 130 L146 134 L130 136", "accent"), line(108, 160, 90, 150, "thin"),
        rect(270, 170, 70, 40, "thin"), "\n".join(line(x, 170, x, 156, "thin") for x in (285, 305, 325)),
        "\n".join(circle(x, 152, 2, "fill-accent") for x in (285, 305, 325)),
        path("M440 200 L446 170 L470 166 L490 172 L500 160 L506 170 L500 200 M450 200 L452 186 M490 200 L490 186", "thin"),
        wave_field(240, 300, 0, W, 4, 41),
        path("M200 300 Q220 200 300 200 Q380 200 400 300", "thin"),
    )

    svg("raft", "A battered log raft on the dark river, a crow perched on the highest log",
        "\n".join(rect(160 + i * 0, 200 + i * 14, 280, 12, "", 6) for i in range(3)),
        line(190, 196, 190, 246, "thin"), line(410, 196, 410, 246, "thin"),
        line(300, 200, 360, 60), person(260, 200, 0.8, arms=(-6, 20, 40, -40)),
        crow_shape(420, 198, 0.8),
        wave_field(250, 312, 0, W, 5, 42),
        path("M0 110 Q150 96 300 110 Q450 124 600 106", "thin"),
    )

    shelves = []
    rnd = random.Random(43)
    for row in range(5):
        y = 70 + row * 46
        shelves.append(line(60, y, 540, y, "thin"))
        x = 70
        while x < 520:
            w = rnd.uniform(20, 40)
            shelves.append(rect(x, y - 22, w, 16, "thin", 2))
            x += w + rnd.uniform(6, 14)
    svg("word-shop", "A narrow shop lined with tiny shelves, each holding a single slip of paper with a word on it",
        "\n".join(shelves),
        rect(250, 270, 100, 40), line(240, 270, 360, 270),
        path("M270 250 L330 244 L334 262 L272 268 Z", "accent"),
        f'<text x="300" y="260" text-anchor="middle" transform="rotate(-5 300 258)" class="fill-accent" style="font: italic 12px Literata, Georgia, serif">kepthereness</text>',
        rect(440, 20, 30, 26, "accent"), line(446, 20, 446, 46, "thin"), line(458, 20, 458, 46, "thin"),
    )

    svg("cable-car", "A small glass cable car swinging high over the valley, someone clinging to its outside",
        line(0, 120, W, 40),
        line(300, 80, 300, 110), rect(250, 110, 100, 70, "", 8),
        "\n".join(rect(258 + i * 24, 120, 18, 30, "thin", 3) for i in range(4)),
        person(240, 186, 0.6, arms=(10, -20, 12, -26)),
        path("M0 320 L80 240 L140 280 L220 200 L300 290 L380 230 L460 300 L540 250 L600 300"),
        "\n".join(tree(x, 300, 30, 16, "thin") for x in (120, 160, 330, 420, 500)),
        path("M440 60 Q470 40 500 56 Q530 40 560 60", "thin"),
    )

    svg("hermit", "An old hermit with a long beard unrolling a map across his knees outside his hut",
        rect(360, 120, 150, 120), path("M350 120 L435 70 L520 120"), rect(420, 180, 30, 60, "thin"),
        line(490, 90, 490, 70), path("M490 66 q8 -10 0 -20 q-8 -10 0 -20", "thin"),
        circle(230, 140, 14), path("M220 150 Q230 200 240 150", "thin"),
        path("M206 240 L210 166 L250 166 L254 240"),
        path("M150 200 L320 196 L316 230 L154 236 Z"), path("M150 200 Q140 216 154 236 M320 196 Q330 212 316 230"),
        path("M170 222 L210 204 L240 216 L290 206", "accent"), path("M200 230 L220 214 L236 226 Z", "thin"),
        line(0, 240, W, 240),
        path("M530 240 L534 216 Q548 208 562 214 L566 206 L570 214 L568 224 L564 240", ""),
    )

    svg("above-clouds", "The library dome rising above a sea of cloud, other peaks poking up like islands",
        path("M0 220 Q40 200 80 214 Q120 196 170 212 Q220 192 280 210 Q340 190 400 210 Q460 194 520 212 Q560 200 600 214"),
        path("M0 250 Q60 236 120 248 Q200 232 280 246 Q360 232 440 248 Q520 236 600 248", "thin"),
        path("M40 214 L80 160 L110 200", ""), path("M480 210 L520 150 L560 206", ""),
        path("M220 200 L220 140 L380 140 L380 200"), path("M210 140 Q300 40 390 140"),
        "\n".join(line(x, 140, x, 200, "thin") for x in (240, 270, 330, 360)),
        line(300, 60, 300, 46), rect(285, 160, 30, 40, "thin", 10),
        circle(520, 60, 24, "accent"), rays(520, 60, 30, 46, 10, "accent"),
        path("M130 90 q8 -6 16 0 q8 -6 16 0", "thin"),
    )

    carve = []
    rnd = random.Random(44)
    for side in (0, 1):
        x0 = 150 + side * 155
        for i in range(6):
            y = 70 + i * 34
            carve.append(path(f"M{x0 + 10} {y} Q{x0 + 40 + rnd.uniform(-10, 10):.1f} {y - 10:.1f} {x0 + 70} {y + 4} T{x0 + 135} {y}", "thin"))
    svg("library-door", "The tall carved doors of the library standing a crack open, light spilling through",
        rect(150, 40, 145, 270), rect(305, 40, 145, 270),
        path("M140 40 Q300 -30 460 40"),
        "\n".join(carve),
        circle(276, 180, 12), circle(324, 180, 12), rays(276, 180, 0, 12, 4, "thin"), rays(324, 180, 0, 12, 4, "thin"),
        path("M295 40 L305 40 L305 310 L295 310 Z", "accent"),
        path("M300 310 L260 320 M300 310 L340 320", "accent"),
        circle(300, 312, 3, "fill"),
    )

    svg("two-pens", "Two hands drawing side by side on one map, shelves rising up behind",
        path("M60 300 L100 140 L500 140 L540 300 Z"),
        path("M160 260 L200 200 L240 230 L300 180", "accent"), path("M330 270 L360 220 L420 240 L470 190"),
        path("M120 120 Q130 60 180 40 L210 70 L196 130", "thin"), line(180, 40, 220, 200),
        path("M480 120 Q470 60 420 40 L390 70 L404 130", "thin"), line(420, 40, 380 , 210),
        "\n".join(line(x, 0, x, 120, "thin") for x in (20, 40, 560, 580)),
        "\n".join(line(0 if x < 300 else 540, y, 60 if x < 300 else 600, y, "thin") for x in (0, 600) for y in (30, 60, 90)),
    )

    svg("silver-pen", "A hand raising a silver pen, light pouring out from it in every direction",
        rays(300, 120, 30, 140, 24, "accent"),
        line(300, 120, 340, 260), path("M300 120 L294 106 L304 108 Z", "fill-accent"),
        path("M320 220 Q300 230 300 260 L310 320 M360 230 Q380 250 376 280 L370 320"),
        path("M330 230 Q340 210 356 220", "thin"),
        circle(300, 120, 10, "accent"),
    )

    svg("slide", "A long, wobbly slide drawn down the mountainside, with a loop in it",
        path("M120 40 L60 120 L20 320 M120 40 L200 100 L260 200 L300 320"),
        path("M140 50 Q200 120 260 140 Q330 160 330 200 Q330 240 300 230 Q270 220 290 196 Q320 170 380 230 Q450 300 600 300"),
        path("M150 60 Q206 130 264 150 Q320 166 320 200", "thin"), path("M390 236 Q456 290 600 290", "thin"),
        path("M0 200 Q60 180 120 196 Q180 176 240 194 Q300 180 360 196 Q420 182 480 194", "thin"),
        person(160, 70, 0.5, arms=(-10, -14, 10, -14)), crow_shape(240, 40, 0.6),
        rect(540, 230, 30, 60), circle(564, 260, 2, "fill"),
    )

    svg("new-road", "A road being drawn out into blank white space, grass and trees appearing beside it as it goes",
        path("M0 300 Q120 260 240 240 Q360 220 420 200", ""), path("M0 320 Q130 286 250 266 Q370 246 430 222", ""),
        path("M420 200 Q450 194 470 186 M430 222 Q456 214 480 204", "thin"),
        "\n".join(tree(x, y, h, h * 0.5) for x, y, h in ((60, 270, 70), (130, 250, 60), (200, 236, 50), (290, 220, 36))),
        "\n".join(path(f"M{x} {y} l3 -8 l3 8", "thin") for x, y in ((80, 300), (160, 280), (240, 266), (320, 250), (380, 236))),
        line(500, 190, 560, 100), path("M500 190 L494 200 L496 186 Z", "fill-accent"),
        path("M100 180 Q130 150 170 170 Q200 140 250 170", "thin"),
        path("M330 210 Q350 200 380 206", "accent"),
    )

    svg("shop-sign", "The map shop's front with a bell over the door and a crow perched on the hanging sign",
        rect(150, 80, 300, 220), path("M140 80 L300 30 L460 80"),
        rect(270, 190, 60, 110), circle(318, 246, 3, "fill"),
        rect(170, 180, 80, 70), rect(350, 180, 80, 70), line(210, 180, 210, 250, "thin"), line(390, 180, 390, 250, "thin"),
        path("M296 176 Q300 166 304 176 Z"), line(300, 166, 300, 160, "thin"),
        line(450, 110, 520, 110), line(470, 110, 470, 126, "thin"), line(510, 110, 510, 126, "thin"),
        rect(456, 126, 70, 40), path("M466 150 L480 136 L494 148 L514 134", "accent"),
        crow_shape(492, 110, 0.8),
        line(0, 300, W, 300),
    )


def draw_more_long_quiet():
    svg("scan", "A medical screen showing a brain scan, a bright smudge shrinking day by day",
        rect(80, 40, 440, 240, "", 8),
        "\n".join(ellipse(160 + i * 90, 140, 36, 46, "thin") + ellipse(160 + i * 90, 140, 28, 38, "thin") for i in range(4)),
        "\n".join(circle(150 + i * 90, 124, 14 - i * 3, "accent") for i in range(4)),
        "\n".join(line(110, y, 300 - (y % 4) * 20, y, "thin") for y in range(210, 262, 12)),
        path("M340 250 L370 230 L390 240 L420 210 L450 236 L480 220", "accent"),
        line(300, 280, 300, 300), line(240, 300, 360, 300),
    )

    svg("cabin", "A tiny cabin: bunk, porthole, a photo of two children on a beach and a crayon drawing of a rocket",
        rect(60, 200, 300, 30), line(60, 230, 60, 300), path("M60 200 L60 120", "thin"),
        rect(80, 186, 60, 14, "thin", 5),
        porthole(470, 90, 40),
        rect(200, 70, 90, 70), circle(230, 116, 6, "thin"), circle(260, 112, 6, "thin"), line(200, 126, 290, 126, "thin"),
        path("M200 120 Q245 110 290 120", "thin"),
        rect(320, 60, 70, 90, "thin"),
        path("M350 130 L350 90 L355 76 L360 90 L360 130 Z", "accent"), path("M350 120 L342 132 M360 120 L368 132", "accent"),
        circle(355, 100, 4, "thin"),
        rect(420, 200, 140, 12), line(430, 212, 430, 300, "thin"),
        rect(460, 172, 30, 28, "thin"),
        line(0, 300, W, 300),
    )

    pulses = []
    x = 60
    for n in (2, 3, 5, 7, 11):
        for i in range(n):
            pulses.append(line(x, 160, x, 110, "accent"))
            x += 7
        x += 22
    svg("waveform", "The signal drawn as pulses: two, three, five, seven, eleven",
        line(40, 160, 560, 160, "thin"),
        "\n".join(pulses),
        "\n".join(f'<text x="{tx}" y="200" text-anchor="middle" class="fill" style="font: 14px Literata, Georgia, serif; stroke: none">{n}</text>'
                  for tx, n in ((64, 2), (101, 3), (151, 5), (215, 7), (306, 11))),
        path("M420 260 Q450 120 480 220 Q510 300 540 160 Q560 90 580 140", "thin"),
        path("M40 260 Q100 230 160 250 Q220 270 280 240 Q340 210 400 250", "thin"),
    )

    racks = []
    for i in range(3):
        y = 90 + i * 60
        racks.append(line(30, y, 380, y))
        for x in range(50, 370, 40):
            racks.append(path(f"M{x} {y} Q{x - 10} {y - 22} {x - 4} {y - 30} M{x} {y} Q{x + 10} {y - 20} {x + 6} {y - 32}", "thin"))
            racks.append(circle(x, y - 14, 2, "fill-accent"))
    svg("greenhouse", "Racks of glowing plants and, at the end, a tall sunflower with a point of light at its heart",
        "\n".join(racks),
        line(470, 300, 470, 120), path("M470 200 Q440 190 430 170 M470 230 Q500 220 510 200", "thin"),
        circle(470, 96, 26), rays(470, 96, 26, 50, 16, ""), circle(470, 96, 6, "fill-accent"), rays(470, 96, 8, 18, 8, "accent"),
        rect(450, 280, 40, 20),
        path("M30 290 Q120 280 200 290 Q280 300 380 288", "accent"),
        line(0, 300, W, 300),
    )

    svg("pipes", "Rerouting pipes by torchlight in a cramped access space",
        path("M0 80 L380 80 Q420 80 420 120 L420 320"), path("M0 100 L370 100 Q400 100 400 130 L400 320", "thin"),
        path("M600 160 L200 160 Q160 160 160 200 L160 320"), path("M600 176 L210 176 Q176 176 176 210 L176 320", "thin"),
        path("M170 250 Q250 300 300 260 Q340 230 410 240", "accent"),
        "\n".join(rect(x - 6, y - 10, 12, 20, "") for x, y in ((300, 90), (250, 168), (410, 200))),
        path("M500 260 L560 230 L566 244 L506 272 Z"), path("M500 260 L380 200 M506 272 L380 300", "accent"),
        path("M560 230 Q590 220 600 236", "thin"),
    )

    svg("comms", "A screen showing a tired flight director, the station's antenna cable climbing away above",
        rect(120, 60, 360, 200, "", 8),
        circle(300, 140, 34), path("M266 130 Q270 96 300 96 Q332 96 334 130", "thin"), path("M240 240 Q250 184 300 182 Q350 184 360 240"),
        "\n".join(person(x, 250, 0.45) for x in (170, 200, 410, 440)),
        line(300, 0, 300, 60, "thin"), line(306, 0, 306, 60, "thin"),
        "\n".join(circle(150 + i * 20, 280, 4, "fill-accent" if i == 0 else "thin") for i in range(4)),
        path("M480 280 L560 280 L548 300 L492 300 Z"),
    )

    svg("transmitter", "A laptop on a folding table by the pool rail, pulses of sound going down into the glowing water",
        rect(140, 150, 120, 70, "", 4), path("M130 220 L270 220 L280 230 L120 230 Z"),
        rect(160, 166, 80, 10, "thin"), rect(160, 186, 30, 20, "accent"),
        line(110, 230, 290, 230), line(130, 230, 120, 300), line(270, 230, 280, 300),
        line(0, 240, W, 240, "thin"),
        ellipse(450, 290, 150, 26), dots_in(40, lambda x, y: ((x - 450) / 140) ** 2 + ((y - 290) / 22) ** 2 < 1, 45),
        "\n".join(path(f"M{350 + i * 30} {200 + i * 12} q20 -12 40 0", "accent") for i in range(4)),
    )

    sleepers = []
    for i, (x, y) in enumerate(((150, 250), (230, 268), (330, 268), (410, 250), (290, 240))):
        sleepers.append(ellipse(x, y, 34, 8))
        sleepers.append(circle(x - 30, y - 4, 7))
        sleepers.append(path(f"M{x - 30} {y - 12} Q{x - 20} {y - 80} {x} {y - 140}", "accent"))
    svg("dome", "Five sleepers lying in a ring inside a glassy dome, glowing fronds resting on their foreheads",
        path("M60 290 Q60 60 300 50 Q540 60 540 290"), path("M80 290 Q84 80 300 70 Q516 80 520 290", "thin"),
        "\n".join(sleepers),
        sub(300, 200, 0.45, lit=False),
        line(0, 290, W, 290),
        dots(40, 0, 0, 600, 60, 46, 1, 2),
    )

    svg("crew", "Six figures standing together in the dome, looking up at the lights",
        path("M40 290 Q40 50 300 40 Q560 50 560 290", "thin"),
        "\n".join(person(x, 290, 1.1, arms=(-10, 20, 10, 20)) for x in (150, 210, 270, 330, 390, 450)),
        dots(80, 60, 50, 540, 160, 47, 1, 2.4),
        line(0, 290, W, 290),
    )

    svg("two-subs", "Two submarines climbing side by side through the dark, a cloud of lights rising with them",
        sub(200, 200, 0.9), sub(410, 130, 1.0),
        dots(90, 0, 0, W, H, 48, 1, 2.2),
        "\n".join(path(f"M{x} 320 q-4 -10 0 -20", "thin") for x in (180, 230, 400, 440)),
    )

    svg("signal-up", "A single beam of light pointing straight up, and every light in the water turning to follow it",
        line(300, 300, 300, 0, "accent"), line(292, 300, 292, 0, "thin"), line(308, 300, 308, 0, "thin"),
        rect(280, 290, 40, 20),
        "\n".join(line(x, y, x + (300 - x) * 0.05, y - 18, "accent") for x, y in
                  ((60, 120), (120, 200), (180, 80), (420, 90), (480, 210), (540, 130), (100, 260), (500, 270), (220, 240), (380, 230))),
        dots(60, 0, 20, W, 300, 49, 1, 2),
        line(0, 310, W, 310),
    )

    spiral = []
    for arm in range(3):
        for i in range(70):
            t = i / 70
            a = arm * 2 * math.pi / 3 + t * 4 * math.pi
            r = 10 + t * 150
            spiral.append(circle(300 + r * math.cos(a), 160 + r * 0.7 * math.sin(a), 1 + t * 2.4, "fill-accent"))
    svg("choir-mind", "A vast slow spiral of light, like a galaxy, spread across the deep",
        "\n".join(spiral), circle(300, 160, 10, "accent"),
        dots(50, 0, 0, W, H, 50, 0.8, 1.6, "fill"),
    )

    svg("winch", "A winch drum turning slowly, hauling the drill cable up out of the shaft",
        ellipse(240, 140, 30, 70), ellipse(420, 140, 30, 70), line(240, 70, 420, 70), line(240, 210, 420, 210),
        "\n".join(path(f"M{x} 72 Q{x + 12} 140 {x} 208", "thin") for x in range(260, 420, 14)),
        rect(180, 210, 300, 20), line(200, 230, 190, 300), line(460, 230, 470, 300),
        path("M330 210 L330 320", ""), path("M336 210 L336 320", "thin"),
        path("M90 140 A26 26 0 1 1 116 166", "accent"), path("M116 166 L108 154 M116 166 L124 156", "accent"),
        line(0, 300, W, 300),
    )

    svg("ascent-pod", "A narrow capsule rising up a shaft through the ice",
        path("M240 0 L240 320 M360 0 L360 320"),
        hatch(0, 0, 238, 320, 16, "thin"), hatch(362, 0, 600, 320, 16, "thin"),
        path("M270 120 Q270 60 300 40 Q330 60 330 120 L330 220 L270 220 Z"),
        circle(300, 100, 10, "thin"), line(270, 180, 330, 180, "thin"),
        path("M280 220 L276 250 M300 220 L300 260 M320 220 L324 250", "accent"),
        path("M120 60 L160 100 L130 150 M470 40 L440 110 L480 170", "thin"),
    )

    svg("station", "The station hanging beneath the ice, the greenhouse windows glowing, the ocean lit faintly far below",
        path("M0 0 L600 0 L600 60 Q500 80 400 64 Q300 84 200 66 Q100 80 0 62 Z"), hatch(0, 0, 600, 60, 14, "thin"),
        line(300, 64, 300, 110), rect(180, 110, 240, 50, "", 20), rect(130, 124, 50, 24, "", 10), rect(420, 124, 60, 24, "", 10),
        "\n".join(circle(x, 135, 6, "fill-accent") for x in (210, 240, 270, 300, 330, 360, 390)),
        line(300, 160, 300, 190, "thin"), ellipse(300, 196, 30, 6, "thin"),
        dots(60, 0, 250, W, 318, 51, 1, 2),
        path("M0 300 Q150 280 300 296 Q450 310 600 290", "thin"),
    )



if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    draw_gull_rock()
    draw_inkwold()
    draw_long_quiet()
    draw_more_gull_rock()
    draw_more_inkwold()
    draw_more_long_quiet()
    draw_favicon()
    print("Wrote", len([f for f in os.listdir(OUT) if f.endswith(".svg")]), "files to art/")
