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

# The Play store set, recaptured from the watch each release.
WEAR_SRC = pathlib.Path(r"C:\Users\jwden\FootyWear\docs\store\wear")

# ⚠️ THE SITE SHOWS SCREENS THE STORE SET DOES NOT, AND THIS IS WHERE THEY LIVE. Play takes at
# most EIGHT screenshots and the page illustrates nine things, so three of the site's images have
# never been in the store set - and on 16 Aug, when the store set was recaptured and renamed, this
# script broke: it was still asking for wear-05-spoiler-mode, wear-06-finals and wear-04-club-theme
# by their old names and would have reported every source missing.
#
# A second folder rather than a longer store set, because the two are chosen for different reasons:
# the store set is the eight that sell the app, this is whatever the page happens to show. Keeping
# them apart means recapturing one cannot silently empty the other.
WEAR_SITE_SRC = pathlib.Path(r"C:\Users\jwden\FootyWear\docs\store\wear-site")

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
    # (source folder, source file) -> the name the page asks for.
    #
    # ⚠️ THE FILENAMES ON THE LEFT ARE THE STORE SET'S AND THE STORE SET GETS RENUMBERED. It was
    # renumbered on 16 Aug when the whole set was recaptured from the watch, which is what turned
    # this dictionary into eight missing sources. If this script reports one, look at what is in
    # docs/store/wear before assuming a capture failed.
    wear = {
        (WEAR_SRC, "wear-01-scoreboard.png"): "w-round.png",
        (WEAR_SRC, "wear-02-match-detail.png"): "w-match.png",
        (WEAR_SRC, "wear-03-goal-feed.png"): "w-goals.png",
        (WEAR_SRC, "wear-07-tile.png"): "w-tile.png",
        # THE LADDER GALLERY SLOT USED TO BE THE APPLE CAPTURE, and on 16 Aug its caption stopped
        # being true of it: the Wear table gained column headings and a percentage column, the
        # caption was updated to say so, and the picture beside it showed neither. Same
        # caption/image mismatch as the fantasy section, so the same answer - show the screen the
        # words are about. Apple still has the whole "Two watches" section to itself.
        (WEAR_SRC, "wear-05-ladder.png"): "w-ladder.png",
        # THE SECOND COMPETITION, WITH ITS OWN HEADING. Added 13 Aug with the sectioned board.
        # The page claimed "AFL and AFLW in the one app" and illustrated it with nothing, which
        # is the one line on the page a reader is most likely to want proof of.
        (WEAR_SRC, "wear-06-aflw.png"): "w-aflw.png",
        # ⚠️ THE REAL FANTASY SCREEN, not a stand-in. This used to come from a layout-audit folder
        # rather than the store set, and the first cut of the fantasy section on the site was
        # illustrated with the GOAL FEED under alt text describing fantasy scorers - the same
        # caption/image mismatch already caught once on the ladder. It is now a store capture, so
        # the picture on the page and the picture on Play are the same screen.
        (WEAR_SRC, "wear-08-top-scorers.png"): "w-fantasy.png",
        # The three the store set has no room for. See WEAR_SITE_SRC.
        (WEAR_SITE_SRC, "wear-05-spoiler-mode.png"): "w-spoilers.png",
        (WEAR_SITE_SRC, "wear-06-finals.png"): "w-finals.png",
        (WEAR_SITE_SRC, "wear-04-club-theme.png"): "w-club.png",
    }
    missing = [f"{d.name}/{s}" for (d, s) in wear if not (d / s).exists()]
    if missing:
        print(f"  MISSING SOURCES: {missing}")
        return 1
    for (folder, s), d in wear.items():
        round_watch(folder / s, OUT / d)

    apple_src = pathlib.Path(
        r"C:\Users\jwden\AppData\Local\Temp\claude\C--Users-jwden--local-bin"
        r"\d9e0b64f-f287-4fc3-a418-472e979aec47\scratchpad\apple")
    # Only the frames the page actually uses. Generating the rest just leaves dead weight in the
    # repo that looks like it is on the site and is not.
    #
    # a-ladder went out of use on 16 Aug when the gallery slot moved to the Wear table - it is
    # kept here because the Apple ladder is one edit away from being wanted again and the
    # capture folder is a temp path that will not survive being needed later.
    APPLE_USED = {"a2_scoreboard": "a-scoreboard.png", "a3_ladder": "a-ladder.png"}
    if apple_src.exists():
        print("Apple (rounded rectangle):")
        for stem, out in APPLE_USED.items():
            src = apple_src / f"{stem}.png"
            if src.exists():
                apple_watch(src, OUT / out)
            else:
                print(f"  MISSING {src.name}")
    else:
        print(f"no Apple captures at {apple_src} yet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
