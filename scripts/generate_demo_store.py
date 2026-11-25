"""Generate the synthetic, inspectable single-file Relate store for GitHub.

Refuses to overwrite. Not the public runtime's mutable per-browser store.
"""
from pathlib import Path
from visitfallback.demo_service import CareDemo

store = Path('data/demo.rl')
if store.exists():
    raise SystemExit(f'{store} already exists — refusing to overwrite')

app = CareDemo(str(store), 'data/scenarios.json')
try:
    initial = app.snapshot()
    if (initial['phase'], initial['covered'], initial['confirmed_count'], initial['covered_count']) != ('A', True, 3, 3):
        raise AssertionError('Unexpected initial graph state')
    if not initial['proof']['same_outcome']:
        raise AssertionError('Relate / oracle mismatch')
    print(f'PASS: {store} — synthetic Relate graph, phase A, oracle parity')
finally:
    app.close()
