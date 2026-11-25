# VisitFallback — Plesk public demo deployment

> **Synthetic-only hackathon demonstration.** Do not upload patient, caregiver or medical data. **Never expose the original local `visitfallback.webapp` directly to the internet.** Use `visitfallback.public_webapp` below. This patch is based on the verified `VisitFallback_Cinematic_UI_V2_Concise` source; reconcile any changes made in your GitHub repository before copying it over.

## 0. Why this patch matters

The local application stores its `CareDemo` instance in one global `Handler.demo`; with multiple web visitors, clicking E in one browser would change the state shown in another. The public adapter gives **one independent Relate `.rl` store per browser cookie**, limits active sessions to 24 by default, reaps idle sessions, and leaves the verified engine, Cypher adapter, oracle and UI unchanged. One Python process is required; this is a small traffic-limited jury demo, **not a production healthcare service**.

The persistent `data/demo.rl` is separately committed to GitHub **for inspection**. The public service generates disposable per-browser graphs; it does not mutate the repository file.

## 1. Merge and publish code

From the local repo root, copy these NEW files from the patch ZIP (do not blindly replace your current backend or UI):

- `visitfallback/public_webapp.py`
- `tests/test_public_webapp.py`
- `scripts/generate_demo_store.py`
- `ops/visitfallback.service`, `ops/nginx-directives.txt`, `ops/DEPLOY_PLESK.md`

Run on a Windows workstation that has already passed the Relate tests:

```powershell
python -m unittest discover -s tests -v
python -m scripts.generate_demo_store
Test-Path .\data\demo.rl
```

**Expected on Windows with Relate installed: 46 tests, all PASS.** If `data/demo.rl` already exists, the generator refuses to overwrite it. Inspect it with the corresponding Relate engine first. The provided `.gitignore` excludes temporary `.rl` files while explicitly allowing `data/demo.rl`. Verify that Git stages that file normally; see `ops/GITHUB_PUBLISH.md`.

For a temporary browser test on Windows (no HTTPS), use the *explicitly local-only* cookie setting:

```powershell
python -m visitfallback.public_webapp --store-dir build\public-test --port 8767 --origin http://127.0.0.1:8767 --dev-http
```

Open `http://127.0.0.1:8767/`, then test D → E → D. Without `--dev-http`, cookies are intentionally marked `Secure` and only persist over HTTPS.

Commit the files and publish to your existing GitHub repo:

```powershell
git add visitfallback/public_webapp.py tests/test_public_webapp.py scripts/generate_demo_store.py ops/ data/demo.rl
git status
git commit -m "Harden VisitFallback public Relate demo with isolated browser sessions"
git push origin main
```

Ensure the repository is public, carries the mandatory GitHub topic **`relate`**, contains a README that explains the embedded **single-file** mode, and has a license plus AI-assistance disclosure.

## 2. Prepare Plesk source and Python

In Plesk, connect `https://github.com/guelmbaye/visitfallback` (`main`) and pull/deploy to the intended project folder. **Keep that folder outside the domain's web document root.** Create a separate, empty directory to use as the static document root; Nginx will proxy all requests to Python.

On the server, locate the actual project root rather than guessing the Plesk vhost path:

```bash
find /var/www/vhosts -path '*/visitfallback/public_webapp.py' -print 2>/dev/null
```

Open a shell as the Plesk domain system user and replace `PROJECT_DIR` with the discovered path:

```bash
cd PROJECT_DIR
python3 --version
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m unittest discover -s tests -v
```

**Block deployment if installing `relate-db==1.0.1` or the real Relate integration tests fail on this Linux/Python environment.**

## 3. systemd service (root privileges required)

Use `ops/visitfallback.service` as a template: replace its `REPLACE_WITH_...` placeholders with the absolute project directory, Plesk system user and group. The service binds only to **127.0.0.1:8766**, stores per-browser Relate files under **`/run/visitfallback/stores`** (systemd manages that runtime directory), and caps sessions at 24.

```bash
sudo cp ops/visitfallback.service /etc/systemd/system/visitfallback.service
sudo nano /etc/systemd/system/visitfallback.service
sudo systemctl daemon-reload
sudo systemctl enable --now visitfallback
sudo systemctl status visitfallback --no-pager
sudo journalctl -u visitfallback -n 80 --no-pager
```

The startup line should say: `Relate preflight PASS; isolated synthetic browser sessions enabled`. Only **one worker/process** may own these in-memory session objects. `systemd` will restart the server if it crashes. On a service restart, old temporary sessions are intentionally discarded, and browsers reinitialize their demos on reload.

## 4. Plesk nginx proxy and HTTPS

Plesk **Websites & Domains → visitfallback.e-ntsi.com → Apache & nginx Settings**:

- Disable **Proxy mode** to prevent Plesk's default duplicate `location /` block.
- Disable **Serve static files directly by nginx**; do not serve the Git working directory.
- Paste `ops/nginx-directives.txt` in **Additional nginx directives** and Apply.
- Use a valid TLS certificate (for example Let's Encrypt through Plesk SSL It!) and enable HTTPS redirect.
- Leave ports 8766 and the Python process inaccessible from the public internet; expose only 443 through Nginx.

If Plesk rejects `location /` as duplicate, recheck **Proxy mode** and custom nginx templates. Do not disable nginx globally or expose the source tree as a workaround.

## 5. Public smoke tests

From a different network or private browser window:

- `https://visitfallback.e-ntsi.com/` loads; Relate connected and synthetic-only flags appear.
- A → B → C → D → E → D returns **3/3 → 0/3 → 2/3 → 3/3 → 2/3 → 3/3 executable**.
- Open a second incognito/private browser profile: change to E in one profile; the other remains in its own state A (or its chosen state).
- `https://visitfallback.e-ntsi.com/data/demo.rl`, `/data/scenarios.json`, `/.git/config` and `/visitfallback/engine.py` must all return **404/403**, never file contents.
- `/api/state` must return JSON with `data_kind: SYNTHETIC_ONLY`; rate-limited/capacity-exhausted sessions fail closed.
- Verify the video URL `https://youtu.be/dnZXDM7evWM` and source repo URL `https://github.com/guelmbaye/visitfallback` from a logged-out browser.

## 6. Devpost fields

- **Try it out:** `https://visitfallback.e-ntsi.com` (only after external smoke test)
- **Video:** `https://youtu.be/dnZXDM7evWM`
- **Public GitHub repo:** `https://github.com/guelmbaye/visitfallback`
- **Relate mode:** `Single file`
- **Persistent store path:** `data/demo.rl` (only when genuinely committed)
- **Why this mode:** `Relate runs embedded in Python with a portable single-file graph. The repository includes an inspectable synthetic .rl file, while each demo visitor uses an isolated temporary Relate graph so interactions do not affect other judges.`

The contest rules available to us did not explicitly confirm whether the same person may submit a second solo entry. Obtain organizer clarification before final submission if needed.

## Limitations

This isolates browsers but is still a **single-thread, small-capacity HTTP server**, and it cannot safely handle production traffic or sensitive data. It has no accounts or real caregiver actions, no abuse-resistant public rate limiter, and no production security review. Keep the VPS monitored during judging, and consider upstream request-rate controls for the public domain.
