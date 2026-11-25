# VisitFallback Gate 0 — decision record

## What was actually run

- 11 fixture scenarios, all synthetic and independently specified.
- Offline graph-shaped projection through `engine.py` compared to `oracle.py` exhaustive assignments.
- 19 offline tests PASS; 2 Relate integration tests SKIPPED in this environment because `relate-db` is unavailable.
- Offline JSON: `build/gate0-offline.json`. `gate0_status = PASS_OFFLINE_ONLY`.
- Zero false `COVERED` declarations against this small fixture oracle; **not a field safety metric**.

## What must still pass on Windows

```powershell
python -m unittest discover -s tests -v
python -m visitfallback.gate0 --backend both --store build/visitfallback-run1.rl --report build/gate0-both.json
```

1. Real Relate 1.0.1 `CREATE` and Cypher `MATCH` traverse the same 11 synthetic cases.
2. All covered/uncovered verdicts and assignments match the independent enumeration.
3. Live mutation via Cypher turns the rescue trip covered → uncovered → covered.
4. Removing Celine's `CAN_DO DRIVE` graph edge turns a covered visit into an uncovered one. **This is the strongest evidence that the graph is the runtime source of truth.**
5. `same_outcome=true` and `gate0_status=PASS_FULL_RELATE`.

## Decision

**CONDITIONAL TECHNICAL GO** only to prove the graph-backed implementation, not to release an actual caregiving service or assert superiority over the three named competitors. Do not start a UI sprint until Windows integration logs are reviewed.

## Reusable 90-second winning moment

"Tomorrow, an elderly person needs an outbound ride, an escort and a ride home. Sofia cancels. Omar confirms the first ride, Lina confirms the escort, Celine offers the return but does not confirm. A generic 'someone can help' alert looks reassuring; VisitFallback correctly says NOT COVERED. Celine confirms: COVERED. Her driving capability is revoked in Relate: NOT COVERED again. Every decision has a traceable graph edge and independent oracle agreement."

No claim that the real helpers accepted or that the trip occurred; the story is fully synthetic.
