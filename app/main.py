   # release 2
import json, os, time
from typing import List, Optional
import joblib, numpy as np
from fastapi import FastAPI, Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

MODEL = joblib.load(os.getenv("MODEL_FILE", "models/model.joblib"))
FLAGS_FILE = os.getenv("FLAGS_FILE", "flags.json")
DELAY_MS = int(os.getenv("DELAY_MS", "0"))  # simulates a latency regression
VERSION = os.getenv("APP_VERSION", "dev")

REQS = Counter("http_requests_total", "requests", ["status"])
LAT = Histogram("predict_latency_seconds", "latency",
                buckets=(.01, .025, .05, .1, .25, .5, 1, 2.5))
LABELED = Counter("labeled_predictions_total", "predictions that received feedback")
CORRECT = Counter("correct_predictions_total", "correct predictions")

app = FastAPI()


def flags():
    try:
        with open(FLAGS_FILE) as f:
            return json.load(f)
    except Exception:
        return {"ai_enabled": True, "return_probabilities": False}


class Req(BaseModel):
    features: List[float]
    label: Optional[int] = None  # simulated user feedback


@app.get("/healthz")
def health():
    return {"ok": True, "version": VERSION}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/predict")
def predict(r: Req):
    start = time.time()
    f = flags()
    if not f.get("ai_enabled", True):  # feature flag = kill switch
        return {"prediction": None, "fallback": True, "version": VERSION}
    if DELAY_MS:
        time.sleep(DELAY_MS / 1000)
    probs = MODEL.predict_proba(np.array(r.features).reshape(1, -1))[0]
    pred = int(MODEL.classes_[probs.argmax()])
    if r.label is not None:
        LABELED.inc()
        if pred == r.label:
            CORRECT.inc()
    LAT.observe(time.time() - start)
    REQS.labels("200").inc()
    out = {"prediction": pred, "version": VERSION}
    if f.get("return_probabilities"):
        out["probabilities"] = probs.tolist()
    return out