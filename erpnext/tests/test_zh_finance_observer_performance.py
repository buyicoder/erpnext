from pathlib import Path
from unittest import TestCase


class TestZhFinanceObserverPerformance(TestCase):
	def setUp(self):
		self.source = (
			Path(__file__).parents[2]
			/ "erpnext"
			/ "public"
			/ "js"
			/ "zh_finance_overrides.js"
		).read_text()

	def test_dom_localization_batches_mutations_once_per_animation_frame(self):
		self.assertIn("requestAnimationFrame(flush_localization)", self.source)
		self.assertIn("const pending_localization_roots = new Set();", self.source)
		self.assertNotIn("characterData: true", self.source)

	def test_attribute_localization_is_idempotent(self):
		self.assertIn("if (input.title !== localized) input.title = localized;", self.source)
		self.assertIn(
			"if (input.getAttribute(\"aria-label\") !== localized)",
			self.source,
		)

