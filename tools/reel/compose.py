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

QUOTE = ["Fire does not", "ask permission."]
TAGLINE = "THE WAY LEADER  —  CHAPTER 6"
HANDLE = "@_esotericechoes_7"


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
def grade(path_in, path_out):
    im = Image.open(path_in).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    # pull the orange back toward the brand's umber/parchment sepia
    im = ImageEnhance.Color(im).enhance(0.78)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    # warm umber cast, gentle
    tint = Image.new("RGB", (W, H), (168, 124, 72))
    im = Image.blend(im, Image.blend(im, tint, 0.18), 1.0)
    im = ImageEnhance.Brightness(im).enhance(0.97)
    im.save(path_out)
    return im


# ---------------------------------------------------------------- the overlay
def overlay(path_out):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # bottom scrim: transparent at y0, deep umber by the base
    y0, y1, peak = 740, H, 242
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
    tagw = d.textlength(TAGLINE, font=f_tag) + 6 * (len(TAGLINE) - 1)
    tag_runs = [(c, f_tag) for c in TAGLINE]
    shade(lambda dd, dy, col: draw_runs(dd, tag_runs, (W - tagw) / 2, 1062 + dy, col, track=6),
          blur=7, dy=3)
    d = ImageDraw.Draw(ov)
    draw_runs(d, tag_runs, (W - tagw) / 2, 1062, TAG, track=6)

    # the quote, in small caps
    big = ImageFont.truetype(CASLON, 112)
    small = ImageFont.truetype(CASLON, 86)
    ys = [1182, 1314]
    for line, y in zip(QUOTE, ys):
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
    d.line([(W / 2 - 110, 1424), (W / 2 + 110, 1424)], fill=GOLD + (165,), width=2)

    # handle
    f_h = ImageFont.truetype(CASLON, 30)
    shade(lambda dd, dy, col: dd.text((76, 1478 + dy), HANDLE, font=f_h, fill=col), blur=6, dy=3)
    d = ImageDraw.Draw(ov)
    d.text((76, 1478), HANDLE, font=f_h, fill=GOLD + (240,))

    ov.save(path_out)
    return ov


if __name__ == "__main__":
    art = grade(os.path.join(D, "art6.png"), os.path.join(D, "art_graded.png"))
    ov = overlay(os.path.join(D, "overlay.png"))
    flat = art.convert("RGBA")
    flat.alpha_composite(ov)
    flat.convert("RGB").save(os.path.join(D, "preview_frame.png"))
    print("wrote art_graded.png, overlay.png, preview_frame.png")
