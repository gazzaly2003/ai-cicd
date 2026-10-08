import argparse, sys, joblib, pandas as pd
from sklearn.metrics import accuracy_score

p = argparse.ArgumentParser()
p.add_argument("--model", default="models/model.joblib")
p.add_argument("--min-accuracy", type=float, default=0.90)
a = p.parse_args()

df = pd.read_csv("eval/golden.csv")
model = joblib.load(a.model)
acc = accuracy_score(df["label"], model.predict(df.drop(columns="label").values))
print(f"accuracy={acc:.4f} (required >= {a.min_accuracy})")
sys.exit(0 if acc >= a.min_accuracy else 1)