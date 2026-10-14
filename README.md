# CI/CD for AI Systems

A complete, working example of how to ship an AI model safely. Every change goes through automated testing, a model quality gate, a gradual canary release, automatic rollback when quality drops, and a feature flag that switches the AI off instantly.

**Stack:** GitHub Actions (CI), ArgoCD (GitOps CD), Argo Rollouts (canary and automatic rollback), Prometheus and Grafana (monitoring), FastAPI and scikit-learn (the AI service), Docker, Kubernetes (kind, runs locally for free).

> Demo video: *add your link here*
> Repository: https://github.com/gazzaly2003/ai-cicd

---

## 1. Why a company needs this

AI fails silently. A new model can deploy with no errors and still give worse answers, respond slowly, or make wrong decisions, and nobody notices until customers complain or money is lost. Examples: a fraud model that lets more fraud through, a recommendation model that lowers sales, a support chatbot that starts giving bad answers.

Many companies still release AI changes by hand: someone trains a model, checks it on a laptop and pushes it to everyone. This project makes AI releases safe and automatic.

**The problem it solves**

- Bad models are often released with no automatic checks
- A faulty model can reach 100% of customers before anyone notices
- Rolling back takes time and often depends on someone being awake
- There is no record of who changed which model or setting

**How it helps**

| Safety layer | Business problem it solves |
|---|---|
| Automated tests and quality gate | A bad model is stopped before any customer sees it, and no one has to remember to check |
| Canary release (20%, 60%, 100%) | If something is wrong, only a small share of users is affected, not everyone |
| Automatic rollback | A drop in speed or accuracy is detected and reverted in minutes, even at night with nobody watching |
| Feature flag kill switch | Support can switch the AI off instantly with a fallback, with no redeploy and no waiting for a new build |
| GitOps (everything in Git) | Every release and rollback is recorded: who changed what and when, useful for audits and undoing mistakes |
| Monitoring (Prometheus and Grafana) | The team sees AI speed and quality in real time |

**What the company gains**

- **Lower risk:** failures are small and short instead of big outages
- **Faster releases:** teams ship AI updates often, without fear
- **Less manual work:** no release checklists and no staring at dashboards
- **Cheaper mistakes:** a failure caught at 20% of traffic costs far less than one at 100%
- **Accountability:** Git keeps a full history of every model and config change
- **No vendor lock-in:** all tools are free, standard and widely used

> In one sentence: it lets a team release AI models quickly without fearing that a bad model will reach all customers, because the system tests, rolls out gradually, monitors, and rolls back by itself.

*This is a working demonstration of the pattern. Production use needs the company's own model, real quality data, a real cluster and proper secret handling (see section 11).*

---

## 2. What this project proves

| Requirement | How it is shown | Result |
|---|---|---|
| Automated testing | pytest and a model quality gate run on every push | A bad model (accuracy about 0.33) fails CI and is never deployed |
| Canary deployment | Argo Rollouts shifts traffic 20%, then 60%, then 100% | A good release is promoted step by step |
| Automatic rollback on quality drop | Prometheus checks p95 latency and accuracy on the canary | A slow release (800 ms delay) fails analysis and is rolled back with no human action |
| Feature flags | `ai_enabled` in `k8s/flags-configmap.yaml` | The AI is turned off and on with a one-line Git change and no redeploy |

---

## 3. How it works

```
Developer pushes code or a new model
        |
GitHub Actions
  1. Unit tests (pytest)
  2. Model quality gate: fails if accuracy on the golden dataset < 0.90
  3. Build Docker image and publish to GitHub Container Registry
  4. Write the new image tag into k8s/rollout.yaml (GitOps)
        |
ArgoCD watches the repo and syncs the cluster
        |
Argo Rollouts: canary 20% -> 60% -> 100%
  Prometheus checks the new version while it rolls out:
    - p95 latency must stay <= 0.5 s
    - accuracy (from user feedback) must stay >= 85%
  Pass: promote.   Fail: automatic rollback to the stable version.
        |
Feature flag (k8s/flags-configmap.yaml)
  ai_enabled true/false switches the AI off with no redeploy.
```

Three safety layers: the **CI gate** blocks bad models before deploy, the **canary analysis** catches problems on real traffic, and the **feature flag** is an instant kill switch.

---

## 4. Requirements

Windows 10 or 11 (commands are PowerShell). Mac and Linux work with small changes.

| Tool | Where to get it | Check |
|---|---|---|
| Git | git-scm.com | `git --version` |
| Python 3.12 | python.org (tick "Add to PATH") | `python --version` |
| Docker Desktop | docker.com (must show "Engine running") | `docker --version` |
| kubectl | `winget install Kubernetes.kubectl` | `kubectl version --client` |
| kind | `winget install Kubernetes.kind` | `kind --version` |
| Helm | `winget install Helm.Helm` | `helm version` |
| GitHub account | github.com | |

