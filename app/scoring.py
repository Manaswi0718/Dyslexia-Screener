"""
Transparent scoring engine.

Turns game rounds + a short parent questionnaire into:
  * per-skill "concern" scores (0 = as expected for age, 100 = far below), using accuracy AND speed
  * a likelihood index (0-100) and band for each screened condition:
        Dyslexia (reading module)  ·  Dyscalculia (numbers module)  ·  Attention signs (attention module)
  * clear "what this means" + "when to see a professional" guidance
  * a data-quality check (tired / random tapping / did not understand)

IMPORTANT: the age expectations below are PROVISIONAL, set from typical task difficulty.
They must be replaced with norms collected from a pilot with real children before any real use.
"""
from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------- skills
# floor  = chance level for the task (random tapping)
# acc6 / acc10 = expected accuracy for a typical 6-year-old / 10-year-old (linear in between)
# rt6 / rt10   = expected response time (ms) per answer at those ages
SKILLS = {
    # reading module
    "visual":      dict(module="reading", label="Spotting look-alike letters", floor=0.30, acc6=0.75, acc10=0.92, rt6=1500, rt10=900, w=0.8),
    "phonology":   dict(module="reading", label="Hearing sounds in words (rhyme)", floor=0.50, acc6=0.75, acc10=0.92, rt6=2500, rt10=1600, w=1.3),
    "lettersound": dict(module="reading", label="Matching sounds to letters", floor=0.25, acc6=0.75, acc10=0.95, rt6=2500, rt10=1500, w=1.0),
    "decoding":    dict(module="reading", label="Reading new words", floor=0.50, acc6=0.70, acc10=0.90, rt6=3500, rt10=2000, w=1.5),
    "memory":      dict(module="reading", label="Sound & sequence memory", floor=0.25, acc6=0.65, acc10=0.85, rt6=1200, rt10=800, w=0.7),
    "naming":      dict(module="reading", label="Word-to-picture speed", floor=0.17, acc6=0.85, acc10=0.97, rt6=2200, rt10=1300, w=1.0),
    "spelling":    dict(module="reading", label="Building words from letters", floor=0.30, acc6=0.65, acc10=0.90, rt6=3000, rt10=1800, w=1.2),
    # numbers module
    "numsense":    dict(module="numbers", label="Seeing how many (dots)", floor=0.25, acc6=0.75, acc10=0.92, rt6=2500, rt10=1500, w=1.2),
    "numcompare":  dict(module="numbers", label="Comparing numbers", floor=0.50, acc6=0.80, acc10=0.95, rt6=1800, rt10=1000, w=1.0),
}

# In regular scripts (Hindi, Telugu) dyslexia shows more as SLOW reading than as wrong answers.
SPEED_WEIGHT = {"en": 0.25, "hi": 0.40, "te": 0.40}

BANDS = [  # (upper bound, key, label)
    (25, "unlikely", "Unlikely"),
    (50, "possible", "Possible"),
    (75, "likely", "Likely"),
    (101, "very_likely", "Very likely"),
]

GUIDANCE = {
    "dyslexia": {
        "unlikely":    ("The child's reading-related skills look as expected for their age.",
                        "No assessment needed now. Play again in 6-12 months, or sooner if the teacher raises reading concerns."),
        "possible":    ("Some reading-related skills are weaker than expected for this age. This can be normal variation, tiredness, or an early sign of a reading difficulty.",
                        "Practise the activities below for 6-8 weeks, then play again. If the result stays the same or the teacher is worried, book an assessment."),
        "likely":      ("Several reading-related skills are clearly below what is expected for this age - a pattern often seen in children with dyslexia.",
                        "Book an assessment with a clinical psychologist or developmental paediatrician within the next 1-2 months. Take this report with you."),
        "very_likely": ("Most reading-related skills are well below what is expected for this age. This pattern is strongly associated with dyslexia.",
                        "Book a full assessment as soon as possible. Support helps most when it starts early, and a formal diagnosis makes the child eligible for school and exam support."),
    },
    "dyscalculia": {
        "unlikely":    ("Number skills look as expected for this age.", "No action needed now."),
        "possible":    ("Some number skills are weaker than expected for this age.",
                        "Practise counting and number games at home for 6-8 weeks, then play again. Mention it to the maths teacher."),
        "likely":      ("Basic number skills are clearly below what is expected for this age - a pattern often seen in dyscalculia.",
                        "Ask for an assessment of maths learning with a clinical psychologist within 1-2 months."),
        "very_likely": ("Basic number sense is well below what is expected for this age. This pattern is strongly associated with dyscalculia.",
                        "Book an assessment soon. Dyscalculia is a recognised Specific Learning Disability with school support available."),
    },
    "attention": {
        "unlikely":    ("Attention and impulse control during the game looked typical.", "No action needed."),
        "possible":    ("The child missed some targets or tapped impulsively more than expected. Tiredness, hunger or a noisy room can cause this.",
                        "Play again on another day in a quiet room. If teachers or parents also notice attention difficulties, mention it to your paediatrician."),
        "likely":      ("The child showed clear signs of inattention or impulsivity in this game.",
                        "This game cannot diagnose ADHD. If you also see attention difficulties at home and school, talk to a paediatrician or child psychiatrist."),
        "very_likely": ("The child showed strong signs of inattention or impulsivity in this game.",
                        "Talk to a paediatrician or child psychiatrist. ADHD is diagnosed using reports from home and school, not a single test."),
    },
}

