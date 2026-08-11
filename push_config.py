#!/usr/bin/env python3
"""Write the runtime config to BOTH hosts and read both back.

THE SWITCH LIVES IN TWO PLACES AND WILL FOR YEARS. `RemoteConfig.DEFAULT_URL` is compiled into the
app, so every build installed before the move to footyscore.app keeps asking
`katalyst88.github.io/footyscores-config/config.json` for as long as that URL answers. Editing one
by hand flips the switch for half the fleet and leaves no sign that it did.

This is the only supported way to change it. It writes both repositories, commits, pushes, waits
for GitHub Pages to serve the new bytes, and then FETCHES BOTH URLS and compares them to what it
meant to publish — because a push that succeeded is not a file that is being served.

    python push_config.py --espn off --notice "ESPN is down; scores may be stale."
    python push_config.py --espn on --notice ""      # clear the notice
    python push_config.py --show                     # what is live right now

Requires `git` with push rights to both repositories.
"""
import argparse, json, subprocess, sys, time, urllib.request, pathlib

HERE = pathlib.Path(__file__).resolve().parent

# Both live copies. The first is the new home; the second is the one older installs still read.
TARGETS = [
    {"name": "footyscore.app",
     "repo": HERE,
     "file": HERE / "config.json",
     "url": "https://footyscore.app/config.json"},
    {"name": "github pages mirror",
     "repo": HERE.parent / "footyscores-config",
     "file": HERE.parent / "footyscores-config" / "config.json",
     "url": "https://katalyst88.github.io/footyscores-config/config.json"},
]

MARKER = "footyscores"


def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"__error__": str(e)}


def show():
    for t in TARGETS:
        print(f"{t['name']:24} {t['url']}")
        print(f"{'':24} {json.dumps(fetch(t['url']))}")


def build(args, current):
    cfg = dict(current)
    cfg["config"] = MARKER
    if args.espn is not None:
        cfg["espn"] = args.espn
    if args.live is not None:
        cfg["livePollSeconds"] = args.live
    if args.idle is not None:
        cfg["idlePollMinutes"] = args.idle
    if args.notice is not None:
        cfg["notice"] = args.notice or None
    # Key order fixed so a diff shows a changed VALUE rather than a reshuffled file.
    return {k: cfg.get(k) for k in
            ["config", "espn", "livePollSeconds", "idlePollMinutes", "notice"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--espn", choices=["on", "off"])
    ap.add_argument("--live", type=int, help="live poll seconds (the app clamps to 10-600)")
    ap.add_argument("--idle", type=int, help="idle poll minutes (the app clamps to 5-1440)")
    ap.add_argument("--notice", help='a line shown in the app; "" clears it')
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    if args.show or not any([args.espn, args.live, args.idle, args.notice is not None]):
        show()
        return 0

    current = json.loads(TARGETS[0]["file"].read_text(encoding="utf-8"))
    wanted = build(args, current)
    body = json.dumps(wanted, indent=2) + "\n"
    print("publishing:", json.dumps(wanted))

    missing = [t["name"] for t in TARGETS if not t["repo"].is_dir()]
    if missing:
        print(f"FAILED: these checkouts are not on this machine: {missing}")
        print("Both must be published together, so nothing was written.")
        return 1

    for t in TARGETS:
        t["file"].write_text(body, encoding="utf-8", newline="\n")
        subprocess.run(["git", "add", t["file"].name], cwd=t["repo"], check=True)
        r = subprocess.run(["git", "commit", "-m", f"config: {json.dumps(wanted)}"],
                           cwd=t["repo"], capture_output=True, text=True)
        if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
            print(f"FAILED to commit {t['name']}: {r.stdout}{r.stderr}")
            return 1
        subprocess.run(["git", "push", "-q"], cwd=t["repo"], check=True)
        print(f"pushed  {t['name']}")

    # READ IT BACK. Pages takes a moment, and a push that succeeded is not a file being served.
    print("waiting for both to serve the new bytes ...")
    deadline = time.time() + 180
    pending = {t["name"]: t for t in TARGETS}
    while pending and time.time() < deadline:
        time.sleep(10)
        for name in list(pending):
            live = fetch(pending[name]["url"])
            if live == wanted:
                print(f"live    {name}")
                del pending[name]

    if pending:
        print(f"\nNOT SERVING THE NEW CONFIG YET: {list(pending)}")
        print("The push went through, so this is Pages being slow rather than a failure. Re-run")
        print("with --show in a few minutes. Do NOT assume the switch has taken effect until both")
        print("read back, because the app that matters may be reading the one that has not.")
        return 1

    print("\nboth hosts serving the same config.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
