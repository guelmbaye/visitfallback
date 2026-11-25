# Gate 1 E — adversarial contrast audit

## Hypothesis

**Three confirmations do not entail a feasible care plan.** A helper can confirm an obligation and nevertheless be unavailable because of another recorded commitment.

## Negative control and oracle

The synthetic return runs 10:45–11:30. In D, the selected return helper Celine is busy 12:00–12:30: no overlap, so fully covered. In E, all three confirmations are *identical* to D but the existing `Busy` node for Celine is moved to 11:00–11:15. A naive `all needs have a confirmed offer` baseline returns **true** in E, but the deterministic engine and independent exhaustive oracle both return **false** because the return helper is double-booked.

No real people are contacted. A synthetic confirmed offer represents a demo state, not evidence of consent.

| Check | Expected |
|---|---|
| A | 3 confirmed, 3 eligible, covered |
| B | 0 confirmed, 0 eligible, not covered |
| C | 2 confirmed, 2 eligible, not covered |
| D | 3 confirmed, 3 eligible, covered |
| **E** | **3 confirmed, 2 eligible, not covered** |
| E → D | Restored full coverage, conflict removed |
| D → E | False coverage blocked, conflict present |
| Cypher `BUSY_DURING` removed or corrupted | Fail instead of showing a positive proof |
| Other original Gate0 scenarios | Unchanged |

## Cypher-backed evidence

- `MATCH (v:Visit ...)-[:HAS_HELPER]->(p:Person)-[:BUSY_DURING]->(b:Busy ...) SET b.start=$start, b.end=$end RETURN ...`
- The same Relate `.rl` file is used throughout the UI session.
- The readback is checked against the phase contract before the UI can show PASS.
- The standalone oracle reads the deliberately declared synthetic scenario rather than importing the engine.

## Claims boundary

This is **not** a clinical safety evaluation, proof of actual visit fulfillment, or a benchmark against production apps. E is a conflict-based false confirmation counterexample, not a demonstration of *three individually eligible but globally impossible* assignments.

## Build-environment evidence

The script compilation and 29 offline tests pass; 6 real Relate tests are skipped when the package is absent. Chromium runs A→B→C→D→E→D against an **offline fixture-backed mock**, checks `3/3 confirmed` versus `2/3 eligible` and displays no JS errors. The final Relate check must be performed by the user on Windows.
