from unittest import TestCase

from scripts.patch_frappe_desktop_page import (
	RAW_DESKTOP_TITLE,
	RAW_SEARCH_TITLE,
	RAW_WORKSPACE_DEPENDENCIES,
	TRANSLATED_DESKTOP_TITLE,
	TRANSLATED_SEARCH_TITLE,
	TRANSLATED_WORKSPACE_DEPENDENCIES,
	patch_html,
	patch_links_widget,
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

	def test_search_tooltip_uses_server_translation(self):
		patched = patch_html(f"before\n{RAW_SEARCH_TITLE}\nafter")

		self.assertIn(TRANSLATED_SEARCH_TITLE, patched)
		self.assertNotIn(RAW_SEARCH_TITLE, patched)

	def test_template_patch_fails_when_pinned_source_changes(self):
		with self.assertRaisesRegex(ValueError, "no longer matches"):
			patch_html('title="Search"')

	def test_workspace_dependencies_use_runtime_doctype_translations(self):
		patched = patch_links_widget(f"before\n{RAW_WORKSPACE_DEPENDENCIES}\nafter")

		self.assertIn(TRANSLATED_WORKSPACE_DEPENDENCIES, patched)
		self.assertNotIn(RAW_WORKSPACE_DEPENDENCIES, patched)

	def test_workspace_dependency_patch_fails_when_pinned_source_changes(self):
		with self.assertRaisesRegex(ValueError, "no longer matches"):
			patch_links_widget('${item.incomplete_dependencies.join(", ")}')
