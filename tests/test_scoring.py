"""Tests for the scoring engine (app/scoring.py). Run with:  pytest -q"""
from app.scoring import build_report, skill_profile, data_quality, band_for

READING = ["visual", "phonology", "lettersound", "decoding", "memory", "naming", "spelling"]
GAME = {"visual": "mirror", "phonology": "rhyme", "lettersound": "letters", "decoding": "realword",
        "memory": "memory", "naming": "naming", "spelling": "spell", "numsense": "dots", "numcompare": "compare"}


def rounds(acc, rt, skills=READING, n=10):
    hits = round(acc * n)
    return [{"game": GAME[s], "skill": s, "clicks": n, "hits": hits, "misses": n - hits, "mean_rt_ms": rt} for s in skills]


def report(rs, lang="en", age=9, q=None, prob=None):
    return build_report({"age": age, "language": lang, "rounds": rs, "questionnaire": q or {}}, prob, 0.23, [])


def test_strong_reader_is_unlikely():
    r = report(rounds(1.0, 900), prob=0.05)
    assert r["conditions"]["dyslexia"]["band"] == "unlikely"
    assert r["see_professional"] is False


def test_struggling_reader_is_flagged():
    r = report(rounds(0.3, 2500), prob=0.6)
    assert r["conditions"]["dyslexia"]["band"] in ("likely", "very_likely")
    assert r["see_professional"] is True


def test_random_answers_score_high_even_when_fast():
    # guessing on a two-choice game must never look "as expected"
    prof = skill_profile(rounds(0.5, 800, ["decoding"]), 9, "te")
    assert prof["decoding"]["concern"] >= 90


def test_slow_but_accurate_counts_more_in_regular_scripts():
    slow = rounds(1.0, 6000, ["decoding"])
    assert skill_profile(slow, 9, "te")["decoding"]["concern"] > skill_profile(slow, 9, "en")["decoding"]["concern"]
    assert skill_profile(slow, 9, "ta")["decoding"]["concern"] > skill_profile(slow, 9, "en")["decoding"]["concern"]


def test_older_children_are_held_to_higher_expectations():
    same = rounds(0.8, 1500, ["visual"])
    assert skill_profile(same, 12, "en")["visual"]["concern"] >= skill_profile(same, 6, "en")["visual"]["concern"]


def test_questionnaire_adds_at_most_15_points():
    base = report(rounds(0.9, 1200), prob=0.1)["conditions"]["dyslexia"]["index"]
    allyes = {k: "yes" for k in ["family_reading", "speech_delay", "teacher_reading", "letters_reverse"]}
    bumped = report(rounds(0.9, 1200), q=allyes, prob=0.1)["conditions"]["dyslexia"]["index"]
    assert 0 < bumped - base <= 15


def test_numbers_module_only_when_played():
    assert "dyscalculia" not in report(rounds(1.0, 900))["conditions"]
    r = report(rounds(1.0, 900) + rounds(0.3, 3000, ["numsense", "numcompare"]))
    assert r["conditions"]["dyscalculia"]["band"] in ("likely", "very_likely")


def test_attention_game_detects_impulsive_tapping():
    calm = {"game": "gonogo", "skill": "attention", "clicks": 24, "hits": 32, "misses": 0, "go_total": 24, "nogo_total": 8,
            "omissions": 0, "commissions": 0, "go_rts": [420, 450, 430, 440, 460, 410]}
    impulsive = dict(calm, omissions=6, commissions=7, go_rts=[200, 900, 300, 1200, 250, 800])
    a = report(rounds(1.0, 900) + [calm])["conditions"]["attention"]["index"]
    b = report(rounds(1.0, 900) + [impulsive])["conditions"]["attention"]["index"]
    assert b > a + 30


def test_random_tapping_is_reported():
    fast_random = [{"game": g, "skill": s, "clicks": 10, "hits": 4, "misses": 6, "mean_rt_ms": 300}
                   for g, s in [("rhyme", "phonology"), ("realword", "decoding")]]
    assert data_quality(fast_random)


def test_band_edges():
    assert band_for(0)[0] == "unlikely" and band_for(24.9)[0] == "unlikely"
    assert band_for(25)[0] == "possible" and band_for(50)[0] == "likely" and band_for(75)[0] == "very_likely"
    assert band_for(100)[0] == "very_likely"
