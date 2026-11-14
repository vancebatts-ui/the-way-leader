# Way Leader Reels — art-first rebuild, state as of 2026-11-13 evening

Picking this up in a new session? Read this file, then `compose.py` and `render_art.swift`.
Everything needed is here; nothing is only in a chat transcript.

## PRE-SHIP REVIEW, 2026-11-13/14 — what it caught and what it changed

A 16-agent review (6 independent lenses over the three cuts, each serious finding handed to a
skeptic told to refute it) returned **7 confirmed, 3 refuted, 10 low-severity**. Full output:
`tasks/wulmaf2h3.output` in the session dir. It was worth running — it caught two blockers I
had personally signed off on. Run it again before any future batch ships.

**Blockers it caught, both since fixed by regenerating the art:**
1. *Post 4 read Southern European / Mediterranean, not Levantine.* Loose waves not ringlets, a
   brown beard, a narrow straight nose, a light hazel eye, a rosy malar flush. I had approved
   that face from a 310px thumbnail without zooming in — the same mistake as the first round,
   one notch subtler. **"Not European" in a prompt does not exclude Greek or Italian.** The
   corrected prompt names them: *NOT Greek, NOT Italian, NOT Southern European or Mediterranean;
   no ruddy flush; no light, hazel, green or blue eyes.* Judge faces at 600px+, never at thumbnail.
2. *Post 5 had a ruled full-width horizontal band at 56% height* — a tabletop edge behind the arm,
   the exact artifact the brief says to reject. Cause was the prompt's own line "Below 55% height:
   plain umber shadow" — the generator read that as a hard-edged fill. Rewritten to demand a
   continuous imperceptible gradient and to name every forbidden edge.

**Code defects it caught, all fixed in `compose.py`:**
- **The handle sat BELOW the safe area on all three posts** (ink to y=1513/1519/1527 against a
  1499 limit). Root cause: `d.text()` for the handle had no `anchor`, so PIL defaulted to `"la"`
  (ascender top) while every other y in the file is a baseline via `draw_runs(anchor="ls")`.
  The configured numbers had been written as if they were the bottom of the type. Fixed with
  `anchor="ls"`, `rule_y`/`handle_y` moved to 1400/1470 on all three, and — more importantly —
  **`check_ink()` now measures the lowest bright pixel on every build and raises `SystemExit`
  rather than writing a frame that crosses `SAFE_BOTTOM`.** This class of bug cannot ship again.
- **Post 4's art was the flattest of the three at thumbnail size.** `grade()` applied one identical
  recipe to all three; it now takes a per-post `contrast`, and post4 runs at 1.35 instead of 1.06.
