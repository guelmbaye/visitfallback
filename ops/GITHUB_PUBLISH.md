# VisitFallback — GitHub publishing (Windows / PowerShell)

Repository: https://github.com/guelmbaye/visitfallback

This guide assumes a local working directory containing the project root (`visitfallback/`, `web/`, `tests/`, `data/`, `requirements.txt`). Use the **public-deployment patch** on top of the code you already tested; do not replace a modified backend/UI without comparing changes.

## 1. Add the public-ready files

Copy the contents of the patch to the root of your working tree, preserving its paths. In particular:

- `.gitignore` (**the dot and name are significant**)
- `visitfallback/public_webapp.py`
- `tests/test_public_webapp.py`
- `scripts/generate_demo_store.py`
- `ops/visitfallback.service`, `ops/nginx-directives.txt`, `ops/DEPLOY_PLESK.md`
- `ops/GITHUB_PUBLISH.md` (this guide)

Keep `data/scenarios.json` and the complete existing `visitfallback` Python package and `web` UI.

## 2. Create the *inspectable* Relate graph

```powershell
cd C:\Projects\visitfallback   # adapt to your real project path
.\.venv\Scripts\Activate.ps1   # if already configured
python -m unittest discover -s tests -v
python -m scripts.generate_demo_store
Test-Path .\data\demo.rl
Get-Item .\data\demo.rl | Select-Object Name,Length
```

The generator intentionally refuses to overwrite `data/demo.rl`. If it already exists, verify that it contains **only the synthetic demo** before deciding whether to keep or regenerate it. The graph to commit is the inspectable demonstration file, **not** a session graph under `build/`, `runtime/` or `/run/`.

## 3. Check what Git will publish

```powershell
git status --short
git check-ignore -v .\build\visitfallback-local-new.rl
git check-ignore -v .\data\demo.rl
```

Expected: build graph is ignored; **no matching ignore rule** is printed for `data/demo.rl` (exit code 1). If a global or `.git/info/exclude` rule still ignores `data/demo.rl`, inspect it before forcing any add.

If you previously tracked virtual environments, reports or runtime databases, adding `.gitignore` alone will NOT untrack them. Examine `git ls-files` before using `git rm --cached` on selected paths. Avoid broad forced removals that could drop important project files.

## 4. Git initialization (ONLY if not already initialized)

```powershell
git rev-parse --is-inside-work-tree
# If false / not a Git repository:
git init
git branch -M main
git remote add origin https://github.com/guelmbaye/visitfallback.git
```

If the local project is already connected to GitHub, skip initialization. Check its remote:

```powershell
git remote -v
```

## 5. Stage, review, and push

```powershell
git add .gitignore README.md requirements.txt `
  visitfallback web data/scenarios.json data/demo.rl tests scripts ops docs

git status --short
git diff --cached --stat

git commit -m "Prepare VisitFallback public Relate demo and reproducible graph"
git push -u origin main
```

If you have other project root files, review and add them individually (`make_fixtures.py`, for example); don't assume the staging command includes every file. If GitHub's `main` already has commits not in your local branch, `git fetch origin` and reconcile/pull before pushing; **do not use `--force`**.

## 6. Verify GitHub publicly

In a logged-out/private browser, verify:

- `https://github.com/guelmbaye/visitfallback` is public
- `data/demo.rl` exists (GitHub may not render binary `.rl` files; download availability is sufficient)
- the README explains **Relate single-file mode**, setup, synthetic data and significant AI assistance
- `visitfallback/public_webapp.py`, `scripts/generate_demo_store.py`, `ops/` and `web/` exist
- `.venv/`, `build/`, `.env`, session graphs and private media are **absent**
- add the GitHub repository topic **`relate`** (recommended extra: `relate-neo4j-hackathon`) using GitHub → About → gear icon → Topics
- select and add an appropriate open-source `LICENSE` file, if one is not yet present

**Security note:** `.gitignore` is NOT a secrets-removal or security tool. If a credential or private data was pushed in an earlier commit, remove it from Git history as appropriate, rotate the credential, and check all shared copies.

## 7. Link to Devpost (after verification)

- GitHub URL: `https://github.com/guelmbaye/visitfallback`
- Relate mode: **Single file**
- Persistent graph path: **`data/demo.rl`**
- Video: `https://youtu.be/dnZXDM7evWM`
- Live demo: `https://visitfallback.e-ntsi.com` **only after HTTPS, sessions and isolation are tested**