TITLES = {"dyslexia": "Dyslexia (reading)", "dyscalculia": "Dyscalculia (numbers)", "attention": "Attention signs"}

# Questionnaire: research-backed risk factors. Each "yes" adds points to the related index.
QUESTIONS = {
    "family_reading": ("A parent or sibling had trouble learning to read or spell", "dyslexia", 8),
    "speech_delay":   ("The child started speaking late or had speech therapy", "dyslexia", 5),
    "teacher_reading":("The teacher has said the child struggles with reading or spelling", "dyslexia", 8),
    "letters_reverse":("The child often mixes up letters (b/d) or skips words when reading", "dyslexia", 5),
    "teacher_math":   ("The teacher has said the child struggles with numbers or maths", "dyscalculia", 10),
    "attention_home": ("The child finds it hard to sit still or stay focused on tasks", "attention", 10),
}

ACTIVITIES = {
    "visual":      ["Letter hunt: circle every 'b' (or ब / బ) on a newspaper page, then every 'd'.",
                    "Trace look-alike letters in sand or salt while saying their sound aloud.",
                    "Use a different colour for each confusable letter on flashcards."],
    "phonology":   ["Rhyme games in the car or at meals: 'What rhymes with cat?'",
                    "Clap the syllables of family names and favourite foods.",
                    "Sing rhyming songs and pause so the child fills in the rhyming word."],
    "lettersound": ["Daily 5-minute letter-sound flashcards - say the sound, not the letter name.",
                    "Match letter magnets to objects starting with that sound.",
                    "Write letters in the air with big arm movements while saying the sound."],
    "decoding":    ["Read together for 15 minutes every day, taking turns line by line.",
                    "Play 'real or silly word' by changing one letter: cat -> cap -> zap.",
                    "Use simple, decodable books at the child's level - not above it."],
    "memory":      ["Repeat-after-me games with growing lists: 'I went to the market and bought...'",
                    "Give two-step instructions, then three-step, and praise success.",
                    "Play memory card-matching games."],
    "naming":      ["Rapid naming: lay out 5 pictures and name them quickly, 3 times a day.",
                    "'I spy' games to build quick word recall.",
                    "Name colours, animals and objects against a gentle timer - make it fun, not stressful."],
    "spelling":    ["Build words with letter tiles before writing them.",
                    "Say each sound while writing the letter (multi-sensory spelling).",
                    "Practise 3-5 words a week, not long lists."],
    "numsense":    ["Dot cards: flash a card with 1-6 dots and say how many without counting.",
                    "Count real objects (spoons, steps, coins) every day.",
                    "Board games with dice, like Snakes & Ladders."],
    "numcompare":  ["'Which is more?' with handfuls of beans or coins.",
                    "Number line on the floor: jump to the bigger number.",
                    "Card game 'War': each flips a card, the bigger number wins."],
}

NEXT_STEPS_IF_DIAGNOSED = [
    ("Get structured support", "Work with a special educator using structured, phonics-based (multi-sensory) teaching. Short, frequent sessions work best."),
    ("Ask the school for accommodations", "Extra time, oral answers, less copying from the board, printed notes, and not cutting marks for spelling in subjects like science."),
    ("Get the SLD certificate", "Specific Learning Disability is recognised under India's RPwD Act, 2016. With the certificate (and UDID card) the child can get board-exam concessions such as extra time, a scribe or reader, and exemption from a third language."),
    ("Use assistive technology", "Audiobooks, text-to-speech, and dyslexia-friendly settings on phones and tablets."),
    ("Protect confidence", "Dyslexia is not about intelligence. Talk about the child's strengths, and explain that their brain learns to read in a different way."),
    ("Track progress", "Play this screener again every 6-8 weeks to see if skills are improving."),
]