Machine: 8 GB RAM minimum (16 GB recommended) and about 15 GB free disk. Everything is free and nothing runs in the cloud. Close and reopen the terminal after installing tools.

---

## 5. Step-by-step setup

### Step 1: Get the code

Use your own copy so the pipeline can push to it. On GitHub click **Fork**, then:

```powershell
cd $HOME\Documents
git clone https://github.com/<YOUR-GITHUB-USERNAME>/ai-cicd.git
cd ai-cicd
```

### Step 2: Change the names to yours (only if you forked)

Use your GitHub username in lowercase.

1. `argocd/app.yaml`: set `repoURL` to `https://github.com/<your-username>/ai-cicd.git`.
2. `k8s/rollout.yaml`: set the `image:` line to `ghcr.io/<your-username>/ai-cicd:latest` for now. The pipeline replaces it with a real tag after its first run.

### Step 3: Allow GitHub Actions to push

Repo **Settings, Actions, General, Workflow permissions, Read and write permissions, Save**.

### Step 4: Run the pipeline once

Add a blank line to `app/main.py`, then:

```powershell
git add .
git commit -m "First pipeline run"
git push
```

Open the **Actions** tab and wait for both jobs to turn green (2 to 4 minutes). The CI bot then commits the real image tag into `k8s/rollout.yaml`. Run `git pull --rebase` afterwards.

### Step 5: Make the image public

GitHub profile, **Packages**, `ai-cicd`, **Package settings**, **Change visibility**, **Public**. The cluster pulls the image without a password.

### Step 6 (optional): Run the AI service locally first

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python train.py
python -m pytest tests/
python eval/evaluate.py --min-accuracy 0.90
uvicorn app.main:app --port 8000
```

Open http://localhost:8000/docs to try `/predict`. Stop with Ctrl+C. If PowerShell blocks the activate script, run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.

### Step 7: Create the Kubernetes cluster

Start Docker Desktop and wait for "Engine running".

```powershell
kind create cluster --name ai-cicd
kubectl get nodes
```

The node must show `Ready`.

### Step 8: Install ArgoCD, Argo Rollouts and Prometheus/Grafana

Use `--server-side` for both Argo installs, otherwise the Rollout type may not register.

```powershell
kubectl create namespace argocd
kubectl apply -n argocd --server-side --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts --server-side --force-conflicts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl get crd | findstr rollouts

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack -n monitoring --create-namespace --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```

`rollouts.argoproj.io` must appear in the CRD list. Wait 5 to 10 minutes until everything is `Running`:

```powershell
kubectl get pods -A
```

### Step 9: Deploy the app with ArgoCD

```powershell
kubectl apply -f argocd\app.yaml
kubectl get applications -n argocd
kubectl get pods -n ai
```

After 1 to 4 minutes you should see `Synced` and 3 `ai-service` pods `1/1 Running`. If it shows `OutOfSync`, open the ArgoCD page, click `ai-service`, then **Refresh, Sync, Synchronize** (tick Server-Side Apply).

If a pod shows `ImagePullBackOff`, the package is not public (Step 5). Fix it, then run `kubectl delete pod -n ai -l app=ai-service`.

### Step 10: Start the traffic generator

The canary analysis needs real requests to measure.

```powershell
kubectl create configmap loadgen-code -n ai --from-file=loadgen\loadgen.py
kubectl create configmap loadgen-data -n ai --from-file=golden.csv=eval\golden.csv
kubectl apply -f loadgen\deploy.yaml
```

### Step 11: Open the dashboards

Each command needs its own terminal, left open:

```powershell
kubectl port-forward svc/argocd-server -n argocd 8081:443
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
kubectl port-forward -n ai svc/ai-service 8080:80
```

| Page | URL | Login |
|---|---|---|
| ArgoCD | https://localhost:8081 (accept the browser warning) | `admin` and the password below |
| Grafana | http://localhost:3000 | `admin` and the password below |
| The AI service | http://localhost:8080/docs | none |

Passwords are different on every new cluster:

```powershell
$p = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($p))

