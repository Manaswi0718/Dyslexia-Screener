"""
Adaptive practice engine.

After screening, each child gets a learner profile:
  * mastery per skill, tracked with Bayesian Knowledge Tracing (BKT) and updated after every answer
  * a practice level (1-5) per game; inside a session the level follows a 3-up / 1-down staircase
  * the exact letter / sound pairs the child confuses, so practice shows those more often
  * a format profile (letter size, spacing, speech speed, time, round length) chosen from the screening,
    with a plain reason for each choice

The screening itself is never adapted: it has to stay identical for every child so scores can be compared.
"""
from __future__ import annotations

import random
from datetime import datetime, timezone

# skill -> practice game. Attention is screened but not "trained": a go/no-go game is not a treatment for ADHD.
SKILL_GAME = {"visual": "mirror", "phonology": "rhyme", "lettersound": "letters", "decoding": "realword",
              "memory": "memory", "naming": "naming", "spelling": "spell", "numsense": "dots", "numcompare": "compare"}
GAME_SKILL = {g: s for s, g in SKILL_GAME.items()}

# BKT parameters. guess = chance of a right answer without the skill (depends on how many options a game has).
P_LEARN, P_SLIP = 0.04, 0.20
P_GUESS = {"visual": 0.25, "phonology": 0.5, "lettersound": 0.25, "decoding": 0.5, "memory": 0.25,
           "naming": 0.2, "spelling": 0.25, "numsense": 0.25, "numcompare": 0.5}
MASTERED = 0.90
LEVELS = (1, 5)


def bkt_update(p: float, correct: bool, skill: str, level: int = 3) -> float:
    """One Bayesian Knowledge Tracing step: posterior given the answer, then the chance of learning.
    Easy items (low level) are easier to get right without the skill, so they count as weaker evidence."""
    g0 = P_GUESS.get(skill, 0.25)
    g = min(0.85, g0 + (1 - g0) * 0.45 * (5 - max(1, min(5, level))) / 4)
    if correct:
        post = p * (1 - P_SLIP) / (p * (1 - P_SLIP) + (1 - p) * g)
    else:
        post = p * P_SLIP / (p * P_SLIP + (1 - p) * (1 - g))
    return post + (1 - post) * P_LEARN


def level_cap(level: int) -> float:
    """Doing well on easy items can't prove mastery: the ceiling rises with the level played (L1 0.6 ... L5 1.0)."""
    return 0.5 + 0.1 * max(1, min(5, level))


def level_for(mastery: float) -> int:
    return max(LEVELS[0], min(LEVELS[1], 1 + int(mastery * 5)))


def format_profile(report: dict) -> dict:
    """Pick display and pacing settings from the screening results, and say why."""
    skills, conds = report.get("skills", {}), report.get("conditions", {})
    concern = lambda k: skills.get(k, {}).get("concern", 0)
    fmt = {"font_scale": 1.0, "letter_spacing": 0.0, "speech_rate": 1.0, "time_factor": 1.0,
           "round_size": 8, "calm": False, "reasons": []}

    if concern("visual") >= 40 or concern("spelling") >= 50:
        fmt.update(font_scale=1.25, letter_spacing=0.12)
        fmt["reasons"].append("Bigger letters with more space between them, because telling look-alike letters apart was hard.")
    if concern("phonology") >= 40 or concern("lettersound") >= 40:
        fmt["speech_rate"] = 0.8
        fmt["reasons"].append("Slower speech, because hearing sounds in words was hard.")
    slow = [k for k, v in skills.items() if v.get("mean_rt_ms") and v.get("expected_rt_ms")
            and v["mean_rt_ms"] > 1.5 * v["expected_rt_ms"]]
    if slow or concern("numsense") >= 50:
        fmt["time_factor"] = 1.5
        fmt["reasons"].append("50% more time on timed games, because answers took longer than expected.")
    if conds.get("attention", {}).get("band") in ("likely", "very_likely"):
        fmt.update(round_size=5, calm=True)
        fmt["reasons"].append("Shorter rounds and fewer animations, because the attention game showed signs of distraction.")
    if not fmt["reasons"]:
        fmt["reasons"].append("Standard settings: nothing in the screening called for changes.")
    return fmt