WHO_TO_SEE = [
    "Clinical psychologist (RCI-registered) - does the formal learning-disability assessment",
    "Developmental paediatrician or child psychiatrist - rules out other causes; diagnoses ADHD",
    "Special educator - provides the actual remedial teaching",
    "Free options: child guidance / psychiatry departments of government hospitals, and District Early Intervention Centres (DEIC)",
    "First, rule out vision and hearing problems with a basic eye and hearing test",
]


def _expected(spec: dict, age: float):
    t = float(np.clip((age - 6) / 4, 0, 1.25))           # extrapolate a little past 10
    acc = min(spec["acc6"] + t * (spec["acc10"] - spec["acc6"]), 0.98)
    rt = max(spec["rt6"] + t * (spec["rt10"] - spec["rt6"]), 0.6 * spec["rt10"])
    return acc, rt


def band_for(index: float):
    for upper, key, label in BANDS:
        if index < upper:
            return key, label
    return BANDS[-1][1], BANDS[-1][2]


def skill_profile(rounds: list[dict], age: float, lang: str) -> dict:
    sw = SPEED_WEIGHT.get(lang, 0.3)
    agg: dict[str, dict] = {}
    for r in rounds:
        if r["skill"] not in SKILLS:
            continue
        a = agg.setdefault(r["skill"], {"hits": 0, "clicks": 0, "rts": []})
        a["hits"] += r["hits"]; a["clicks"] += max(r["clicks"], 0)
        if r.get("mean_rt_ms"):
            a["rts"].append(r["mean_rt_ms"])
    out = {}
    for k, a in agg.items():
        spec = SKILLS[k]
        acc = a["hits"] / a["clicks"] if a["clicks"] else 0.0
        rt = float(np.median(a["rts"])) if a["rts"] else None
        exp_acc, exp_rt = _expected(spec, age)
        acc_gap = float(np.clip((exp_acc - acc) / (exp_acc - spec["floor"]), 0, 1))
        speed_gap = float(np.clip((rt - exp_rt) / (1.5 * exp_rt), 0, 1)) if rt else 0.0
        # wrong answers count fully on their own; slowness adds on top (more strongly in regular scripts)
        concern = 100 * min(1.0, acc_gap + (1 - acc_gap) * sw * 1.6 * speed_gap)
        out[k] = {"label": spec["label"], "module": spec["module"], "accuracy": round(acc, 2),
                  "expected_accuracy": round(exp_acc, 2), "mean_rt_ms": round(rt) if rt else None,
                  "expected_rt_ms": round(exp_rt), "concern": round(concern)}
    return out


def attention_profile(rounds: list[dict], age: float):
    g = next((r for r in rounds if r["game"] == "gonogo"), None)
    if not g or not g.get("go_total"):
        return None
    omission = g["omissions"] / g["go_total"]
    commission = g["commissions"] / max(g["nogo_total"], 1)
    rts = g.get("go_rts") or []
    cv = float(np.std(rts) / np.mean(rts)) if len(rts) > 3 else 0.0
    t = float(np.clip((age - 6) / 4, 0, 1.25))
    exp_om, exp_com, exp_cv = 0.15 - 0.08 * t, 0.35 - 0.15 * t, 0.30 - 0.08 * t   # PROVISIONAL
    s_om = np.clip((omission - exp_om) / 0.4, 0, 1)
    s_com = np.clip((commission - exp_com) / 0.5, 0, 1)
    s_cv = np.clip((cv - exp_cv) / 0.3, 0, 1)
    index = 100 * (0.4 * s_om + 0.4 * s_com + 0.2 * s_cv)
    return {"index": float(index), "omission_rate": round(omission, 2), "commission_rate": round(commission, 2),
            "rt_variability": round(cv, 2)}


def data_quality(rounds: list[dict]) -> list[str]:
    issues = []
    # quick taps are normal in Mirror Hunt / Echo Memory / Catch the Star, so only check the answer-choice games
    choice_games = {"rhyme", "letters", "realword", "naming", "dots", "compare"}
    fast_random = sum(1 for r in rounds if r["game"] in choice_games and r.get("mean_rt_ms") and r["mean_rt_ms"] < 600
                      and r["clicks"] and r["hits"] / r["clicks"] < 0.6)
    if fast_random >= 2:
        issues.append("Very fast answers with many mistakes in several games - the child may have been tapping randomly.")
    no_taps = sum(1 for r in rounds if r["game"] == "mirror" and r["clicks"] == 0)
    if no_taps:
        issues.append("The child did not tap at all in some rounds - they may not have understood the task.")
    return issues


