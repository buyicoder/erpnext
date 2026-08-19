from unittest import TestCase

from scripts.patch_frappe_print_page import (
	DEFAULT_FORMAT,
	SELECTED_FORMAT,
	SELECTOR_SETUP,
	patch_text,
)


class TestPatchFrappePrintPage(TestCase):
	def test_default_format_uses_link_control_translation_path(self):
		patched = patch_text(f"{SELECTOR_SETUP}\n{DEFAULT_FORMAT}\n{SELECTED_FORMAT}")

		self.assertIn("this.print_format_control = this.add_sidebar_item", patched)
		self.assertIn("this.print_format_selector = this.print_format_control.$input", patched)
		self.assertIn("return this.print_format_control.set_value(selected_format)", patched)
		self.assertIn(
			'return this.print_format_control.set_value(this.frm.meta.default_print_format || "")',
			patched,
		)
		self.assertNotIn("this.print_format_selector.val(this.frm.meta.default_print_format", patched)
		self.assertIn('return this.print_format_control.get_value() || "Standard"', patched)

	def test_patch_fails_when_pinned_source_changes(self):
		with self.assertRaisesRegex(ValueError, "no longer matches"):
			patch_text("unexpected upstream source")
