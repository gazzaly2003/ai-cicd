import argparse, os, joblib, numpy as np, pandas as pd
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

p = argparse.ArgumentParser()
p.add_argument("--out", default="models/model.joblib")
p.add_argument("--noise", type=float, default=0.0)  # fraction of corrupted labels
a = p.parse_args()

X, y = load_digits(return_X_y=True)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
if a.noise > 0:
    rng = np.random.default_rng(0)
    idx = rng.random(len(ytr)) < a.noise
    ytr = ytr.copy()
    ytr[idx] = rng.integers(0, 10, idx.sum())

os.makedirs(os.path.dirname(a.out), exist_ok=True)
joblib.dump(LogisticRegression(max_iter=2000).fit(Xtr, ytr), a.out)

if not os.path.exists("eval/golden.csv"):
    df = pd.DataFrame(Xte)
    df["label"] = yte
    df.to_csv("eval/golden.csv", index=False)
print("saved", a.out)