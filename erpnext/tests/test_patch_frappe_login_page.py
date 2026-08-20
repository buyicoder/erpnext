from unittest import TestCase

from scripts.patch_frappe_login_page import (
	RAW_LOGIN_TITLE,
	TRANSLATED_LOGIN_TITLE,
	patch_text,
)


class TestPatchFrappeLoginPage(TestCase):
	def test_login_title_uses_runtime_translation(self):
		patched = patch_text(f"before\n{RAW_LOGIN_TITLE}\nafter\n")

		self.assertIn(TRANSLATED_LOGIN_TITLE, patched)
		self.assertNotIn(RAW_LOGIN_TITLE, patched)

	def test_pinned_source_contract_rejects_missing_or_duplicate_title(self):
		with self.assertRaises(ValueError):
			patch_text("context has changed")
		with self.assertRaises(ValueError):
			patch_text(f"{RAW_LOGIN_TITLE}\n{RAW_LOGIN_TITLE}")