$p = kubectl -n monitoring get secret kube-prometheus-stack-grafana -o jsonpath="{.data.admin-password}"
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($p))
```

In Grafana go to **Explore**, choose **Prometheus**, click **Code**, and run `rate(labeled_predictions_total[1m])` to confirm data is flowing. Live accuracy:

```
sum(rate(correct_predictions_total[1m])) / sum(rate(labeled_predictions_total[1m]))
```

Quick test of the AI itself: on http://localhost:8080/docs open **POST /predict**, click **Try it out**, and send:

```json
{"features": [0,0,5,13,9,1,0,0,0,0,13,15,10,15,5,0,0,3,15,2,0,11,8,0,0,4,12,0,0,8,8,0,0,5,8,0,0,9,8,0,0,4,11,0,1,12,7,0,0,2,14,5,10,12,0,0,0,0,6,13,10,0,0,0]}
```

Expected answer: `"prediction": 0`.

---

## 6. Try the safety features

Always run `git pull --rebase` before editing, because the CI bot commits after each build. Run the PowerShell lines in the terminal. The JSON goes in the browser.

### A. A good release is promoted gradually

Add a comment to `app/main.py`, commit and push. Watch Actions go green, then:

```powershell
kubectl get rollout ai-service -n ai -w
kubectl get analysisrun -n ai
```

The rollout goes 20%, 60%, 100% and the analysis shows `Successful`.

### B. CI blocks a bad model

```powershell
python train.py --out models/model.joblib --noise 0.9
git add .
git commit -m "bad model test"
git push
```

The **Model quality gate** step fails and nothing is deployed. Undo with `git revert HEAD --no-edit` and `git push`.

### C. The canary catches a slow release and rolls back automatically

In `k8s/rollout.yaml` set `DELAY_MS` to `"800"`, then commit and push. The canary's p95 latency goes above 0.5 s, the analysis run shows `Failed`, and traffic returns to the stable version. Undo with `git revert HEAD --no-edit` and `git push`.

Grafana query for the latency spike:

```
histogram_quantile(0.95, sum(rate(predict_latency_seconds_bucket[1m])) by (le))
```

### D. Feature flag kill switch

In `k8s/flags-configmap.yaml` change `"ai_enabled": true` to `false`, then:

```powershell
git add .
git commit -m "Turn AI off"
git pull --rebase
git push
kubectl annotate application ai-service -n argocd argocd.argoproj.io/refresh=hard --overwrite
```

Wait 1 to 2 minutes. `POST /predict` now returns `"prediction": null` and `"fallback": true`, and the pods are not restarted. Set the flag back to `true` the same way to restore normal predictions.

---

## 7. Screenshots

Add your images to a `docs/` folder and link them here:

```
![Green pipeline](docs/actions-green.png)
![Bad model blocked by CI](docs/actions-red.png)
![Canary rollout in ArgoCD](docs/argocd-rollout.png)
![Failed canary rolled back](docs/argocd-rollback.png)
![Grafana latency](docs/grafana-latency.png)
![Feature flag fallback](docs/flag-fallback.png)
```

---

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| `kubectl` says `localhost:8080 refused` | Docker is not running, or run `kubectl config use-context kind-ai-cicd` |
| `kind get clusters` errors about the Docker API | Start Docker Desktop and wait for "Engine running" |
| "Can't reach the page" | That page's port-forward stopped. Run it again in a new terminal |
| `git push` rejected (fetch first) | `git pull --rebase`, then push again |
| `git pull` says unstaged changes | `git status`, then commit, stash or `git restore` the file |
| ArgoCD `OutOfSync` and `Missing` | Check `kubectl get crd \| findstr rollouts`, then Refresh and Sync |
| `no matches for kind "Rollout"` | Reinstall Argo Rollouts with `--server-side` (Step 8) |
| `ImagePullBackOff` | Make the GHCR package public (Step 5) |
| 422 "Field required: features" in `/docs` | The request body must be `{"features": [...64 numbers...]}` |
| Pods stuck `Pending` | Low memory. Raise `memory=` in `%USERPROFILE%\.wslconfig`, run `wsl --shutdown`, restart Docker |
| CI fails to push | Settings, Actions, General, Read and write permissions |
| PowerShell error on `{"prediction": ...}` | That text is output to read, not a command |

---

## 9. Project structure

```
ai-cicd/
  app/                 FastAPI service, metrics, feature flag logic
  tests/               pytest tests
  eval/                golden.csv and evaluate.py (quality gate)
  models/              trained model (model.joblib)
  loadgen/             traffic generator
  k8s/                 Rollout, Service, ServiceMonitor, AnalysisTemplate, flags ConfigMap
  argocd/              ArgoCD Application
  .github/workflows/   CI pipeline (ci.yml)
  train.py             trains the model (--noise simulates a bad one)
  Dockerfile
```

---

## 10. Clean up

Pause: quit Docker Desktop (the cluster is kept). Delete everything:

```powershell
kind delete cluster --name ai-cicd
```

---

## 11. Limitations and next steps

This is a local demonstration. It uses a small public dataset (scikit-learn digits), simulated user feedback, and a single-node local cluster. Production use would need a managed cluster, a model registry, real feedback data, secrets management, and a dedicated feature flag service such as flagd or Unleash. Ideas for the future: shadow deployments, drift detection, and an LLM-as-judge quality check for LLM applications.

---

## 12. License

MIT. See the `LICENSE` file.
