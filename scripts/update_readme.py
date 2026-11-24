#!/usr/bin/env python3
"""Regenerate the SNS links section of this profile README.

Source of truth: the LINKS array in dosTaiyaki/linklist's script.js.
The generated block replaces everything between the LINKS:START and
LINKS:END markers in README.md. Links that have a shields.io badge
mapping are rendered as badges; the rest become plain text bullets so
no link is ever dropped.

Usage:
    python3 scripts/update_readme.py [--readme PATH] [--source PATH]

Without --source, script.js is downloaded from the linklist repo.
"""

import argparse
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT_JS_URL = (
    "https://raw.githubusercontent.com/dosTaiyaki/linklist/main/script.js"
)
START = "<!-- LINKS:START -->"
END = "<!-- LINKS:END -->"

BADGE_STYLE = "style=for-the-badge"


def badge(alt, label, color, logo, url):
    img = (
        f"https://img.shields.io/badge/{label}-{color}"
        f"?{BADGE_STYLE}&logo={logo}&logoColor=white"
    )
    return f"[![{alt}]({img})]({url})"


def render(label, url):
    """Return one markdown line for a link, or None for a text bullet."""
    if "note.com/qa/" in url:
        return None  # Q&A box: no distinct badge, use a text bullet
    if "discord.com/invite/" in url:
        return badge("Discord (community)", "Discord_(community)",
                     "5865F2", "discord", url)
    if "discord.com/users/" in url:
        return badge("Discord", "Discord", "5865F2", "discord", url)
    if "x.com/" in url:
        if url.rstrip("/").endswith("_sub"):
            return badge("X (sub)", "X_(sub)", "000000", "x", url)
        return badge("X (main)", "X_(main)", "000000", "x", url)
    if "youtube.com" in url:
        return badge("YouTube", "YouTube", "FF0000", "youtube", url)
    if "instagram.com" in url:
        return badge("Instagram", "Instagram", "E4405F", "instagram", url)
    if "threads.com" in url or "threads.net" in url:
        return badge("Threads", "Threads", "000000", "threads", url)
    if "misskey.io" in url:
        return badge("Misskey", "Misskey", "A1CA03", "misskey", url)
    if "note.com" in url:
        return badge("note", "note", "111111", "note", url)
    if url.startswith("mailto:"):
        return badge("Email", "Email", "D14836", "gmail", url)
    return None


def parse_links(script_js):
    labels = re.findall(r'label:\s*"([^"]+)"', script_js)
    urls = re.findall(r'url:\s*"([^"]+)"', script_js)
    if not labels or len(labels) != len(urls):
        raise ValueError(
            f"LINKS parse failed: {len(labels)} labels vs {len(urls)} urls"
        )
    return list(zip(labels, urls))


def build_block(links):
    badges, bullets = [], []
    for label, url in links:
        if "github.com" in url:
            continue  # linklist only: the profile README is on GitHub itself
        if "note.com" in url:
            continue  # note/質問箱: badge icon does not render in the GitHub app; profile keeps icon links only (user decision 2026-11-24)
        line = render(label, url)
        if line is None:
            bullets.append(f"- {label}: [{url}]({url})")
        else:
            badges.append(line)
    parts = badges + bullets
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--readme", default=None,
                    help="README.md path (default: repo root README)")
    ap.add_argument("--source", default=None,
                    help="local script.js path (default: download)")
    args = ap.parse_args()

    if args.readme:
        readme_path = Path(args.readme)
    else:
        readme_path = Path(__file__).resolve().parent.parent / "README.md"

    if args.source:
        script_js = Path(args.source).read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(SCRIPT_JS_URL, timeout=30) as r:
            script_js = r.read().decode("utf-8")

    links = parse_links(script_js)
    block = build_block(links)

    text = readme_path.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(START) + r"\n(.*?)\n" + re.escape(END), re.DOTALL
    )
    m = pattern.search(text)
    if not m:
        print("ERROR: LINKS markers not found in README", file=sys.stderr)
        return 1
    existing = m.group(1)
    date_line = re.compile(r"^最終更新日：.*$", re.MULTILINE)
    existing_links = date_line.sub("", existing).rstrip("\n")
    if date_line.search(existing) and existing_links == block:
        print(f"README already up to date ({len(links)} links)")
        return 0
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)
    stamp = f"最終更新日：{now.year}年{now.month}月{now.day}日"
    block = block + "\n" + stamp
    new_text = pattern.sub(f"{START}\n{block}\n{END}", text, count=1)
    if new_text != text:
        readme_path.write_text(new_text, encoding="utf-8")
        print(f"README updated from {len(links)} links")
    else:
        print(f"README already up to date ({len(links)} links)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
