from unittest import TestCase

from scripts.patch_frappe_desktop_page import (
	RAW_DESKTOP_TITLE,
	TRANSLATED_DESKTOP_TITLE,
	patch_text,
)


class TestPatchFrappeDesktopPage(TestCase):
	def test_desktop_page_title_uses_runtime_translation(self):
		patched = patch_text(f"before\n{RAW_DESKTOP_TITLE}\nafter")

		self.assertIn(TRANSLATED_DESKTOP_TITLE, patched)
		self.assertNotIn(RAW_DESKTOP_TITLE, patched)

	def test_patch_fails_when_pinned_source_changes(self):
		with self.assertRaisesRegex(ValueError, "no longer matches"):
			patch_text('title: "Desktop",')
