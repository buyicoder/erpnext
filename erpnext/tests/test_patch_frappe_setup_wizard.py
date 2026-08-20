from unittest import TestCase

from scripts.patch_frappe_setup_wizard import (
	CHINA_LANGUAGE_DEFAULT,
	RAW_LANGUAGE_DEFAULT,
	patch_text,
)


class TestPatchFrappeSetupWizard(TestCase):
	def test_china_image_starts_setup_in_chinese(self):
		patched = patch_text(f"before\n{RAW_LANGUAGE_DEFAULT}\nafter\n")

		self.assertIn(CHINA_LANGUAGE_DEFAULT, patched)
		self.assertNotIn(RAW_LANGUAGE_DEFAULT, patched)

	def test_pinned_source_contract_rejects_missing_or_duplicate_default(self):
		with self.assertRaises(ValueError):
			patch_text("setup wizard changed")
		with self.assertRaises(ValueError):
			patch_text(f"{RAW_LANGUAGE_DEFAULT}\n{RAW_LANGUAGE_DEFAULT}")
