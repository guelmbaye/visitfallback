# VisitFallback — Cinematic UI V2 / Concise copy

This release **shortens only visible text in the interface**. The A–E sequence, the 3D journey, the 15-minute conflict, Relate queries, deterministic engine, independent oracle and privacy disclaimers remain unchanged.

### What changed

- Shorter hero and section copy; removed redundant section descriptions.
- Five scenario controls use compact labels and retain descriptive accessibility labels.
- Decision explanations are one sentence long.
- Each care-step card keeps its current result visible; proposed/withdrawn offers move under **Other offers** (expand on click).
- Graph and evidence panels use concise labels; **Cypher & methodology** remains expandable.
- Relate backend, API, scenarios and frozen file hashes are identical to the tested contrast release.

### Windows

```powershell
cd C:\Projects\VisitFallback_Cinematic_UI_V2_Concise
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m visitfallback.webapp --store build/visitfallback-concise-run1.rl --port 8766
```

Open http://127.0.0.1:8766/, then test D → E → D. Use a new `.rl` name; stop prior server before starting this one.

**Synthetic only. Not medical advice.** Do not expose the local HTTP server publicly without hardening.
