"""Turn raw simulator captures into the marketing imagery the site uses.

⚠️ THE ROUND DISPLAY IS THE WHOLE PROBLEM. The Wear captures are SQUARE 454x454 pictures of a
ROUND screen, so their corners hold rows the watch itself clips away — put one on a web page
unmasked and the bottom of the screen looks broken, as though the app were cut off. Every Wear
frame is masked to a circle here. Apple's display is a rounded rectangle and is masked to that.

⚠️ THE BEZEL IS DRAWN, NOT A STOCK DEVICE MOCKUP. A downloaded render of somebody's watch is the
single most recognisable "made in twenty minutes" tell, it dates the moment Apple ships a new case,
and its perspective never matches the flat screenshot pasted into it. This is a plain ring in the
app's own palette: it reads as a watch without pretending to be a photograph of one.

Everything is written at 2x and the page asks for it at half size, so it stays sharp on a retina
display without shipping a 4K asset.
"""
import pathlib
from PIL import Image, ImageDraw

OUT = pathlib.Path(__file__).resolve().parent.parent / "img"
WEAR_SRC = pathlib.Path(r"C:\Users\jwden\FootyWear\docs\store\wear")

# The app's own palette, so the frames belong to the product rather than to a stock kit.
INK = (10, 10, 11)
BEZEL = (32, 33, 36)
RIM = (74, 76, 82)

SCALE = 2
ROUND_D = 300 * SCALE          # the round watch face diameter on the page
BAND = 14 * SCALE              # bezel thickness


def _supersample(size):
    """Draw big and shrink: PIL has no anti-aliased circle, and a jagged bezel is a tell."""
    return size * 4


def round_watch(src: pathlib.Path, dst: pathlib.Path) -> None:
    inner = ROUND_D - BAND * 2
    face = Image.open(src).convert("RGB").resize((inner, inner), Image.LANCZOS)

    # Circular mask for the face, built oversized then downsampled for a clean edge.
    big = _supersample(inner)
    m = Image.new("L", (big, big), 0)
    ImageDraw.Draw(m).ellipse((0, 0, big - 1, big - 1), fill=255)
    mask = m.resize((inner, inner), Image.LANCZOS)

    canvas = Image.new("RGBA", (ROUND_D, ROUND_D), (0, 0, 0, 0))

    # The bezel: an outer ring in case colour with a slightly lighter rim, so the edge reads.
    bigc = _supersample(ROUND_D)
    ring = Image.new("RGBA", (bigc, bigc), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.ellipse((0, 0, bigc - 1, bigc - 1), fill=BEZEL + (255,))
    rd.ellipse((0, 0, bigc - 1, bigc - 1), outline=RIM + (255,), width=2 * 4)
    canvas.alpha_composite(ring.resize((ROUND_D, ROUND_D), Image.LANCZOS))

    canvas.paste(face, (BAND, BAND), mask)
    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dst)
    print(f"  {dst.name:34} {canvas.size}")


def apple_watch(src: pathlib.Path, dst: pathlib.Path) -> None:
    face = Image.open(src).convert("RGB")
    w, h = face.size
    scale = (250 * SCALE) / h
    inner = (int(w * scale), int(h * scale))
    face = face.resize(inner, Image.LANCZOS)

    # Apple's display is a rounded rectangle with a generous radius, and the case is more generous
    # still. Two radii, because one radius for both is what makes a drawn device look like a box.
    face_r = int(min(inner) * 0.24)
    big = (inner[0] * 4, inner[1] * 4)
    m = Image.new("L", big, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, big[0] - 1, big[1] - 1), radius=face_r * 4, fill=255)
    mask = m.resize(inner, Image.LANCZOS)

    total = (inner[0] + BAND * 2, inner[1] + BAND * 2)
    case_r = face_r + BAND
    bigc = (total[0] * 4, total[1] * 4)
    ring = Image.new("RGBA", bigc, (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.rounded_rectangle((0, 0, bigc[0] - 1, bigc[1] - 1), radius=case_r * 4, fill=BEZEL + (255,))
    rd.rounded_rectangle((0, 0, bigc[0] - 1, bigc[1] - 1), radius=case_r * 4,
                         outline=RIM + (255,), width=2 * 4)
    canvas = ring.resize(total, Image.LANCZOS)

    canvas.paste(face, (BAND, BAND), mask)
    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dst)
    print(f"  {dst.name:34} {canvas.size}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    print("Wear (round, masked):")
    wear = {
        "wear-01-scoreboard.png": "w-round.png",
        "wear-02-match-detail.png": "w-match.png",
        "wear-03-alerts-grid.png": "w-alerts.png",
        "wear-05-spoiler-mode.png": "w-spoilers.png",
        "wear-06-finals.png": "w-finals.png",
        "wear-07-tile.png": "w-tile.png",
        "wear-08-goal-feed.png": "w-goals.png",
        "wear-04-club-theme.png": "w-club.png",
    }
    missing = [s for s in wear if not (WEAR_SRC / s).exists()]
    if missing:
        print(f"  MISSING SOURCES: {missing}")
        return 1
    for s, d in wear.items():
        round_watch(WEAR_SRC / s, OUT / d)

    apple_src = pathlib.Path(
        r"C:\Users\jwden\AppData\Local\Temp\claude\C--Users-jwden--local-bin"
        r"\d9e0b64f-f287-4fc3-a418-472e979aec47\scratchpad\apple")
    if apple_src.exists():
        print("Apple (rounded rectangle):")
        for f in sorted(apple_src.glob("*.png")):
            apple_watch(f, OUT / f"a-{f.stem.split('_')[-1]}.png")
    else:
        print(f"no Apple captures at {apple_src} yet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
