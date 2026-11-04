"""Tests for the API and the game content. Run with:  pytest -q"""
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parent.parent
client = TestClient(app)
CONTENT = {k: v for k, v in json.loads((ROOT / "static" / "content.json").read_text(encoding="utf-8")).items() if not k.startswith("_")}


def test_home_page_loads():
    r = client.get("/")
    assert r.status_code == 200 and "Word Wizards" in r.text


def test_report_endpoint_returns_full_report():
    session = {"age": 8, "language": "te", "questionnaire": {"family_reading": "yes"}, "rounds": [
        {"game": "realword", "skill": "decoding", "clicks": 12, "hits": 5, "misses": 7, "mean_rt_ms": 3000},
        {"game": "rhyme", "skill": "phonology", "clicks": 10, "hits": 5, "misses": 5, "mean_rt_ms": 2600}]}
    r = client.post("/api/report", json=session)
    assert r.status_code == 200
    body = r.json()
    assert body["conditions"]["dyslexia"]["band"] in ("possible", "likely", "very_likely")
    assert 0 <= body["model"]["probability"] <= 1
    assert len(body["reasons"]) == 3                       # top-3 SHAP explanations
    assert body["next_steps_if_diagnosed"] and body["who_to_see"]


def test_bad_request_is_rejected():
    assert client.post("/api/report", json={"language": "en"}).status_code == 422


def test_every_language_has_every_text():
    keys = set(CONTENT["en"]["ui"])
    for lang, c in CONTENT.items():
        assert set(c["ui"]) == keys, f"{lang} is missing {keys - set(c['ui'])}"
        for block in ("mirror", "realword", "rhyme", "naming", "spell", "letters"):
            assert c.get(block), f"{lang} has no {block}"


def test_game_content_is_consistent():
    for lang, c in CONTENT.items():
        for m in c["mirror"]:
            assert m["target"] not in m["distractors"], (lang, m)
        assert not set(c["realword"]["real"]) & set(c["realword"]["alien"]), lang
        for s in c["spell"]:
            assert s["trap"] not in s["units"], (lang, s)
        assert any(r["rhymes"] for r in c["rhyme"]) and any(not r["rhymes"] for r in c["rhyme"]), lang


def test_spoken_words_have_audio():
    manifest = json.loads((ROOT / "static" / "audio" / "manifest.json").read_text(encoding="utf-8"))
    for lang, c in CONTENT.items():
        words = {w for r in c["rhyme"] for w in (r["a"], r["b"])} | {n["word"] for n in c["naming"]}
        missing = words - set(manifest.get(lang, {}))
        assert len(missing) <= 2, f"{lang}: no audio for {missing}"   # a couple may fall back to the browser voice
