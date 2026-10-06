#!/usr/bin/env python3
"""Collecte des bons plans pour la routine de veille.

    python3 scripts/veille.py fetch   # récupère les sources -> data/candidates.json (nouveautés seulement)
    python3 scripts/veille.py commit  # marque les candidats comme vus dans state/seen.json

Le tri (ce qui est vraiment rare) est fait par Claude à partir de data/candidates.json
et de config/profil.md ; ce script ne fait que collecter, normaliser et dédoublonner.
Uniquement la bibliothèque standard, pour tourner partout sans installation.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import tomllib
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES_FILE = ROOT / "config" / "sources.toml"
SEEN_FILE = ROOT / "state" / "seen.json"
CANDIDATES_FILE = ROOT / "data" / "candidates.json"

# UA de navigateur : Reddit renvoie 429 aux agents « robots ».
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
TIMEOUT = 20
MAX_AGE_DAYS = 7  # ignore les éléments publiés il y a plus longtemps
SEEN_RETENTION_DAYS = 90
SUMMARY_MAX = 600

# Indices qu'une offre devient gratuite (ou presque) une fois les remises cumulées :
# ODR, cashback, cagnotte fidélité, coupons, applis de remboursement… Repérés dans le
# titre et le résumé pour que le tri les examine en priorité et calcule le prix net.
SIGNAUX = {
    "rembourse": r"100 ?% rembours|rembours[ée]|\bodr\b|offre de remboursement",
    "cashback": r"cash ?back|igraal|poulpeo|joko|rakuten|widilo|ebuyclub",
    "cagnotte": r"cagnott|carte (de )?fid[ée]lit[ée]|ticket (e\.)?leclerc|\bvia [0-9]+[,.]?[0-9]* ?€ (sur|de|en)",
    "appli_remboursement": r"shopmium|quoty|coupon ?network|envie ?de ?plus|bons? de r[ée]duction|\bcoupons?\b|\bbri\b",
    "gratuit": r"gratuit|offert|\bfree\b|\b0([,.]00?)? ?€|€ ?0([,.]00?)?\b",
    "erreur_prix": r"erreur de prix|bug de prix|price error|mistake fare",
}


def item_id(url: str, title: str) -> str:
    key = (url or title).strip().lower()
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def clean_text(raw: str | None) -> str:
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    return text[:SUMMARY_MAX]


def parse_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    raw = raw.strip()
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def http_get(url: str, retries: int = 2) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == retries:
                raise
            wait = e.headers.get("Retry-After", "")
            time.sleep(min(int(wait) if wait.isdigit() else 10 * (attempt + 1), 60))


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(el: ET.Element, *names: str) -> str | None:
    for child in el:
        if local(child.tag) in names and (child.text or "").strip():
            return child.text
    return None


def detect_signals(*texts: str) -> list[str]:
    blob = " ".join(t for t in texts if t).lower()
    return [name for name, pattern in SIGNAUX.items() if re.search(pattern, blob)]


def parse_feed(data: bytes) -> list[dict]:
    """Parse un flux RSS 2.0 ou Atom en éléments normalisés."""
    root = ET.fromstring(data)
    entries = [el for el in root.iter() if local(el.tag) in ("item", "entry")]
    items = []
    for el in entries:
        title = clean_text(child_text(el, "title"))
        url = child_text(el, "link")
        if not url:  # Atom : <link href="..."/>
            for child in el:
                if local(child.tag) == "link" and child.get("rel", "alternate") == "alternate":
                    url = child.get("href")
                    break
        extra = {}
        for child in el:
            # Champs spécifiques (ex. <pepper:merchant name=".." price=".."/> sur Dealabs)
            if "}" in child.tag and child.attrib and local(child.tag) not in ("link", "content", "thumbnail"):
                extra[local(child.tag)] = dict(child.attrib)
        items.append({
            "title": title,
            "url": (url or "").strip(),
            "published": child_text(el, "pubDate", "published", "updated", "date"),
            "summary": clean_text(child_text(el, "description", "summary", "content")),
            "extra": extra,
        })
    return items


def parse_gamerpower(data: bytes) -> list[dict]:
    items = []
    for g in json.loads(data):
        if g.get("status", "Active") != "Active":
            continue
        items.append({
            "title": g.get("title", ""),
            "url": g.get("open_giveaway_url") or g.get("gamerpower_url", ""),
            "published": g.get("published_date"),
            "summary": clean_text(g.get("description")),
            "extra": {
                "valeur": g.get("worth"),
                "type": g.get("type"),
                "plateformes": g.get("platforms"),
                "fin": g.get("end_date"),
            },
        })
    return items


def parse_epic(data: bytes) -> list[dict]:
    games = json.loads(data)["data"]["Catalog"]["searchStore"]["elements"]
    now = datetime.now(timezone.utc)
    items = []
    for g in games:
        offers = ((g.get("promotions") or {}).get("promotionalOffers") or [])
        for block in offers:
            for offer in block.get("promotionalOffers", []):
                start, end = parse_date(offer.get("startDate")), parse_date(offer.get("endDate"))
                discount = (offer.get("discountSetting") or {}).get("discountPercentage")
                if discount != 0 or not start or not end or not (start <= now <= end):
                    continue
                slug = g.get("productSlug") or (g.get("catalogNs") or {}).get("mappings", [{}])[0].get("pageSlug")
                items.append({
                    "title": f"{g.get('title')} (gratuit sur Epic)",
                    "url": f"https://store.epicgames.com/fr/p/{slug}" if slug else "https://store.epicgames.com/fr/free-games",
                    "published": offer.get("startDate"),
                    "summary": clean_text(g.get("description")),
                    "extra": {
                        "prix_normal": (g.get("price") or {}).get("totalPrice", {}).get("fmtPrice", {}).get("originalPrice"),
                        "fin": offer.get("endDate"),
                    },
                })
    return items


PARSERS = {"rss": parse_feed, "gamerpower": parse_gamerpower, "epic": parse_epic}


def load_sources() -> list[dict]:
    with SOURCES_FILE.open("rb") as f:
        return [s for s in tomllib.load(f).get("source", []) if s.get("enabled", True)]


def load_seen() -> dict[str, str]:
    if SEEN_FILE.exists():
        return json.loads(SEEN_FILE.read_text())
    return {}


def cmd_fetch(_args) -> int:
    seen = load_seen()
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    candidates, report = [], []
    for src in load_sources():
        try:
            raw_items = PARSERS[src["type"]](http_get(src["url"]))
        except Exception as e:  # une source en panne ne doit pas bloquer les autres
            report.append({"source": src["name"], "ok": False, "erreur": f"{type(e).__name__}: {e}"[:200]})
            continue
        new = 0
        for it in raw_items:
            pub = parse_date(it["published"])
            if pub and pub < cutoff:
                continue
            iid = item_id(it["url"], it["title"])
            if iid in seen or any(c["id"] == iid for c in candidates):
                continue
            signaux = detect_signals(it["title"], it["summary"])
            candidates.append({"id": iid, "source": src["name"], "categorie": src.get("category", ""),
                               "signaux": signaux, **it})
            new += 1
        report.append({"source": src["name"], "ok": True, "recus": len(raw_items), "nouveaux": new})

    CANDIDATES_FILE.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATES_FILE.write_text(json.dumps({
        "genere_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": report,
        "candidats": candidates,
    }, ensure_ascii=False, indent=1))

    for r in report:
        status = f"{r['nouveaux']} nouveaux / {r['recus']}" if r["ok"] else f"ÉCHEC {r['erreur']}"
        print(f"- {r['source']}: {status}")
    cumuls = sum(1 for c in candidates if len(set(c["signaux"]) - {"gratuit"}) >= 2)
    print(f"{len(candidates)} candidats écrits dans {CANDIDATES_FILE.name} ({cumuls} avec plusieurs remises cumulables)")
    return 0 if any(r["ok"] for r in report) else 1


def cmd_commit(_args) -> int:
    if not CANDIDATES_FILE.exists():
        print("Rien à valider : lance d'abord `fetch`.", file=sys.stderr)
        return 1
    seen = load_seen()
    today = datetime.now(timezone.utc).date()
    for c in json.loads(CANDIDATES_FILE.read_text())["candidats"]:
        seen.setdefault(c["id"], today.isoformat())
    limit = (today - timedelta(days=SEEN_RETENTION_DAYS)).isoformat()
    seen = {k: v for k, v in seen.items() if v >= limit}
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(seen, indent=0, sort_keys=True) + "\n")
    print(f"{len(seen)} éléments mémorisés dans {SEEN_FILE.name}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch").set_defaults(func=cmd_fetch)
    sub.add_parser("commit").set_defaults(func=cmd_commit)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
