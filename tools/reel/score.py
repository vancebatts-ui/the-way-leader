"""Original 12s score for the Post 1 Reel: D-minor drone, slow pad, four sparse piano-like notes, small-room reverb.
Pure stdlib so it runs without numpy. Writes score.wav (44.1 kHz, 16-bit stereo)."""
import math, wave, struct, array, sys

SR = 44100
DUR = 12.0
N = int(SR * DUR)
L = array.array('d', [0.0]) * N
R = array.array('d', [0.0]) * N
TAU = 2 * math.pi


def env_swell(t, start, attack, end, release):
    if t < start or t > end:
        return 0.0
    a = min(1.0, (t - start) / attack)
    r = min(1.0, (end - t) / release)
    # raised-cosine curves sound gentler than linear ramps
    return (0.5 - 0.5 * math.cos(math.pi * a)) * (0.5 - 0.5 * math.cos(math.pi * r))


def add_tone(freq, amp, start, attack, end, release, pan=0.0, detune=0.0, harmonics=((1, 1.0), (2, 0.18))):
    gl = math.cos((pan + 1) * math.pi / 4)
    gr = math.sin((pan + 1) * math.pi / 4)
    f = freq * (1 + detune)
    i0, i1 = int(start * SR), min(N, int(end * SR))
    for i in range(i0, i1):
        t = i / SR
        e = env_swell(t, start, attack, end, release) * amp
        if e == 0.0:
            continue
        # slow breathing tremolo keeps the pad alive
        e *= 0.88 + 0.12 * math.sin(TAU * 0.23 * t + freq)
        s = 0.0
        for h, ha in harmonics:
            s += ha * math.sin(TAU * f * h * t)
        L[i] += s * e * gl
        R[i] += s * e * gr


def add_piano(freq, amp, start, pan=0.0, length=4.5):
    gl = math.cos((pan + 1) * math.pi / 4)
    gr = math.sin((pan + 1) * math.pi / 4)
    parts = ((1, 1.0, 1.1), (2, 0.42, 1.8), (3, 0.16, 2.6), (4, 0.07, 3.4), (5, 0.03, 4.5))
    i0, i1 = int(start * SR), min(N, int((start + length) * SR))
    for i in range(i0, i1):
        t = (i - i0) / SR
        atk = min(1.0, t / 0.006)
        s = 0.0
        for h, ha, decay in parts:
            # slight inharmonicity, like a real string
            fh = freq * h * (1 + 0.0004 * h * h)
            s += ha * math.exp(-decay * t) * math.sin(TAU * fh * t)
        v = s * amp * atk
        L[i] += v * gl
        R[i] += v * gr


D2, A2, D3, F3, Fs3, A3, E4 = 73.42, 110.0, 146.83, 174.61, 185.00, 220.0, 329.63
D4, E4n, F4, Fs4, G4, A4, B4, D5 = 293.66, 329.63, 349.23, 369.99, 392.00, 440.0, 493.88, 587.33

# argv[1] picks the piece; each is a pad chord plus four melody notes on the same beats
PIECES = {
    # Post 1, The Calling: minor, melody resolving home A - F - E - D
    'calling': (((D3, 0.10), (F3, 0.075), (A3, 0.07), (E4, 0.04)), (A4, F4, E4n, D4)),
    # Post 2, The Call to Truth: minor, rising out of the cage D - F - A - D
    'truth': (((D3, 0.10), (F3, 0.075), (A3, 0.07), (E4, 0.04)), (D4, F4, A4, D5)),
    # Post 3, The Way Revealed: major, a morning hymn F# - A - B - A
    'way': (((D3, 0.10), (Fs3, 0.075), (A3, 0.07), (E4, 0.04)), (Fs4, A4, B4, A4)),
    # Post 4, The War Within: minor, the half-step rub A - Bb - A, left hanging on E
    'war': (((D3, 0.10), (F3, 0.075), (A3, 0.07), (E4, 0.04)), (A4, 466.16, A4, E4n)),
    # Post 5, The Cost of the Covenant: minor, patient, keeps returning home F - E - D - D
    'covenant': (((D3, 0.10), (F3, 0.075), (A3, 0.07), (E4, 0.04)), (F4, E4n, D4, D4)),
    # Post 6, The Furnace: darker pad (no added 9th), descending, then one rise for the fourth man
    'furnace': (((D3, 0.12), (F3, 0.085), (A3, 0.06)), (F4, D4, 261.63, A4)),
}
piece = sys.argv[1] if len(sys.argv) > 1 else 'calling'
pad, melody = PIECES[piece]

# drone
add_tone(D2, 0.30, 0.0, 2.5, DUR, 2.5, pan=0.0)
add_tone(A2, 0.16, 0.6, 3.0, DUR, 2.5, pan=0.0)
# pad, two slightly detuned voices per note spread left/right
for fr, a in pad:
    add_tone(fr, a, 1.4, 3.5, DUR, 2.8, pan=-0.55, detune=-0.0016)
    add_tone(fr, a, 1.4, 3.5, DUR, 2.8, pan=0.55, detune=0.0016)
# sparse melody, four notes
for (start, amp, pan, length), fr in zip(((1.0, 0.20, 0.15, 4.5), (3.9, 0.19, -0.1, 4.5),
                                          (6.7, 0.18, 0.1, 4.5), (9.2, 0.21, 0.0, 2.8)), melody):
    add_piano(fr, amp, start, pan=pan, length=length)


def reverb(x, wet=0.28):
    # Schroeder: 4 parallel combs into 2 series allpasses
    out = array.array('d', [0.0]) * N
    for d, g in ((1557, 0.80), (1617, 0.79), (1491, 0.81), (1422, 0.78)):
        buf = array.array('d', [0.0]) * N
        for i in range(N):
            y = x[i] + (g * buf[i - d] if i >= d else 0.0)
            buf[i] = y
            out[i] += y * 0.25
    for d, g in ((225, 0.5), (556, 0.5)):
        y = array.array('d', [0.0]) * N
        for i in range(N):
            xd = out[i - d] if i >= d else 0.0
            yd = y[i - d] if i >= d else 0.0
            y[i] = -g * out[i] + xd + g * yd
        out = y
    return array.array('d', (x[i] * (1 - wet) + out[i] * wet for i in range(N)))


L = reverb(L)
R = reverb(R)

# master fade: in over 0.4s, out over the last 2s
for i in range(N):
    t = i / SR
    g = min(1.0, t / 0.4) * min(1.0, (DUR - t) / 2.0)
    L[i] *= g
    R[i] *= g

peak = max(max(abs(v) for v in L), max(abs(v) for v in R))
scale = (10 ** (-3 / 20)) / peak
with wave.open(f'score_{piece}.wav', 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    frames = bytearray()
    for i in range(N):
        frames += struct.pack('<hh', int(L[i] * scale * 32767), int(R[i] * scale * 32767))
    w.writeframes(bytes(frames))
print(f'wrote score_{piece}.wav, peak scaled by', round(scale, 3))
