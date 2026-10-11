import csv, json, random, time, urllib.request

rows = list(csv.reader(open("/data/golden.csv")))[1:]
while True:
    r = random.choice(rows)
    body = json.dumps({"features": [float(v) for v in r[:-1]],
                       "label": int(float(r[-1]))}).encode()
    req = urllib.request.Request("http://ai-service/predict", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=5).read()
    except Exception:
        pass
    time.sleep(0.05)
