"""Tests for the adaptive practice engine (app/adaptive.py). Run with:  pytest -q"""
from fastapi.testclient import TestClient

from app.adaptive import bkt_update, init_learner, plan_session, update_learner, format_profile
from app.main import app

client = TestClient(app)
WEAK_VISUAL = {"skills": {"visual": {"concern": 75, "mean_rt_ms": 3000, "expected_rt_ms": 1000}, "phonology": {"concern": 50},
                          "decoding": {"concern": 10}, "spelling": {"concern": 40}, "numsense": {"concern": 5}},
               "conditions": {"attention": {"band": "likely"}}}


def test_bkt_goes_up_when_right_and_down_when_wrong():
    assert bkt_update(0.5, True, "visual") > 0.5 > bkt_update(0.5, False, "visual")


def test_easy_items_count_as_weaker_evidence():
    assert bkt_update(0.3, True, "visual", level=5) > bkt_update(0.3, True, "visual", level=1)


def test_learner_starts_from_the_screening():
    L = init_learner(WEAK_VISUAL, [{"game": "mirror", "expected": "ब", "chosen": "व"}])
    assert L["mastery"]["visual"] < L["mastery"]["decoding"]
    assert L["levels"]["mirror"] < L["levels"]["realword"]
    assert L["confusions"] == {"ब|व": 1}


def test_format_follows_the_screening_and_explains_itself():
    f = format_profile(WEAK_VISUAL)
    assert f["font_scale"] > 1 and f["speech_rate"] < 1 and f["time_factor"] > 1 and f["calm"] and f["round_size"] == 5
    assert len(f["reasons"]) == 4
    plain = format_profile({"skills": {"visual": {"concern": 0}}, "conditions": {}})
    assert plain["font_scale"] == 1 and plain["speech_rate"] == 1


def test_plan_targets_weak_skills_and_their_confusions():
    L = init_learner(WEAK_VISUAL, [{"game": "mirror", "expected": "ब", "chosen": "व"}])
    acts = plan_session(L, seed=0)["activities"]
    games = [a["game"] for a in acts]
    assert "mirror" in games and len(acts) == 3
    assert next(a for a in acts if a["game"] == "mirror")["focus"] == [["ब", "व"]]


def test_mastery_needs_success_at_higher_levels():
    L = {"mastery": {"visual": 0.3}, "levels": {"mirror": 1}, "confusions": {}}
    L = update_learner(L, [{"game": "mirror", "start_level": 1, "end_level": 1, "answers": [{"correct": True, "level": 1}] * 10}])
    assert L["mastery"]["visual"] <= 0.6                         # easy items alone can't prove mastery
    L = update_learner(L, [{"game": "mirror", "start_level": 5, "end_level": 5, "answers": [{"correct": True, "level": 5}] * 10}])
    assert L["mastery"]["visual"] >= 0.9 and "visual" in L["mastered"]


def test_confusions_fade_when_practised_correctly():
    L = {"mastery": {"visual": 0.5}, "levels": {}, "confusions": {"ब|व": 2}}
    L = update_learner(L, [{"game": "mirror", "answers": [{"correct": True, "level": 3, "pair": "ब|व"}] * 2}])
    assert "ब|व" not in L["confusions"]
    L = update_learner(L, [{"game": "mirror", "answers": [{"correct": False, "level": 3, "expected": "घ", "chosen": "ध"}]}])
    assert L["confusions"] == {"घ|ध": 1}


def test_progress_history_is_kept():
    L = init_learner(WEAK_VISUAL)
    for _ in range(3):
        L = update_learner(L, [{"game": "mirror", "seconds": 30, "answers": [{"correct": True, "level": 2}]}])
    assert len(L["sessions"]) == 3 and len(L["history"]) == 3


def test_practice_api_round_trip():
    L = client.post("/api/learner/init", json={"report": WEAK_VISUAL, "mistakes": []}).json()
    plan = client.post("/api/practice/plan", json={"learner": L}).json()
    assert plan["activities"]
    act = plan["activities"][0]
    res = [{"game": act["game"], "start_level": act["level"], "end_level": min(5, act["level"] + 1), "seconds": 40,
            "answers": [{"correct": True, "level": act["level"]}] * 6}]
    L2 = client.post("/api/practice/update", json={"learner": L, "results": res}).json()
    assert L2["mastery"][act["skill"]] > L["mastery"][act["skill"]]
    assert L2["levels"][act["game"]] == res[0]["end_level"]
