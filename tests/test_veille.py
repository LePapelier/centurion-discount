import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import veille  # noqa: E402

FIX = Path(__file__).parent / "fixtures"


def test_parse_rss_with_namespaced_extras():
    items = veille.parse_feed((FIX / "dealabs.xml").read_bytes())
    assert items[0]["title"] == "SSD Samsung 990 Pro 2 To à 89€"
    assert items[0]["url"] == "https://www.dealabs.com/bons-plans/ssd-1"
    assert items[0]["summary"] == "Erreur de prix probable"
    assert items[0]["extra"]["merchant"] == {"name": "Amazon", "price": "89€"}


def test_parse_atom():
    (item,) = veille.parse_feed((FIX / "reddit.atom").read_bytes())
    assert item["url"] == "https://www.reddit.com/r/FreeGameFindings/comments/abc/"
    assert item["summary"] == "Free until Friday"
    assert veille.parse_date(item["published"]).year == 2026


def test_parse_gamerpower_skips_expired():
    (item,) = veille.parse_gamerpower((FIX / "gamerpower.json").read_bytes())
    assert item["extra"]["valeur"] == "$24.99"
    assert veille.parse_date(item["published"]) is not None


def test_parse_epic_keeps_only_current_free_offers():
    now = datetime.now(timezone.utc)
    iso = lambda d: d.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    offer = lambda pct, start, end: {"promotionalOffers": [{"promotionalOffers": [
        {"startDate": iso(start), "endDate": iso(end), "discountSetting": {"discountPercentage": pct}}]}]}
    data = {"data": {"Catalog": {"searchStore": {"elements": [
        {"title": "Libre", "productSlug": "libre", "promotions": offer(0, now - timedelta(days=1), now + timedelta(days=6))},
        {"title": "Soldé", "productSlug": "solde", "promotions": offer(50, now - timedelta(days=1), now + timedelta(days=6))},
        {"title": "Bientôt", "productSlug": "bientot", "promotions": offer(0, now + timedelta(days=6), now + timedelta(days=13))},
        {"title": "Sans promo", "promotions": None},
    ]}}}}
    (item,) = veille.parse_epic(json.dumps(data).encode())
    assert item["title"] == "Libre (gratuit sur Epic)"
    assert item["url"] == "https://store.epicgames.com/fr/p/libre"


def test_fetch_then_commit_dedups(tmp_path, monkeypatch):
    sources = tmp_path / "sources.toml"
    sources.write_text('[[source]]\nname="D"\ntype="rss"\nurl="x"\n'
                       '[[source]]\nname="KO"\ntype="rss"\nurl="boom"\n')
    monkeypatch.setattr(veille, "SOURCES_FILE", sources)
    monkeypatch.setattr(veille, "SEEN_FILE", tmp_path / "seen.json")
    monkeypatch.setattr(veille, "CANDIDATES_FILE", tmp_path / "candidates.json")
    monkeypatch.setattr(veille, "MAX_AGE_DAYS", 10_000)

    def fake_get(url):
        if url == "boom":
            raise OSError("bloqué")
        return (FIX / "dealabs.xml").read_bytes()
    monkeypatch.setattr(veille, "http_get", fake_get)

    assert veille.cmd_fetch(None) == 0
    out = json.loads((tmp_path / "candidates.json").read_text())
    assert len(out["candidats"]) == 2
    assert [r["ok"] for r in out["sources"]] == [True, False]

    assert veille.cmd_commit(None) == 0
    veille.cmd_fetch(None)
    assert json.loads((tmp_path / "candidates.json").read_text())["candidats"] == []


def test_detect_signals_spots_stackable_discounts():
    s = veille.detect_signals("Dentifrice Oral-B 100% remboursé via Shopmium",
                              "Cumulable avec 2€ de cashback iGraal et 1,50€ via 1,50€ sur la carte de fidélité")
    assert {"rembourse", "appli_remboursement", "cashback", "cagnotte"} <= set(s)
    assert veille.detect_signals("Lot de 3 Nutella (Via 3.65€ cagnottés)") == ["cagnotte"]
    assert "gratuit" in veille.detect_signals("Échantillon offert", "")
    assert veille.detect_signals("SSD 2 To à 89€", "Bon prix") == []
