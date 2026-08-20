from unittest import TestCase

from scripts.patch_frappe_setup_wizard import (
	CHINA_LANGUAGE_DEFAULT,
	CHINA_BUILT_DATE_LANGUAGE,
	CHINA_SETUP_DATE_LANGUAGE,
	CHINA_LANGUAGE_INITIALIZATION,
	CHINA_LANGUAGE_BINDING_ORDER,
	CHINA_LANGUAGE_CURRENT_SELECTION,
	RAW_BUILT_DATE_LANGUAGE,
	RAW_LANGUAGE_DEFAULT,
	RAW_LANGUAGE_INITIALIZATION,
	RAW_LANGUAGE_BINDING_ORDER,
	RAW_LANGUAGE_CURRENT_SELECTION,
	RAW_SETUP_DATE_LANGUAGE,
	patch_built_date_control_text,
	patch_date_control_text,
	patch_text,
)


class TestPatchFrappeSetupWizard(TestCase):
	def test_china_image_starts_setup_in_chinese(self):
		patched = patch_text(
			f"before\n{RAW_LANGUAGE_DEFAULT}\n{RAW_LANGUAGE_INITIALIZATION}\n"
			f"{RAW_LANGUAGE_CURRENT_SELECTION}\n{RAW_LANGUAGE_BINDING_ORDER}\nafter\n"
		)

		self.assertIn(CHINA_LANGUAGE_DEFAULT, patched)
		self.assertNotIn(RAW_LANGUAGE_DEFAULT, patched)
		self.assertIn(CHINA_LANGUAGE_INITIALIZATION, patched)
		self.assertNotIn(RAW_LANGUAGE_INITIALIZATION, patched)
		self.assertIn(CHINA_LANGUAGE_CURRENT_SELECTION, patched)
		self.assertIn(CHINA_LANGUAGE_BINDING_ORDER, patched)
		self.assertNotIn(RAW_LANGUAGE_BINDING_ORDER, patched)

	def test_setup_date_picker_uses_chinese_system_default_before_user_setup(self):
		patched = patch_date_control_text(f"before\n{RAW_SETUP_DATE_LANGUAGE}\nafter\n")

		self.assertIn(CHINA_SETUP_DATE_LANGUAGE, patched)
		self.assertNotIn(RAW_SETUP_DATE_LANGUAGE, patched)

	def test_built_date_picker_uses_document_language_after_frappe_build(self):
		patched = patch_built_date_control_text(f"before{RAW_BUILT_DATE_LANGUAGE}after")

		self.assertIn(CHINA_BUILT_DATE_LANGUAGE, patched)
		self.assertNotIn(RAW_BUILT_DATE_LANGUAGE, patched)

	def test_pinned_source_contract_rejects_missing_or_duplicate_default(self):
		with self.assertRaises(ValueError):
			patch_text(f"{RAW_LANGUAGE_INITIALIZATION}\nsetup wizard changed")
		with self.assertRaises(ValueError):
			patch_text(
				f"{RAW_LANGUAGE_DEFAULT}\n{RAW_LANGUAGE_DEFAULT}\n{RAW_LANGUAGE_INITIALIZATION}\n"
				f"{RAW_LANGUAGE_CURRENT_SELECTION}\n{RAW_LANGUAGE_BINDING_ORDER}"
			)