- **The chapter tag was the weakest element for contrast** (down to 2.6:1 over bright art, because
  it often sits above the scrim's reach). Now gets two shade passes, a wide soft halo then a tight one.

**Still open, because it touches his words — ASK, do not fix silently:**
Post 5's quote is configured at 76pt but silently autofits down to **65pt**, because two of its four
lines exceed the 960px column. At 65pt it is the smallest type in the series and weakest at feed
size. The reviewer's proposed fix edits the quote ("It is the faithfulness you **keep** on hard
ones"). **That is his sentence from his own book — it is not ours to trim.** Options to put to him:
accept 65pt, re-break the lines, widen the column, or approve a shorter wording himself.

**Low-severity notes worth his eye, not acted on:** the Furnace reads to one lens as *burning at
the stake*, and "ask permission" is consent language; Post 4's fist at the jaw could read as a hand
at the throat at thumbnail scale (the Post 4 regeneration already moved the fist clear of the neck).

**A process rule learned the hard way:** art5.png was overwritten *while the review agents were
reading it*, so that run's Post 5 findings were contaminated and partly unusable. Never change the
inputs under a running review.

## SHIPPED 2026-11-14 00:49 ET — this job is DONE

Vance approved all three ("Go, Brother"). Pushed as commit `98c7117` and swapped into
Metricool. Nothing is outstanding.

| Post | Figure | Cut (live) | Fires | Metricool id | uuid |
|---|---|---|---|---|---|
| 4 — The War Within | Judean man, fist at the jaw | `WL-Post04-The-War-Within-Reel-v3.mp4` | Mon 11/16 10:00 | 427756554 | -3543980373235055961 |
| 5 — Cost of the Covenant | Black African hand on the tzitzit | `WL-Post05-Cost-of-the-Covenant-Reel-v4.mp4` | Wed 11/18 10:00 | 427756642 | 4357966642178835969 |
| 6 — The Furnace | Judean man in the fire | `WL-Post06-The-Furnace-Reel-v4.mp4` | Fri 11/20 10:00 | 427756714 | -895706748583525836 |

All three: `draft:false`, `isAiGenerated:true`, real `mediaAltText`, captions verbatim and
untouched. Served from `https://vancebatts-ui.github.io/the-way-leader/media/` — all 200, and
each one's sha256 verified against both the local render and Metricool's stored copy.
`WL-Post06-The-Furnace-Reel-v2.mp4` (the European figure) was deleted and now 404s.

Final measurements on the shipped set: horizontal-band score 0.0 / −9.6 / 0.0 (the rejected
Post 5 scored −70.5); lowest type ink y=1475 on all three against a 1499 limit; thumbnail value
spread 110 / 130 / 92 (Post 4 was 69 before its own grade).

**Still open, and it is his call, not ours:** Post 5's quote renders at 65pt, not the configured
76pt — see the review section above. He was told, and shipping at 65pt was the decision, because
the alternative was editing his sentence.

## Getting art out of Canva when the MCP connector is gone

The Canva MCP server was removed from this session mid-task and could not be re-added
(`set_session_connector_enabled` reported Canva was not available to the session at all, even
after Vance confirmed it showed active in his connector list). A session only picks up
connectors that existed when it started. **The browser pane worked instead, and is now the
proven path** — `canva.com/dream-lab`, already signed in:

1. Set the aspect selector to 9:16 (check `btns[3].innerText` on the prompt form).
2. **Dream Lab silently truncates the prompt at 1500 characters** — `maxlength="1500"` on the
   textarea, no warning. Count before pasting. A 1557-char prompt lost its no-text negative.
3. `cmd+a`+Delete does NOT clear the React-controlled textarea. Set it through the native
   setter and fire a bubbling input event:
   ```js
   const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set
   setter.call(ta, prompt); ta.dispatchEvent(new Event('input', {bubbles:true}))
   ```
4. Click the form's `Submit` button. Four variants come back.
5. To judge them, pull the thumbnails: the `<img>` srcs at `media.canva.com/v2/image-resize/...width:310`
   carry signed csig/osig — curl them as-is and build a contact sheet. The signature params
   cannot be edited for a bigger size.
6. For full resolution click the variant's **"Download generated image"** button. It lands in
   `~/Downloads` with the prompt as the filename (~8–9 MB JPG, 1536×2720). **The newest
   generation's four buttons are at the TOP of the `find` results**, older sets below.
7. Cover-crop to frame: `s = max(1080/w, 1920/h)`, LANCZOS resize, centre crop 1080×1920.

## The correction that drives this rebuild

2026-11-13, Vance: *"I want you to look at my previous illustrations and notice that i went
with historical accuracy as to how the people looked from the region and also included
multiple ethinticty to appeal to everyone for the message is for all."*

Two generated figures (Chapter 4 and Chapter 6) came back European and are **rejected**.
Full direction in `~/.claude/projects/-Users-buddyb/memory/feedback-illustration-art-direction.md`.
His 28 reference plates: Google Drive `My Drive/ChatGPT Image *.png` and
`My Drive/Downloads (1)/ChatGPT Image *.png`.

Short version: default every figure to historically accurate Near Eastern/Levantine — deep
olive-brown skin, dark eyes, black hair and beard, Semitic features — say "not European"
explicitly in the prompt, and **vary ethnicity across the three posts** so the set reads as
for everyone. Never fix it by recolouring a European face.

## Where the three posts stand

| Post | Chapter | Fires | Metricool id | uuid | State |
|---|---|---|---|---|---|
| 4 | 4 — The War Within | Mon 11/16 10:00 ET | 423989784 | -3543980373235055961 | **untouched**, old text card, `draft:false` — publishes as-is |
| 5 | 5 — Cost of the Covenant | Wed 11/18 10:00 ET | 423989810 | 4357966642178835969 | **untouched**, old text card, `draft:false` — publishes as-is |
| 6 | 6 — The Furnace | Fri 11/20 10:00 ET | **427647674** | -895706748583525836 | holds the v2 cut whose figure was European → **set to `draft:true` 11/13**, cannot fire |

**Post 4 fires Monday 11/16.** If his yes does not come before then, it publishes the old text
card. That is not a disaster — the card is fine, it is just the format the rebuild replaces —
but it is the one deadline in this job. Posts 5 and 6 have more room.

brandId `7351037`, timezone `America/New_York`. Every update changes the id; the uuid never
changes. Captions are verbatim from his Formation Series doc — **do not reword them**; read
the live caption back with `getScheduledPosts` and send it unchanged.

`isAiGenerated` was set **true** on Post 6 when the AI artwork went in. Keep it true on any
post carrying generated art — his motto is "Hate a lie even if it helps you." He has not
objected, but he also has not commented on it; worth confirming once.

## Build pipeline

```bash
python3 compose.py post4      # -> post4_art_graded.png, post4_overlay.png, post4_preview.png
swift render_art.swift <dir> post4_art_graded.png post4_overlay.png score_war.m4a WL-Post04-...-v2.mp4
```

- `compose.py` holds a `POSTS` dict: art filename, chapter number, the quote **with the
  card's own line breaks**, type sizes and the y positions. It grades the art toward the
  brand umber (saturation 0.78, umber tint 0.18), builds the bottom scrim and sets the quote
  in faked small caps in Big Caslon, then writes a flat preview. Quote lines auto-shrink to a
  960px column, so a long quote cannot overrun — Post 5 falls from 76pt to 65pt this way.
  All type lands above y=1500, clear of Instagram's caption bar and buttons.
- `render_art.swift` takes `dir art overlay score out`. 12s, 1080x1920, 30fps. The art pushes
  in 1.0→1.065 while the overlay holds still and fades up between 0.5s and 1.9s, then a fade
  to black over the final second, then the AAC score is muxed in and stills are written at
  0/1.2/3/7/11.5s. **Look at the stills before shipping.**
- Scores already exist (built by `score.py`): `score_war`, `score_covenant`, `score_furnace`.
  Grab them from the 11-10 session scratchpad or regenerate with `score.py`.

Quotes, verbatim from the Canva cards:
- Post 4: "Not every voice / in your head / is your own."
- Post 5: "Emunah is not the faith / you feel on good days. / It is the faithfulness / you maintain on hard ones."
- Post 6: "Fire does not / ask permission."

## Getting full-resolution art out of Canva — the MCP path (only if the connector is back)

Not needed if you use the browser pane above. Kept because it is hard-won and faster when the
connector exists. `generate-image` returns only a media id and a ~112px thumbnail — **no download URL**. The
way out: `resize-design` an existing card to 1080x1920 (new design, original untouched),
`read-design` with `open_transaction`, `edit-design` to delete the template elements and
`insert_fill` the media at 0,0 full-bleed, `commit`, then `export-design` as PNG at that size
and curl the URL. **Export URLs expire in under a day — download immediately.**
Working design from the last run: `DAHaq_z0sVc`. Source cards: Post 4 `DAHak1CAWjE`,
Post 5 `DAHakyg-tJs`, Post 6 `DAHak1BA_uk`.

Other image generators checked 11-13: Higgsfield is on a free plan with **0 credits**; Figma
bills Figma AI credits and has to write into a Figma file. Canva Pro is the intended path.

## The three prompts — these are the ones that produced the art now in hand

These came out of a 14-agent concept-and-judge pass (concepts → three single-criterion judges
→ synthesis). The subjects survived the panel; only the ethnicity lines are new. **Posts 4 and
5 had to be cut down to fit Dream Lab's 1500-character cap**; the full uncut versions are in
`art-prompts/`, and the trimmed one actually used for Post 5 is in the scratchpad as
`p5_prompt.txt` (1490 chars). If you reroll, trim from the style and surface language, never
from the ethnicity clause or the no-text / no-border negatives — those are the failure modes
that actually bit.

### Post 6 — The Furnace (used 11-13; variant 1 of 4)

> Full-bleed vertical sepia illustration in the style of a Leonardo da Vinci sanguine chalk
> and brown-ink study on aged parchment. A strong, powerfully built Judean man of the ancient
> Near East — deep olive-brown skin, dark brown eyes, black tightly curled hair and a full
> black beard, authentic Semitic Middle Eastern features, historically accurate to Babylon-era
> Judah and emphatically not European — stands firm and upright inside a furnace, flames
> surrounding him on all sides and rising past his shoulders, his head lifted and his hands
> open at his sides. He is unburned. He wears a simple rough undyed tunic. Fine Renaissance
> cross-hatching, soft umber and ochre wash, deep chiaroscuro, the fire drawn as elegant
> curling tongues of flame with glowing embers. A faint thin ruled geometric circle is lightly
> compass-drawn on the background behind his head like a construction line on an anatomy study
> sheet, a drafting mark and not a glowing halo. The figure is large in the frame, filling most
> of the height, seen from just below the knees up, and his face sits in the upper third. The
> artwork bleeds edge to edge with no frame, no border, no margin, no vignette box. Absolutely
> no text, no letters, no numbers, no writing, no Hebrew or any other script, no signature, no
> watermark anywhere in the image.

### Post 4 — The War Within ("voice-at-his-shoulder") — used 11-13; **variant 2 of 4**

`art-prompts/post4-war-within.txt`, trimmed to fit 1500, with the ethnicity clause inserted
after "a single bearded man in his forties": *a Levantine man of the ancient Near East, warm
brown skin, dark eyes, black hair and a full black beard, Semitic features, not European.*
Subject: head and shoulders, head turned sharply off axis, eyes fixed past his own shoulder as
if weighing a voice beside his ear, one hand braced closed against the jaw with the knuckles
lit as a single plane, deep empty shadow behind him with **nothing resolving in it**.
All four variants came back correctly Levantine. Took #2 for the sharpest gaze and the clearest
lit knuckles.

### Post 5 — Cost of the Covenant ("the-daily-hold") — used 11-13; **variant 1 of 4**

`art-prompts/post5-covenant.txt` cut to 1490 chars (`p5_prompt.txt` in the scratchpad), with
the arm specified as *deep dark brown, a Black African labourer's arm, emphatically not
European and not pale* — this is the post that carries the second ethnicity in the set.
Subject: one bare forearm and one fist gripping a frayed hemp rope under load, rope taking a
turn around the forearm, running up over a worn grooved stone edge in the top-left corner, the
weight never shown.
All four came back anatomically clean (one hand, five fingers, no phantom arm) — the failure
the panel most feared did not happen. **But three of the four put a hard horizontal line across
the frame** where the lit upper field meets the dark lower one, which is the "no horizontal
band" failure the check list calls out; the scrim is far too weak at that height to hide it.
Variant 1 is the only one with a soft diagonal fall-off. If you reroll this concept, push
harder on *no horizon, no visible ground plane, continuous graded background*.

Check each returned image against: no painted or decorative border; no stray lettering; the
figure large and the emotional centre in the **top half**; the bottom 45% empty enough for the
scrim; correct hands (five fingers, no duplicates); warm umber/ochre/sanguine only.

## What to do once the art is in hand

1. Save as `art4.png` / `art5.png` / `art6.png` next to `compose.py`.
2. `python3 compose.py postN`, look at `postN_preview.png`.
3. Render, look at the stills, **send the cut to Vance and wait for his yes.**
4. Copy into `media/` as `WL-PostNN-...-v2.mp4`, commit, push, wait for the Pages URL to 200.
5. `updateScheduledPost` with the new URL, the caption read back unchanged, `draft:false` for
   4 and 5, and `draft:false` for 6 only once he has approved the corrected Furnace.
6. Verify Metricool's stored copy matches: `curl` the returned `static.metricool.com` URL and
   compare sha256 against the local file. It matched byte for byte on every post so far.

Push needs the explicit credential helper:
`git -c credential.helper= -c credential.helper='!/Users/buddyb/bin/gh auth git-credential' push`
