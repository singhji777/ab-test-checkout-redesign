"""Synthetic A/B test: a redesigned (one-page) checkout vs. the old multi-step checkout on an e-commerce app.

Planted truths (so the analysis has something real to find):
  * 50/50 randomisation (no sample-ratio mismatch)
  * Treatment helps MOBILE a lot, DESKTOP barely at all  -> heterogeneous effect
  * A mild novelty effect: the mobile uplift is larger in the first days and settles later
  * Order value (for converters) is unchanged
"""
import numpy as np, pandas as pd
from pathlib import Path
rng = np.random.default_rng(11)
OUT = Path(__file__).resolve().parents[1] / "data" / "ab_test_checkout.csv"

N = 64000
start = pd.Timestamp("2025-09-01")
day = rng.integers(0, 14, N)
df = pd.DataFrame({
    "user_id": np.arange(100001, 100001 + N),
    "date": (start + pd.to_timedelta(day, unit="D")).strftime("%Y-%m-%d"),
    "group": rng.choice(["control", "treatment"], N, p=[0.5, 0.5]),
    "device": rng.choice(["mobile", "desktop"], N, p=[0.64, 0.36]),
    "user_type": rng.choice(["new", "returning"], N, p=[0.58, 0.42]),
    "traffic_source": rng.choice(["organic", "paid", "email", "direct"], N, p=[0.35, 0.30, 0.15, 0.20]),
})
base = {("mobile", "new"): 0.075, ("mobile", "returning"): 0.115, ("desktop", "new"): 0.105, ("desktop", "returning"): 0.150}
p = np.array([base[(d, u)] for d, u in zip(df.device, df.user_type)])
src_mult = df.traffic_source.map({"organic": 1.0, "paid": 0.85, "email": 1.25, "direct": 1.1}).values
p = p * src_mult
lift = np.ones(N)
t = (df.group == "treatment").values
novelty = 0.17 + 0.12 * np.exp(-day / 3.0)                # mobile uplift 29% early -> ~17% later
lift[t & (df.device == "mobile").values] = 1 + novelty[t & (df.device == "mobile").values]
lift[t & (df.device == "desktop").values] = 1.02
df["converted"] = (rng.random(N) < np.clip(p * lift, 0, 1)).astype(int)
df["revenue"] = np.where(df.converted == 1, np.round(rng.lognormal(7.35, 0.65, N), 0), 0.0)
df = df.sort_values(["date", "user_id"]).reset_index(drop=True)
df.to_csv(OUT, index=False)
print(df.shape, df.groupby("group").converted.mean().round(4).to_dict())
