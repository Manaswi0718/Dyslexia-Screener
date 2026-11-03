"""
Step 2 - Train the dyslexia-risk model on the Rello et al. (2020) Kaggle dataset.

Trains TWO models:
  1. FULL model     - all ~197 per-exercise features (best possible score, for the README)
  2. PORTABLE model - language-independent summary features that OUR games also
                      produce (accuracy, miss rate, hits, misses, clicks, age).
                      This is the one the app uses.

Usage:  python ml/train.py data/Dyt-desktop.csv
Outputs: models/portable_model.joblib, models/metrics.json, models/shap_summary.png
"""
import json, re, sys
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, recall_score, precision_score, balanced_accuracy_score, confusion_matrix
from sklearn.ensemble import RandomForestClassifier

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

OUT = Path("models"); OUT.mkdir(exist_ok=True)


def load(path):
    df = pd.read_csv(path, sep=None, engine="python")          # auto-detects ; or ,
    df.columns = [c.strip() for c in df.columns]
    target = next(c for c in df.columns if c.lower() == "dyslexia")
    y = df[target].astype(str).str.strip().str.lower().map({"yes": 1, "no": 0, "1": 1, "0": 0})
    df = df[y.notna()].copy(); y = y[y.notna()].astype(int)
    print(f"Loaded {len(df)} rows | dyslexia = {y.sum()} ({y.mean():.1%})")
    return df, y


def per_exercise_cols(df):
    pat = re.compile(r"^(Clicks|Hits|Misses|Score|Accuracy|Missrate)(\d+)$", re.I)
    return [c for c in df.columns if pat.match(c)]


def portable_features(df):
    """Summary stats our own games can produce, regardless of language."""
    def group(name):
        cols = [c for c in df.columns if re.match(rf"^{name}\d+$", c, re.I)]
        return df[cols].apply(pd.to_numeric, errors="coerce")
    acc, miss, hits, misses, clicks = (group(n) for n in ["Accuracy", "Missrate", "Hits", "Misses", "Clicks"])
    X = pd.DataFrame({
        "age": pd.to_numeric(df["Age"], errors="coerce"),
        "acc_mean": acc.mean(axis=1), "acc_std": acc.std(axis=1), "acc_min": acc.min(axis=1),
        "missrate_mean": miss.mean(axis=1), "missrate_max": miss.max(axis=1),
        "hits_mean": hits.mean(axis=1), "misses_mean": misses.mean(axis=1),
        "clicks_mean": clicks.mean(axis=1),
        "hit_ratio": hits.sum(axis=1) / clicks.sum(axis=1).replace(0, np.nan),
    })
    return X.fillna(X.median())


def make_model(pos_weight):
    if HAS_XGB:
        return XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.8,
                             colsample_bytree=0.8, scale_pos_weight=pos_weight, eval_metric="logloss")
    return RandomForestClassifier(n_estimators=400, class_weight="balanced", min_samples_leaf=3, random_state=0)


def evaluate(name, X, y):
    pos_weight = (y == 0).sum() / max((y == 1).sum(), 1)
    cv = StratifiedKFold(5, shuffle=True, random_state=42)
    proba = cross_val_predict(make_model(pos_weight), X, y, cv=cv, method="predict_proba")[:, 1]
    # choose threshold that maximises balanced accuracy (screening: we care about recall)
    ths = np.linspace(0.05, 0.95, 91)
    best = max(ths, key=lambda t: balanced_accuracy_score(y, proba >= t))
    pred = proba >= best
    m = {
        "roc_auc": round(roc_auc_score(y, proba), 3),
        "recall_dyslexia": round(recall_score(y, pred), 3),
        "precision_dyslexia": round(precision_score(y, pred), 3),
        "balanced_accuracy": round(balanced_accuracy_score(y, pred), 3),
        "threshold": round(float(best), 2),
        "confusion_matrix [[TN,FP],[FN,TP]]": confusion_matrix(y, pred).tolist(),
        "n_features": X.shape[1],
    }
    # baseline: always predict "no dyslexia"
    m["baseline_balanced_accuracy"] = 0.5
    print(f"\n== {name} ==");  [print(f"  {k}: {v}") for k, v in m.items()]
    model = make_model(pos_weight).fit(X, y)
    return model, m


def main(path):
    df, y = load(path)
    full_X = df[per_exercise_cols(df)].apply(pd.to_numeric, errors="coerce")
    full_X["age"] = pd.to_numeric(df["Age"], errors="coerce")
    full_X = full_X.fillna(full_X.median())
    _, full_m = evaluate("FULL model (all exercises)", full_X, y)

    port_X = portable_features(df)
    port_model, port_m = evaluate("PORTABLE model (used in app)", port_X, y)

    joblib.dump({"model": port_model, "features": list(port_X.columns),
                 "threshold": port_m["threshold"], "medians": port_X.median().to_dict()},
                OUT / "portable_model.joblib")
    json.dump({"model_type": "XGBoost" if HAS_XGB else "RandomForest",
               "full": full_m, "portable": port_m}, open(OUT / "metrics.json", "w"), indent=2)

    try:
        import shap, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        sv = shap.TreeExplainer(port_model).shap_values(port_X)
        if isinstance(sv, list): sv = sv[1]
        if getattr(sv, "ndim", 2) == 3: sv = sv[:, :, 1]
        shap.summary_plot(sv, port_X, show=False); plt.tight_layout()
        plt.savefig(OUT / "shap_summary.png", dpi=150); print("\nSaved models/shap_summary.png")
    except Exception as e:
        print(f"\n(SHAP plot skipped: {e})")
    print("Saved models/portable_model.joblib and models/metrics.json")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/Dyt-desktop.csv")
