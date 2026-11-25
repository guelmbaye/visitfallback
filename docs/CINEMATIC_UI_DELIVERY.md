# VisitFallback — Cinematic UI delivery notes

## What changed

This is a **presentation-only** upgrade on the proven Gate 1 + E service. Only `web/index.html`, `web/app.js` and `web/styles.css` were changed; five extra contract tests and documentation were added. Backend hashes are provided separately.

### 3D / visual system
- Premium dark teal / coral palette; responsive 3D CSS journey across Home → Clinic → Home.
- Scene transition into E: return station and route turn coral, a return-risk chip appears.
- Five phase buttons A–E mutate the **same** Relate store via the existing `/api/phase` endpoint.
- Hero decision panel shows **confirmed offers** and **individually executable obligations** separately.
- D is green (3/3 confirmed, 3/3 executable). E is coral (3/3 confirmed, 2/3 executable).
- A dynamic schedule shows 10:45–11:30 Return vs Celine's busy window, overlapping by 15 minutes only in E.
- An SVG graph is rendered from the graph-derived API snapshot, not a preset static image; clicking D/E updates the explanation.
- The real Cypher queries and three independent proof results remain inspectable below the human story.
- `prefers-reduced-motion` fallback, keyboard focus, mobile layout, no libraries/CDNs.

### Verification performed in build environment
- Python `unittest discover`: **40 tests discovered, 34 PASS, 6 SKIP (real Relate unavailable here)**.
- JavaScript syntax checked using Node `--check`.
- In-memory Chromium test with API responses derived from the synthetic fixture using a separately composed projection (NOT real Relate integration): **1440×900, 1366×768, 390×844**. D→E shows `PLAN COVERED` → `PLAN NOT COVERED`, 3/3 confirmed throughout, 2/3 executable in E. E→D hides overlap and restores covered status. No JavaScript exceptions or document horizontal overflow.
- Actual Relate validation of this *new front end* **must be rerun on the user's Windows machine**. Gate 1+E backend 35/35 PASS was reported by the user and is not altered by this package.

## Video direction (first 90 seconds)

- 0–15 seconds: the 3D home→clinic→home journey, the human question.
- 15–30 seconds: A→B cancellation: the plan breaks.
- 30–45 seconds: C→D, all three confirmations, reassuring green state.
- 45–70 seconds: **D→E, the decisive surprise**. Three confirmations remain. Plan switches coral; one commitment is in conflict.
- 70–85 seconds: scroll to 15-minute overlap on Celine's timeline.
- 85–105 seconds: trace Relate graph connections and open actual Cypher evidence.
- 105–115 seconds: return to D, verification PASS, synthetic-data disclaimer.

## Limits

The UI is **not a medical app**, not a logistics or dispatch service, and cannot verify actual arrivals, capability, consent, or availability outside the synthetic model. Real-world appointment coverage and comparative superiority to other tools remain unverified. The built-in HTTP server must remain local-only until independently hardened.
