"""Presentation-only regression checks for VisitFallback cinematic UI.

These checks do not emulate Relate. Full integration tests still require the
real relate-db package and execute on the user's Windows environment.
"""
import hashlib
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'web/index.html').read_text(encoding='utf8')
CSS=(ROOT/'web/styles.css').read_text(encoding='utf8')
JS=(ROOT/'web/app.js').read_text(encoding='utf8')

class CinematicUiContract(unittest.TestCase):
    def test_care_first_story_and_five_phase_controls(self):
        self.assertIn('Everyone said',HTML)
        self.assertIn('Confirmed ≠ Covered',HTML)
        for phase in 'ABCDE':
            self.assertIn(f'data-phase="{phase}"',HTML)
        self.assertIn('SYNTHETIC DATA',HTML)
        self.assertIn('Not medical advice',HTML)

    def test_real_3d_scene_and_reduced_motion_accessibility(self):
        self.assertIn('perspective:',CSS)
        self.assertIn('rotateX(',CSS)
        self.assertIn('.island',CSS)
        self.assertIn('prefers-reduced-motion:reduce',CSS)
        self.assertIn('aria-live="polite"',HTML)

    def test_evidence_and_timeline_are_live_controls(self):
        for ident in ['sceneConflict','busyBar','overlapMarker','timelineVerdict','graph','cypher','oracleProof','relateProof','count','confirmation']:
            self.assertIn(f'id="{ident}"',HTML)
        for function in ['renderNeeds','renderReason','renderTimeline','renderGraph','render']:
            self.assertIn(f'function {function}',JS)
        self.assertIn("'/api/state'",JS)
        self.assertIn("'/api/phase'",JS)

    def test_no_external_frontend_dependencies_and_safe_text(self):
        self.assertNotIn('<script src="https:',HTML)
        self.assertNotIn('@import',CSS)
        self.assertIn('const clean =',JS)
        self.assertIn('clean(n.',JS)
        self.assertIn('It does not send messages to real helpers',HTML)
        self.assertIn('document.body.dataset.coverage',JS)

    def test_svg_column_labels_have_explicit_contrast(self):
        # SVG text defaults to black when its fill is not set.
        self.assertIn('.graph svg .column-label', CSS)
        self.assertIn('fill:#B4D5E1', CSS)
        for label in ['PERSON / OFFER', 'NEED', 'CAPABILITY', 'FEASIBILITY']:
            self.assertIn(label, JS)

    def test_concise_ui_preserves_proof_and_collapsible_offer_details(self):
        self.assertIn('One visit. Five outcomes.',HTML)
        self.assertIn('Verified. Not assumed.',HTML)
        self.assertIn('need-offer-details',JS)
        self.assertIn('Other offers',JS)
        self.assertIn('3 confirmed. 1 conflict.',JS)
        self.assertIn('Celine is double-booked during the return.',JS)
        self.assertNotIn('Two commitments are not a complete plan.',JS)
        self.assertIn('It does not send messages to real helpers',HTML)

    def test_backend_stays_frozen(self):
        hashes=json.loads((ROOT/'docs/BACKEND_FROZEN_HASHES.json').read_text(encoding='utf8'))
        self.assertTrue(hashes)
        for rel,digest in hashes.items():
            self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),digest,rel)
