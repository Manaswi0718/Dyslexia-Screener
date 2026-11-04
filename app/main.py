"""
Backend for the Word Wizards screener.
Serves the games (static/) and turns game results into a full screening report.

Run:  uvicorn app.main:app --reload     then open http://127.0.0.1:8000
"""
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

from app.scoring import build_report

ROOT = Path(__file__).resolve().parent.parent
bundle = joblib.load(ROOT / "models" / "portable_model.joblib")
MODEL, FEATURES, THRESHOLD = bundle["model"], bundle["features"], bundle["threshold"]

# SHAP explanations come straight from XGBoost (pred_contribs) - no heavy 'shap' library needed on the server
try:
    import xgboost as xgb
    BOOSTER = MODEL.get_booster()
except Exception:
    BOOSTER = None

FEATURE_TEXT = {
    "age": "age", "acc_mean": "overall accuracy", "acc_std": "how uneven accuracy was across games",
    "acc_min": "accuracy in the hardest round", "missrate_mean": "average share of wrong answers",
    "missrate_max": "wrong answers in the hardest round", "hits_mean": "correct answers per round",
    "misses_mean": "wrong answers per round", "clicks_mean": "answers per round",
    "hit_ratio": "share of answers that were correct",
}
# rounds from these games feed the ML model (the Rello et al. data has linguistic + memory exercises)
MODEL_GAMES = {"mirror", "rhyme", "letters", "realword", "memory", "naming", "spell"}

app = FastAPI(title="Word Wizards screener")


class Round(BaseModel):
    model_config = ConfigDict(extra="allow")     # games may send extra fields (mistakes, go_rts, span ...)
    game: str
    skill: str
    clicks: int = 0
    hits: int = 0
    misses: int = 0
    mean_rt_ms: Optional[float] = None


class Session(BaseModel):
    name: Optional[str] = None
    age: int
    grade: Optional[str] = None
    language: str
    questionnaire: Dict[str, str] = {}
    rounds: List[Round]


def model_features(rounds) -> Optional[pd.DataFrame]:
    rs = [r for r in rounds if r.game in MODEL_GAMES]
    if not rs:
        return None
    clicks = np.array([max(r.clicks, 1) for r in rs], float)
    hits = np.array([r.hits for r in rs], float)
    misses = np.array([r.misses for r in rs], float)
    acc, miss = hits / clicks, misses / clicks
    return pd.DataFrame([{
        "acc_mean": acc.mean(), "acc_std": acc.std(ddof=1) if len(acc) > 1 else 0.0, "acc_min": acc.min(),
        "missrate_mean": miss.mean(), "missrate_max": miss.max(), "hits_mean": hits.mean(),
        "misses_mean": misses.mean(), "clicks_mean": clicks.mean(), "hit_ratio": hits.sum() / clicks.sum(),
    }])


@app.post("/api/report")
def report(s: Session):
    X = model_features(s.rounds)
    prob, reasons = None, []
    if X is not None:
        X.insert(0, "age", s.age)
        X = X[FEATURES]
        prob = float(MODEL.predict_proba(X)[0, 1])
        if BOOSTER is not None:
            contrib = BOOSTER.predict(xgb.DMatrix(X), pred_contribs=True)[0][:-1]   # last column = bias
            top = sorted(zip(FEATURES, contrib), key=lambda t: -abs(t[1]))[:3]
            reasons = [{"text": FEATURE_TEXT.get(f, f), "direction": "raised" if v > 0 else "lowered"} for f, v in top]
    session = s.model_dump()
    return build_report(session, prob, THRESHOLD, reasons)


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")
