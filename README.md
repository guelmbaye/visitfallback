# VisitFallback — Confirmed Doesn't Mean Covered

**Everyone said yes. The plan still fails.**

A fictional medical appointment needs three things: **a ride there, an escort, and a ride home**. Three helpers confirm, but a hidden scheduling conflict makes one commitment impossible. VisitFallback traces the care chain with **Relate by Neo4j** and verifies whether the *whole plan* can actually be executed.

**[Live interactive demo](https://visitfallback.e-ntsi.com)** · **[1:50 video demo](https://youtu.be/dnZXDM7evWM)** · [Relate by Neo4j Hackathon](https://relate.devpost.com/)

> **Synthetic-data demonstration only.** No real patients, caregivers, appointments, medical records or messages. Not medical advice, a medical device, or a production care-coordination service.

## The decisive moment

All three offers are confirmed in both states D and E. One conflicting commitment changes the answer.

| | D — Complete rescue | E — Hidden conflict |
|---|---|---|
| Confirmed commitments | 3 / 3 | 3 / 3 |
| Executable commitments | 3 / 3 | **2 / 3** |
| Overall plan | **COVERED** | **NOT COVERED** |

In E, Celine's confirmed return ride (**10:45–11:30**) overlaps another engagement (**11:00–11:15**). The 15-minute clash invalidates the return leg even though her confirmation has not changed.

**Confirmed ≠ Covered.** A simple count of confirmations gives the wrong answer to this *illustrative* scenario; this is not a benchmark against commercial care-coordination tools.

## Explore the five states

| State | Event | Result |
|---|---|---|
| **A** | Sofia covers all three obligations | Covered |
| **B** | Sofia cancels | Not covered |
| **C** | Omar confirms outbound; Lina confirms escort; return unconfirmed | Not covered |
| **D** | Celine also confirms return | Covered |
| **E** | Same confirmations as D, but Celine becomes double-booked | Not covered |

Try **D → E → D** in the [live demo](https://visitfallback.e-ntsi.com) to see the same care plan fail and recover. The interface shows a 3D-style Home → Clinic → Home journey, each required step, a conflict timeline, and the live connected explanation.

## How it uses Relate

**Relate is part of the decision path, not just the visualization.**

- **Mode:** embedded Python, **single-file** `.rl` graph (`relate-db==1.0.1`), without a separate database server.
- **Graph entities:** `Visit`, `Need`, `Offer`, `Person`, `Capability`, `Window`, and `Busy`.
- **Graph relationships:** required obligations, offered help, required capabilities, confirmed offers, availability, and conflicting commitments.
- **Cypher:** queries load the relationship model; switching A–E changes real offer states and the conflicting `Busy` window **in the same session graph**, then queries the graph again.
- **Decision:** a deterministic feasibility engine checks capabilities, times, locations and overlapping engagements using those graph-derived facts.
- **Verification:** a separately implemented exhaustive oracle checks the result. Disagreement fails closed rather than displaying a misleading success.

For inspection, the repository should include the **synthetic, persisted** example at [`data/demo.rl`](data/demo.rl). Generate it with `python -m scripts.generate_demo_store` if it has not yet been committed. The public adapter uses a **separate temporary `.rl` file for each browser session**; it does not edit the repository's example file.

### Architecture

```text
Browser: five states + 3D journey + timeline
            |
            v
Python API / isolated browser session
            |
            v
Relate 1.0.1 (.rl file) -- live Cypher reads and mutations
            |
            v
Deterministic coverage / scheduling checks
            |
            +--> Independent exhaustive oracle
            |
            v
Explained status: COVERED or NOT COVERED
```

## Run it locally

Requires a supported Python environment with `relate-db==1.0.1` available.

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m visitfallback.webapp --store build/visitfallback-local-new.rl --port 8766
```

Open **http://127.0.0.1:8766/**. Use a **new** `.rl` file name for each fresh run; the local demo refuses to overwrite an existing graph. The app is intentionally bound to localhost.

To produce the inspectable single-file store for the repository:

```bash
python -m scripts.generate_demo_store
```

This creates `data/demo.rl` from fictional source data and refuses to overwrite an existing file. If the file is already present, inspect it rather than regenerating it blindly.

For a multi-visitor public demo, use the dedicated `visitfallback.public_webapp` **behind HTTPS/Nginx**, not the local `visitfallback.webapp`. See [Plesk deployment instructions](ops/DEPLOY_PLESK.md) and the [GitHub publishing guide](ops/GITHUB_PUBLISH.md).

## Verification and limitations

Automated tests cover missing confirmations, cancellations, conflicting bookings, insufficient capabilities, incompatible times and handoffs, Relate graph mutations, independent oracle comparisons, and public-demo session isolation. Run the suite locally; do not rely on a claim of test counts without executing it in your environment.

The verified output means **a synthetic schedule is consistent with stated assumptions**. It does **not** mean a real person will arrive or that care has been delivered. This prototype has no real caregiver communication, authentication for sensitive data, patient records or production safety review.

## Built with

**Relate by Neo4j · Cypher · Python · JavaScript · HTML/CSS · SVG** — with a dependency-free frontend and a CSS 3D-style journey.

## AI assistance

Significant AI assistance contributed to implementation, debugging, tests, copywriting, design and video editing. The developer independently exercised the real Relate integration and reviewed the interactive demo and its synthetic scenarios.

## Source and deployment notes

- The [public demo](https://visitfallback.e-ntsi.com) is for fictional, low-traffic judging only.
- Public hosting must use isolated per-browser stores, HTTPS and a reverse proxy; do not serve source files or `.rl` files from the website's document root.
- The repository should contain the documented `data/demo.rl`, the mandatory `relate` GitHub topic, and an appropriate license selected by the author.
