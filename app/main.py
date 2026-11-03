"""
Backend for the Dyslexia Screener.
Serves the games (static/) and turns game results into a risk band with an explanation.

Run:  uvicorn app.main:app --reload     then open http://127.0.0.1:8000
"""
from pathlib import Path
from typing import List, Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
bundle = joblib.load(ROOT / "models" / "portable_model.joblib")
MODEL, FEATURES, THRESHOLD = bundle["model"], bundle["features"], bundle["threshold"]

try:
    import shap
    EXPLAINER = shap.TreeExplainer(MODEL)
except Exception:
    EXPLAINER = None

# Plain-language names for the explanation shown to parents/teachers
FEATURE_TEXT = {
    "age": "age",
    "acc_mean": "overall accuracy",
    "acc_std": "how uneven accuracy was across games",
    "acc_min": "accuracy in the hardest round",
    "missrate_mean": "average share of wrong taps",
    "missrate_max": "wrong taps in the hardest round",
    "hits_mean": "correct answers per round",
    "misses_mean": "wrong answers per round",
    "clicks_mean": "taps per round",
    "hit_ratio": "share of taps that were correct",
}

app = FastAPI(title="Dyslexia Screener")


class Round(BaseModel):
    game: str            # e.g. "mirror", "realword"
    skill: str           # e.g. "visual", "decoding"
    clicks: int
    hits: int
    misses: int
    mean_rt_ms: Optional[float] = None   # average response time


class Session(BaseModel):
    age: int
    language: str
    rounds: List[Round]


def to_features(s: Session) -> pd.DataFrame:
    """Same summary features as ml/train.py -> portable_features()."""
    clicks = np.array([max(r.clicks, 1) for r in s.rounds], float)
    hits = np.array([r.hits for r in s.rounds], float)
    misses = np.array([r.misses for r in s.rounds], float)
    acc, miss = hits / clicks, misses / clicks
    row = {
        "age": s.age,
        "acc_mean": acc.mean(), "acc_std": acc.std(ddof=1) if len(acc) > 1 else 0.0,
        "acc_min": acc.min(),
        "missrate_mean": miss.mean(), "missrate_max": miss.max(),
        "hits_mean": hits.mean(), "misses_mean": misses.mean(),
        "clicks_mean": clicks.mean(),
        "hit_ratio": hits.sum() / clicks.sum(),
    }
    return pd.DataFrame([row])[FEATURES]


def band(p: float) -> dict:
    if p < THRESHOLD * 0.75:
        return {"level": "low", "label": "Few signs"}
    if p < THRESHOLD * 1.5:
        return {"level": "medium", "label": "Some signs - keep an eye on reading progress"}
    return {"level": "high", "label": "Several signs - consider a professional assessment"}


@app.post("/api/predict")
def predict(s: Session):
    X = to_features(s)
    p = float(MODEL.predict_proba(X)[0, 1])

    reasons = []
    if EXPLAINER is not None:
        sv = EXPLAINER.shap_values(X)
        if isinstance(sv, list): sv = sv[1]
        sv = np.asarray(sv)
        if sv.ndim == 3: sv = sv[:, :, 1]
        contrib = sorted(zip(FEATURES, sv[0]), key=lambda t: -abs(t[1]))[:3]
        reasons = [{"feature": f, "text": FEATURE_TEXT.get(f, f),
                    "direction": "raised" if v > 0 else "lowered", "impact": round(float(v), 3)}
                   for f, v in contrib]

    # per-skill summary (accuracy + speed) for the skill chart
    skills = {}
    for r in s.rounds:
        d = skills.setdefault(r.skill, {"hits": 0, "clicks": 0, "rts": []})
        d["hits"] += r.hits; d["clicks"] += max(r.clicks, 1)
        if r.mean_rt_ms: d["rts"].append(r.mean_rt_ms)
    skills = {k: {"accuracy": round(v["hits"] / v["clicks"], 2),
                  "mean_rt_ms": round(float(np.mean(v["rts"]))) if v["rts"] else None}
              for k, v in skills.items()}

    return {"probability": round(p, 3), "threshold": THRESHOLD, **band(p),
            "reasons": reasons, "skills": skills,
            "disclaimer": "This is a screening aid, not a diagnosis. Only a qualified professional can diagnose dyslexia."}


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")
