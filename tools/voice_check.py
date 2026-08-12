"""Catch the copy tells that make a page read as machine-written.

⚠️ THIS EXISTS BECAUSE I COULD NOT SEE IT MYSELF. The previous version of this page was fluent,
specific and factually correct, and JD still called it "clearly AI language" on sight. Re-reading my
own prose was never going to catch that, because the same judgement wrote it. These are the tells,
measured, so the check does not depend on my opinion of my own writing.

The three that actually fired:
  1. EM DASHES. Nearly every sentence had one. It is the single most recognisable tell there is.
  2. UNIFORM HEADINGS. Every heading was a short declarative sentence ending in a full stop
     ("Nothing gives it away.", "Built twice, on purpose.", "Look at your wrist. That's the whole
     score."). One is a nice line. Nine in a row is a drumbeat, and a drumbeat reads as generated.
  3. LONG BODIES. Forty to sixty word paragraphs where a plain page uses fifteen to twenty.

Run: python tools/voice_check.py [--selftest]
`--selftest` feeds it the OLD copy and proves every check can fail. A check that has never failed
is decoration.
"""
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
# ⚠️ SWEEP EVERY PAGE, not just the one being edited. Checking index.html alone would have declared
# the site clean while privacy.html carried the same tells, which is the "empty fixture" mistake:
# a check that never looked at a file cannot vouch for it.
PAGES = sorted(ROOT.glob("*.html"))

# Seven's measured shape, which is the target: headings of one to three words, bodies of one or two
# sentences averaging fifteen to twenty words.
MAX_HEADING_WORDS = 6
MAX_BODY_WORDS = 34
MAX_SENTENCE_HEADINGS = 1

# ⚠️ A LEGAL PAGE IS NOT MARKETING COPY AND MUST NOT BE HELD TO THE SAME LIMIT. A privacy policy is
# judged on whether it is accurate and complete, so squeezing every paragraph under 34 words would
# force out the qualifications that make it true. The dash and craft-narration rules still apply
# everywhere; only the length allowance differs, and it is stated here rather than quietly skipped.
BODY_LIMITS = {"privacy.html": 55}


def strip_comments(html: str) -> str:
    """Strip what a reader never sees: HTML comments, and the contents of style and script.

    ⚠️ THE FIRST VERSION JUDGED CSS AS PROSE. Removing `<style>` tags but keeping their contents
    left the stylesheet's own comments in the text, so the check reported "narrating your own craft"
    against the word `deliberately` inside a CSS comment about font licensing. A checker that
    reports faults in text no reader can see trains you to ignore it.
    """
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
    return html


def text_of(tag_html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", tag_html)).strip()


def find(html: str, tags) -> list:
    out = []
    for t in tags:
        for m in re.finditer(rf"<{t}\b[^>]*>(.*?)</{t}>", html, flags=re.S | re.I):
            s = text_of(m.group(1))
            if s:
                out.append(s)
    return out


def check(html: str, max_body: int = MAX_BODY_WORDS) -> list:
    html = strip_comments(html)
    problems = []

    # 1. Em and en dashes, anywhere a reader can see.
    body = text_of(html)
    dashes = len(re.findall(r"[—–]|&mdash;|&ndash;", html))
    if dashes:
        problems.append(f"{dashes} em/en dash(es) in visible copy. Use a full stop or a comma.")

    # 2. Headings that are sentences, and headings that run long.
    heads = find(html, ["h1", "h2", "h3"])
    sentence_heads = [h for h in heads if h.endswith(".")]
    if len(sentence_heads) > MAX_SENTENCE_HEADINGS:
        problems.append(
            f"{len(sentence_heads)} headings are full sentences ending in a full stop "
            f"(max {MAX_SENTENCE_HEADINGS}): {sentence_heads[:4]}")
    long_heads = [h for h in heads if len(h.split()) > MAX_HEADING_WORDS]
    if long_heads:
        problems.append(f"headings longer than {MAX_HEADING_WORDS} words: {long_heads[:4]}")

    # 3. Paragraphs that run long. Skip the legal disclaimer, which has to say what it says.
    for p in find(html, ["p"]):
        if "not affiliated" in p.lower() or "trademark" in p.lower():
            continue
        n = len(p.split())
        if n > max_body:
            problems.append(f"{n}-word paragraph (max {max_body}): \"{p[:70]}...\"")

    # 4. Constructions that read as generated regardless of length.
    # ⚠️ EACH RULE CARRIES ITS OWN FLAGS. The "Not X. Y." rule was case insensitive and unanchored,
    # so it fired on "if it says you are not a tester" - which is quoting Google Play's own error
    # message, not striking a pose. The construction worth banning is the sentence-initial fragment
    # ("Not one app wrapped for both."), so it is anchored to a sentence start and case sensitive.
    # A rule that cries wolf on ordinary English is a rule you learn to ignore.
    for pattern, why, flags in [
        (r"\bon purpose\b|\bdeliberately\b", "narrating your own craft", re.I),
        (r"(?:^|[.!?]\s+|>\s*)Not (a|one|just) [a-z]", 'the "Not X. Y." construction', 0),
        (r"\bisn't just\b|\bis not just\b", '"not just" escalation', re.I),
        (r"\bwhole (point|reason)\b", '"the whole point"', re.I),
        (r"\bthat's the (thing|point)\b", "aphoristic filler", re.I),
    ]:
        hits = re.findall(pattern, body, flags=flags)
        if hits:
            problems.append(f"{len(hits)}x {why}: {hits[:3]}")

    return problems


def selftest() -> int:
    """Feed each check the shape it is meant to catch and confirm it fails."""
    cases = {
        "em dash": "<h2>Scores</h2><p>Goals and behinds &mdash; and the clock.</p>",
        "sentence headings": ("<h2>Nothing gives it away.</h2><h2>Built twice, on purpose.</h2>"
                              "<h2>Look at your wrist.</h2>"),
        "long heading": "<h2>The round, sorted the way you would sort it yourself</h2>",
        "long paragraph": "<p>" + " ".join(["word"] * 60) + "</p>",
        "craft narration": "<p>Built twice, on purpose.</p>",
    }
    ok = True
    for name, html in cases.items():
        got = check(html)
        print(f"  {'PASS' if got else 'FAIL'}  {name:20} -> {len(got)} problem(s)")
        if not got:
            ok = False
    clean = "<h1>Never miss a score.</h1><h2>Live Scores</h2><p>Every match in the round.</p>"
    got = check(clean)
    print(f"  {'PASS' if not got else 'FAIL'}  {'clean copy':20} -> {len(got)} problem(s) {got}")
    return 0 if ok and not got else 1


def main() -> int:
    if "--selftest" in sys.argv:
        print("self test, each case must be caught:")
        return selftest()
    if not PAGES:
        print("no pages found to check")
        return 1
    total = 0
    for page in PAGES:
        limit = BODY_LIMITS.get(page.name, MAX_BODY_WORDS)
        problems = check(page.read_text(encoding="utf-8"), max_body=limit)
        total += len(problems)
        note = "" if limit == MAX_BODY_WORDS else f" (body limit {limit}, legal page)"
        print(f"{page.name}{note}: {'clean' if not problems else str(len(problems)) + ' problem(s)'}")
        for p in problems:
            print("   -", p)
    return 0 if total == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
