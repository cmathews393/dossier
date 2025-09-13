#!/usr/bin/env python3
"""
Generate a mapping from local display names -> Sherlock provider keys (slugs).

Writes: src/lib/platforms_map.json

Heuristics:
 - Try case-insensitive exact match
 - Try normalized match (lower, strip non-alnum)
 - Try name variants (replace dot with space, underscores)
 - If multiple matches, prefer exact ci, then shortest key
 - Unmatched items map to null and are reported
"""

import json
import re
import sys
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
LOCAL_PLATFORMS = ROOT / "src/lib/platforms.json"
OUT_PATH = ROOT / "src/lib/platforms_map.json"
SHERLOCK_URLS = [
    "https://raw.githubusercontent.com/sherlock-project/sherlock/master/sherlock_project/resources/data.json",
    "https://raw.githubusercontent.com/sherlock-project/sherlock/main/sherlock_project/resources/data.json",
]


def normalize(s: str) -> str:
    s = s or ""
    s = s.lower()
    s = s.replace("&", "and")
    # remove punctuation except alnum
    s = re.sub(r"[^a-z0-9]", "", s)
    return s


def load_sherlock_data():
    last_err = None
    for url in SHERLOCK_URLS:
        try:
            with urlopen(url, timeout=15) as r:
                raw = r.read().decode("utf-8")
                data = json.loads(raw)
                return data
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Failed to fetch sherlock data.json: {last_err}")


def main():
    if not LOCAL_PLATFORMS.exists():
        print(f"Local platforms file not found: {LOCAL_PLATFORMS}")
        sys.exit(2)

    local = json.loads(LOCAL_PLATFORMS.read_text())
    sherlock = load_sherlock_data()
    sherlock_keys = list(sherlock.keys())

    # build normalization index for sherlock keys
    index = {}
    for k in sherlock_keys:
        nk = normalize(k)
        index.setdefault(nk, []).append(k)

    mapping = {}
    unmatched = []

    for display in local:
        # try case-insensitive exact
        found = None
        for k in sherlock_keys:
            if k.lower() == str(display).lower():
                found = k
                break
        if not found:
            nd = normalize(display)
            candidates = index.get(nd) or []
            if len(candidates) == 1:
                found = candidates[0]
            elif len(candidates) > 1:
                # prefer exact case-insensitive if present
                for c in candidates:
                    if c.lower() == str(display).lower():
                        found = c
                        break
                if not found:
                    # prefer shortest key (likely the slug-like one)
                    found = sorted(candidates, key=len)[0]

        if not found:
            mapping[display] = None
            unmatched.append(display)
        else:
            mapping[display] = found

    OUT_PATH.write_text(json.dumps(mapping, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT_PATH}")
    if unmatched:
        print(f"Unmatched ({len(unmatched)}):\n" + ", ".join(unmatched[:200]))


if __name__ == "__main__":
    main()
