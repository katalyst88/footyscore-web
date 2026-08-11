# footyscore.app

The site, the privacy policy, and the app's runtime settings file. Public on purpose: it holds no
secrets, only a switch and two intervals.

Served by **GitHub Pages** at the apex domain `footyscore.app`. Cloudflare holds the DNS and
nothing else.

## ⚠️ Cloudflare must stay DNS-only (grey cloud), not proxied

Two reasons, and the first is the one that matters.

1. **The privacy policy names who receives the request.** Proxied, Cloudflare would see every
   config fetch — the watch's IP and the time — and that is a third party in the data path which
   the policy would have to disclose. DNS-only, GitHub Pages is the only recipient, which is what
   the policy says.
2. Proxying GitHub Pages needs the SSL mode set to Full or it is an infinite redirect loop, and it
   interferes with GitHub issuing its certificate in the first place.

`.app` is on the HSTS preload list, so HTTPS is not optional and there is no plain-HTTP fallback.
GitHub Pages issues the certificate. "Enforce HTTPS" must be ticked in the repository's Pages
settings.

## ⚠️ `config.json` lives in TWO places and both are live

`RemoteConfig.DEFAULT_URL` is compiled into the app, so **every build already installed keeps
asking `katalyst88.github.io/footyscores-config/config.json` for as long as it exists.** That repo
can never be deleted, and a change made only here reaches nobody who installed before the move.

Flip the switch with `push_config.py` in this repo, which writes both and reads both back. Do not
edit one by hand.

## The files

| | |
|---|---|
| `index.html`, `styles.css` | The site. Hand written, no build step. |
| `privacy.html` | Linked from the Play listing and from the app. |
| `config.json` | The runtime switch the app reads every fifteen minutes. |
| `fonts/` | Fraunces and Hanken Grotesk, self hosted. Shared with watchwalks.com; nothing else about the design is. |

## config.json

```json
{ "config": "footyscores", "espn": "on", "livePollSeconds": 30, "idlePollMinutes": 60, "notice": null }
```

The `config` marker is mandatory and is what makes "last known good" mean anything: the parser
ignores unknown keys, so without a required field any well formed JSON served at this URL — a
Cloudflare error page, an SPA's index fallback, the wrong file uploaded — would decode into a full
set of defaults, ESPN ON, and be written over a cached "off".

Only a literal `"off"` disables ESPN. A typo, an empty string or a missing key all mean ON, because
the safe state is the working state. Both intervals are clamped by the app (live 10–600 seconds,
idle 5–1440 minutes), so a slip of the finger cannot park the poll 68 years out or wake the watch
every second.
