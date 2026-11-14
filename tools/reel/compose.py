#!/usr/bin/env python3
"""Compose the art-first Furnace Reel frame: graded artwork + a separate type overlay.

Writes art_graded.png (1080x1920 RGB) and overlay.png (1080x1920 RGBA).
render_art.swift draws the art with a slow push-in and fades the overlay in on top.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

D = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920

CREAM = (245, 230, 202)
GOLD = (212, 172, 110)
TAG = (228, 192, 132)
SCRIM = (22, 13, 6)

CASLON = "/System/Library/Fonts/Supplemental/BigCaslon.ttf"

HANDLE = "@_esotericechoes_7"

# One entry per post. Line breaks are the card's own. Sizes are tuned so each
# block lands above y=1500, clear of Instagram's caption bar and buttons.
# SAFE_BOTTOM: no ink may fall below this. Instagram draws the author row,
# caption and audio ticker under it. compose.py MEASURES this every run and
# refuses to write the files if anything crosses the line — see check_ink().
SAFE_BOTTOM = 1499

# rule_y / handle_y are BASELINES (anchor "ls"), like every other y here.
# They were ascender-tops for the handle until 2026-11-14, which silently put
# the handle 13-27px below SAFE_BOTTOM on all three posts.
POSTS = {
    "post4": dict(
        art="art4.png", chapter=4,
        quote=["Not every voice", "in your head", "is your own."],
        big=96, small=74, tag_y=1006, first_y=1122, step=116,
        rule_y=1400, handle_y=1470, scrim_y0=700,
        contrast=1.35,   # this art is the flattest of the three at thumbnail size
    ),
    "post5": dict(
        art="art5.png", chapter=5,
        quote=["Emunah is not the faith", "you feel on good days.",
               "It is the faithfulness", "you maintain on hard ones."],
        big=76, small=58, tag_y=972, first_y=1070, step=92,
        rule_y=1400, handle_y=1470, scrim_y0=640,
        contrast=1.06,
    ),
    "post6": dict(
        art="art6.png", chapter=6,
        quote=["Fire does not", "ask permission."],
        big=112, small=86, tag_y=1062, first_y=1182, step=132,
        rule_y=1400, handle_y=1470, scrim_y0=740,
        contrast=1.06,
    ),
}


# ---------------------------------------------------------------- small caps
def smallcaps_runs(word, big, small):
    """[(char, font)] — first letter at full size, the rest as smaller caps."""
    out = []
    for i, ch in enumerate(word):
        out.append((ch.upper(), big if i == 0 else small))
    return out


def line_runs(text, big, small):
    runs = []
    for i, word in enumerate(text.split(" ")):
        if i:
            runs.append((" ", big))
        runs.extend(smallcaps_runs(word, big, small))
    return runs


def runs_width(draw, runs, track=0):
    w = 0
    for ch, f in runs:
        w += draw.textlength(ch, font=f) + track
    return w - track if runs else 0


def draw_runs(draw, runs, x, y, fill, track=0, anchor="ls"):
    for ch, f in runs:
        draw.text((x, y), ch, font=f, fill=fill, anchor=anchor)
        x += draw.textlength(ch, font=f) + track


def draw_runs_centred(draw, runs, cx, y, fill, track=0):
    w = runs_width(draw, runs, track)
    draw_runs(draw, runs, cx - w / 2, y, fill, track)


# ---------------------------------------------------------------- the artwork
def grade(path_in, path_out, contrast=1.06):
    im = Image.open(path_in).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    # pull the orange back toward the brand's umber/parchment sepia
    im = ImageEnhance.Color(im).enhance(0.78)
    # contrast is per-post: a flat illustration dies at thumbnail size, where
    # most of the audience decides whether to keep watching
    im = ImageEnhance.Contrast(im).enhance(contrast)
    # warm umber cast, gentle
    tint = Image.new("RGB", (W, H), (168, 124, 72))
    im = Image.blend(im, Image.blend(im, tint, 0.18), 1.0)
    im = ImageEnhance.Brightness(im).enhance(0.97)
    im.save(path_out)
    return im


# ---------------------------------------------------------------- the overlay
def overlay(path_out, cfg):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # bottom scrim: transparent at y0, deep umber by the base
    y0, y1, peak = cfg['scrim_y0'], H, 242
    grad = Image.new("L", (1, H), 0)
    gp = grad.load()
    for y in range(H):
        if y <= y0:
            a = 0.0
        else:
            t = (y - y0) / (y1 - y0)
            a = t * t * (3 - 2 * t)          # smoothstep
        gp[0, y] = int(peak * a)
    mask = grad.resize((W, H))
    ov.paste(Image.new("RGBA", (W, H), SCRIM + (255,)), (0, 0), mask)

    # a whisper of shade at the very top so the frame reads as a composed piece
    tg = Image.new("L", (1, H), 0)
    tp = tg.load()
    for y in range(H):
        tp[0, y] = int(70 * max(0.0, 1 - y / 420) ** 1.6)
    ov.paste(Image.new("RGBA", (W, H), SCRIM + (255,)), (0, 0), tg.resize((W, H)))

    from PIL import ImageFilter
    d = ImageDraw.Draw(ov)

    def shade(fn, blur=8, dy=4, alpha=185):
        """Lay a blurred dark copy of whatever fn draws under the real thing."""
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fn(ImageDraw.Draw(layer), dy, (10, 6, 2, alpha))
        ov.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))

    # chapter tag
    f_tag = ImageFont.truetype(CASLON, 30)
    TAGLINE = "THE WAY LEADER  —  CHAPTER %d" % cfg["chapter"]
    tagw = d.textlength(TAGLINE, font=f_tag) + 6 * (len(TAGLINE) - 1)
    tag_runs = [(c, f_tag) for c in TAGLINE]
    # The tag is small, letterspaced and often sits above the scrim's reach, so
    # it was the weakest element for contrast (down to 2.6:1 over bright art).
    # Two passes: a wide soft halo to darken the ground, then a tight one.
    shade(lambda dd, dy, col: draw_runs(dd, tag_runs, (W - tagw) / 2, cfg['tag_y'] + dy, col, track=6),
          blur=18, dy=2, alpha=235)
    shade(lambda dd, dy, col: draw_runs(dd, tag_runs, (W - tagw) / 2, cfg['tag_y'] + dy, col, track=6),
          blur=6, dy=2, alpha=215)
    d = ImageDraw.Draw(ov)
    draw_runs(d, tag_runs, (W - tagw) / 2, cfg['tag_y'], TAG, track=6)

    # the quote, in small caps — shrunk to fit if any line would overrun the
    # text column, keeping the block centred where the config put it
    MAXW = 960
    big_sz, small_sz, step = cfg['big'], cfg['small'], cfg['step']
    big = ImageFont.truetype(CASLON, big_sz)
    small = ImageFont.truetype(CASLON, small_sz)
    widest = max(runs_width(d, line_runs(l, big, small), 2) for l in cfg['quote'])
    if widest > MAXW:
        k = MAXW / widest
        big_sz, small_sz, step = (max(1, int(v * k)) for v in (big_sz, small_sz, step))
        big = ImageFont.truetype(CASLON, big_sz)
        small = ImageFont.truetype(CASLON, small_sz)
        print("  fit: %s -> %dpt/%dpt (widest line was %dpx)" % (cfg['art'], big_sz, small_sz, widest))

    n = len(cfg['quote'])
    centre = cfg['first_y'] + cfg['step'] * (n - 1) / 2
    first_y = centre - step * (n - 1) / 2
    ys = [first_y + i * step for i in range(n)]
    for line, y in zip(cfg['quote'], ys):
        runs = line_runs(line, big, small)
        w = runs_width(d, runs, 2)
        # soft drop shadow so the type holds over the flames
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        draw_runs(sd, runs, (W - w) / 2, y + 5, (14, 8, 3, 180), track=2)
        ov.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(9)))
        d = ImageDraw.Draw(ov)
        draw_runs(d, runs, (W - w) / 2, y, CREAM + (255,), track=2)

    # hairline rule under the quote
    d.line([(W / 2 - 110, cfg['rule_y']), (W / 2 + 110, cfg['rule_y'])], fill=GOLD + (165,), width=2)

    # handle
    # anchor="ls" — baseline, matching draw_runs() and every other y in this file.
    # Without it PIL defaults to "la" (ascender top) and the handle renders ~35px
    # lower than the config implies, which is how it ended up below SAFE_BOTTOM.
    f_h = ImageFont.truetype(CASLON, 30)
    shade(lambda dd, dy, col: dd.text((76, cfg['handle_y'] + dy), HANDLE, font=f_h, fill=col, anchor="ls"),
          blur=6, dy=3)
    d = ImageDraw.Draw(ov)
    d.text((76, cfg['handle_y']), HANDLE, font=f_h, fill=GOLD + (240,), anchor="ls")

    check_ink(ov, path_out)   # refuses to save if any type crosses SAFE_BOTTOM
    ov.save(path_out)
    return ov


def check_ink(ov, key):
    """Measure the lowest bright ink in the overlay. Raise if it crosses SAFE_BOTTOM.

    The handle bug shipped because the y values were trusted instead of measured.
    This makes that impossible: every build either prints the real number or stops.
    """
    px = ov.load()
    lowest, where = -1, None
    for y in range(H - 1, 0, -1):
        for x in range(0, W, 2):
            r, g, b, a = px[x, y]
            if a >= 40 and r >= 140:        # cream/gold letterform core only
                if y > lowest:
                    lowest, where = y, x
                break
        if lowest >= 0:
            break
    margin = SAFE_BOTTOM - lowest
    print("  ink: lowest bright pixel y=%d (x=%s), %d px %s SAFE_BOTTOM=%d"
          % (lowest, where, abs(margin), "clear of" if margin >= 0 else "BELOW", SAFE_BOTTOM))
    if margin < 0:
        raise SystemExit(
            "REFUSING to write %s: type crosses the Instagram safe area by %dpx."
            % (key, -margin))
    return lowest


if __name__ == "__main__":
    import sys
    key = sys.argv[1] if len(sys.argv) > 1 else "post6"
    cfg = POSTS[key]
    art = grade(os.path.join(D, cfg["art"]), os.path.join(D, "%s_art_graded.png" % key),
                contrast=cfg.get("contrast", 1.06))
    ov = overlay(os.path.join(D, "%s_overlay.png" % key), cfg)
    flat = art.convert("RGBA")
    flat.alpha_composite(ov)
    flat.convert("RGB").save(os.path.join(D, "%s_preview.png" % key))
    print("wrote %s_art_graded.png, %s_overlay.png, %s_preview.png" % (key, key, key))