def build_report(session: dict, model_prob: float | None, model_threshold: float | None, reasons: list) -> dict:
    age, lang = session["age"], session["language"]
    rounds = session["rounds"]
    q = session.get("questionnaire", {}) or {}
    skills = skill_profile(rounds, age, lang)

    q_bump = {"dyslexia": 0, "dyscalculia": 0, "attention": 0}
    q_flags = []
    for key, (text, target, pts) in QUESTIONS.items():
        if q.get(key) == "yes":
            q_bump[target] += pts; q_flags.append(text)
    for k in q_bump:
        q_bump[k] = min(q_bump[k], 15)

    conditions = {}
    # ---- dyslexia: age-adjusted reading skills (70%) + ML model trained on Rello et al. 2020 (30%) + questionnaire
    read = {k: v for k, v in skills.items() if v["module"] == "reading"}
    if read:
        comp = sum(SKILLS[k]["w"] * v["concern"] for k, v in read.items()) / sum(SKILLS[k]["w"] for k in read)
        ml = 100 * float(np.clip(model_prob / (2 * model_threshold), 0, 1)) if model_prob is not None else comp
        idx = float(np.clip(0.7 * comp + 0.3 * ml + q_bump["dyslexia"], 0, 100))
        conditions["dyslexia"] = {"index": idx, "parts": {"skills": round(comp), "ml_model": round(ml), "questionnaire": q_bump["dyslexia"]}}
    # ---- dyscalculia
    num = {k: v for k, v in skills.items() if v["module"] == "numbers"}
    if num:
        comp = sum(SKILLS[k]["w"] * v["concern"] for k, v in num.items()) / sum(SKILLS[k]["w"] for k in num)
        idx = float(np.clip(comp + q_bump["dyscalculia"], 0, 100))
        conditions["dyscalculia"] = {"index": idx, "parts": {"skills": round(comp), "questionnaire": q_bump["dyscalculia"]}}
    # ---- attention
    att = attention_profile(rounds, age)
    if att:
        idx = float(np.clip(att["index"] + q_bump["attention"], 0, 100))
        conditions["attention"] = {"index": idx, "details": att, "parts": {"game": round(att["index"]), "questionnaire": q_bump["attention"]}}

    for k, c in conditions.items():
        key, label = band_for(c["index"])
        meaning, action = GUIDANCE[k][key]
        c.update({"index": round(c["index"]), "band": key, "label": label, "title": TITLES[k],
                  "meaning": meaning, "action": action})

    notes = []
    if "attention" in conditions and conditions["attention"]["band"] in ("likely", "very_likely") and "dyslexia" in conditions:
        notes.append("Attention difficulties during the games can lower scores in other games too. Keep this in mind when reading the other results.")
    if lang in ("hi", "te"):
        notes.append("Hindi and Telugu are written almost exactly as they sound, so this screener gives extra weight to speed: slow-but-correct reading can be a sign of dyslexia in these languages.")

    weak = sorted([(k, v) for k, v in skills.items() if v["concern"] >= 25], key=lambda kv: -kv[1]["concern"])[:3]
    plan = [{"skill": k, "label": v["label"], "activities": ACTIVITIES[k]} for k, v in weak]

    any_concern = any(c["band"] in ("likely", "very_likely") for c in conditions.values())
    return {
        "child": {"name": session.get("name") or "Child", "age": age, "grade": session.get("grade"), "language": lang},
        "conditions": conditions,
        "skills": skills,
        "reasons": reasons,
        "model": {"probability": None if model_prob is None else round(model_prob, 3), "threshold": model_threshold},
        "questionnaire_flags": q_flags,
        "data_quality": data_quality(rounds),
        "notes": notes,
        "action_plan": plan,
        "next_steps_if_diagnosed": [{"title": t, "text": x} for t, x in NEXT_STEPS_IF_DIAGNOSED],
        "who_to_see": WHO_TO_SEE,
        "see_professional": any_concern,
        "disclaimer": ("This is a screening tool, not a diagnosis. Only a qualified professional can diagnose dyslexia, "
                       "dyscalculia or ADHD. Age expectations are provisional and need validation with local norms."),
    }
