"""
Does adaptive practice help? A simulation with 500 virtual learners.

Each virtual learner has a hidden ability (in "level" units, 1-5) and a personal learning speed.
  * chance of a right answer on a level-L item:  sigmoid(1.8 * (ability - L) + 1.1)
  * learning from an item is largest when the item is a little above the child's ability (the "just hard enough" zone)
We compare three practice policies over 12 sessions of 8 items:
  fixed-easy (always level 1), fixed-medium (always level 3), and adaptive (our 3-up / 1-down staircase).

This is a simulation, not data from children. It shows the engine behaves sensibly; it does not prove the effect size.

Run:  python ml/simulate_adaptive.py      ->  docs/adaptive_simulation.png, models/adaptive_simulation.json
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
rng = np.random.default_rng(7)
N, SESSIONS, ITEMS = 500, 12, 8


def p_correct(ability, level):
    return 1 / (1 + np.exp(-(1.8 * (ability - level) + 1.1)))


def gain(ability, level, speed):
    return speed * np.exp(-((level - ability - 0.5) ** 2) / 1.2)


def run(policy):
    ability = rng.uniform(0.6, 2.4, N)           # children who struggled in the screening
    speed = rng.uniform(0.02, 0.06, N)
    level = np.ones(N, int) if policy != "fixed-medium" else np.full(N, 3)
    streak = np.zeros(N, int)
    curve, success = [ability.mean()], []
    for _ in range(SESSIONS):
        right = 0
        for _ in range(ITEMS):
            lv = np.ones(N, int) if policy == "fixed-easy" else (np.full(N, 3) if policy == "fixed-medium" else level)
            ok = rng.random(N) < p_correct(ability, lv)
            ability = np.minimum(ability + gain(ability, lv, speed), 5.5)
            right += ok
            if policy == "adaptive":
                streak = np.where(ok, streak + 1, 0)
                up = streak >= 3
                level = np.where(up, np.minimum(level + 1, 5), np.where(~ok, np.maximum(level - 1, 1), level))
                streak = np.where(up, 0, streak)
        curve.append(ability.mean())
        success.append((right / ITEMS).mean())
    return {"ability": [round(float(x), 3) for x in curve], "success_rate": [round(float(x), 3) for x in success],
            "reached_level4": round(float((ability >= 4).mean()), 3)}


def main():
    res = {p: run(p) for p in ("fixed-easy", "fixed-medium", "adaptive")}
    (ROOT / "models").mkdir(exist_ok=True)
    json.dump(res, open(ROOT / "models" / "adaptive_simulation.json", "w"), indent=2)
    for p, r in res.items():
        print(f"{p:13s} ability {r['ability'][0]:.2f} -> {r['ability'][-1]:.2f} | "
              f"avg success {np.mean(r['success_rate']):.0%} | reached level 4+: {r['reached_level4']:.0%}")
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
        colors = {"fixed-easy": "#9AA3B5", "fixed-medium": "#F07A3A", "adaptive": "#0E9384"}
        for p, r in res.items():
            ax[0].plot(range(SESSIONS + 1), r["ability"], label=p, color=colors[p], lw=2.5)
            ax[1].plot(range(1, SESSIONS + 1), [x * 100 for x in r["success_rate"]], label=p, color=colors[p], lw=2.5)
        ax[0].set(title="Average skill level of 500 simulated children", xlabel="practice session", ylabel="skill (levels 1-5)")
        ax[1].set(title="Share of answers the child gets right", xlabel="practice session", ylabel="% correct", ylim=(0, 100))
        ax[1].axhspan(70, 85, color="#0E9384", alpha=.08)
        ax[1].text(SESSIONS - .2, 77, "'just hard enough' zone", ha="right", va="center", fontsize=8, color="#0B7468")
        for a in ax:
            a.grid(alpha=.25); a.spines[["top", "right"]].set_visible(False)
        ax[0].legend(frameon=False)
        fig.tight_layout()
        (ROOT / "docs").mkdir(exist_ok=True)
        fig.savefig(ROOT / "docs" / "adaptive_simulation.png", dpi=150)
        print("Saved docs/adaptive_simulation.png")
    except ImportError:
        print("(matplotlib not installed: skipped the chart)")


if __name__ == "__main__":
    main()