def init_learner(report: dict, mistakes: list[dict] | None = None) -> dict:
    """Build a learner profile from a screening report."""
    skills = report.get("skills", {})
    mastery, levels = {}, {}
    for skill, game in SKILL_GAME.items():
        if skill not in skills:
            continue
        # a skill that looked "as expected" starts near mastery; a weak one starts low
        p = max(0.1, min(0.85, 1 - skills[skill]["concern"] / 100))
        mastery[skill] = round(p, 3)
        levels[game] = level_for(p)
    confusions = {}
    for m in mistakes or []:
        if m.get("game") in ("mirror", "letters", "spell") and m.get("expected") and m.get("chosen"):
            key = f'{m["expected"]}|{m["chosen"]}'
            confusions[key] = confusions.get(key, 0) + 1
    return {"version": 1, "created": datetime.now(timezone.utc).isoformat(), "mastery": mastery, "levels": levels,
            "confusions": confusions, "format": format_profile(report), "sessions": [], "history": []}


def plan_session(learner: dict, seed: int | None = None) -> dict:
    """Pick today's 3 activities: the two weakest skills plus one stronger one, so the session isn't all struggle."""
    rng = random.Random(seed)
    m = learner.get("mastery", {})
    if not m:
        return {"activities": [], "message": "No skills to practise yet. Play the screening first."}
    ranked = sorted(m, key=lambda s: m[s])
    weak = [s for s in ranked if m[s] < MASTERED][:2] or ranked[:2]
    rest = [s for s in ranked if s not in weak]
    confidence = rng.choice(rest[len(rest) // 2:]) if rest else None
    chosen = weak + ([confidence] if confidence else [])
    order = [chosen[-1]] + chosen[:-1] if confidence else chosen       # warm up with the easier skill first
    acts = []
    for s in order:
        g = SKILL_GAME[s]
        acts.append({"game": g, "skill": s, "level": learner.get("levels", {}).get(g, level_for(m[s])),
                     "mastery": m[s], "focus": top_confusions(learner, g)})
    return {"activities": acts, "round_size": learner.get("format", {}).get("round_size", 8),
            "format": learner.get("format", {})}


def top_confusions(learner: dict, game: str, n: int = 3) -> list[list[str]]:
    if game not in ("mirror", "letters", "spell"):
        return []
    pairs = sorted(learner.get("confusions", {}).items(), key=lambda kv: -kv[1])[:n]
    return [k.split("|", 1) for k, _ in pairs]


def update_learner(learner: dict, results: list[dict]) -> dict:
    """Apply one practice session.
    results: [{game, start_level, end_level, seconds, answers: [{correct, level, expected?, chosen?, pair?}]}]
    pair = "expected|confused-with" when the item practised a known confusion."""
    m, levels, conf = learner.setdefault("mastery", {}), learner.setdefault("levels", {}), learner.setdefault("confusions", {})
    before = dict(m)
    summary = []
    for r in results:
        skill = GAME_SKILL.get(r.get("game"))
        if not skill:
            continue
        p = m.get(skill, 0.3)
        for a in r.get("answers", []):
            lvl = int(a.get("level") or r.get("start_level") or 3)
            p = bkt_update(p, bool(a.get("correct")), skill, lvl)
            if a.get("correct"):
                p = min(p, max(level_cap(lvl), m.get(skill, 0)))   # never lowered by the cap, only held back
            if not a.get("correct") and a.get("expected") and a.get("chosen") and a["expected"] != a["chosen"]:
                key = f'{a["expected"]}|{a["chosen"]}'
                conf[key] = conf.get(key, 0) + 1                 # a new or repeated confusion
            elif a.get("correct") and a.get("pair") in conf:     # got a known confusion right: fade it
                conf[a["pair"]] -= 1
                if conf[a["pair"]] <= 0:
                    del conf[a["pair"]]
        m[skill] = round(p, 3)
        if r.get("end_level"):
            levels[r["game"]] = max(LEVELS[0], min(LEVELS[1], int(r["end_level"])))
        answers = r.get("answers", [])
        summary.append({"game": r["game"], "skill": skill, "before": before.get(skill), "after": m[skill],
                        "correct": sum(1 for a in answers if a.get("correct")), "total": len(answers),
                        "start_level": r.get("start_level"), "end_level": r.get("end_level")})
    stamp = datetime.now(timezone.utc).isoformat()
    learner.setdefault("sessions", []).append({"date": stamp, "seconds": sum(int(r.get("seconds", 0)) for r in results),
                                               "summary": summary})
    learner.setdefault("history", []).append({"date": stamp, "mastery": dict(m)})
    learner["sessions"], learner["history"] = learner["sessions"][-60:], learner["history"][-60:]
    learner["mastered"] = [s for s, v in m.items() if v >= MASTERED]
    return learner
