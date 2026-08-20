from unittest import TestCase

from scripts.patch_frappe_desktop_page import (
	RAW_DESKTOP_TITLE,
	RAW_FORM_SIDEBAR_TITLE,
	RAW_SEARCH_TITLE,
	RAW_STANDARD_SIDEBAR_LABEL,
	RAW_STANDARD_SIDEBAR_TOOLTIP,
	RAW_WORKSPACE_DEPENDENCIES,
	RAW_TREE_ROOT_LABEL,
	TRANSLATED_DESKTOP_TITLE,
	TRANSLATED_FORM_SIDEBAR_TITLE,
	TRANSLATED_SEARCH_TITLE,
	TRANSLATED_STANDARD_SIDEBAR_LABEL,
	TRANSLATED_STANDARD_SIDEBAR_TOOLTIP,
	TRANSLATED_WORKSPACE_DEPENDENCIES,
	TRANSLATED_TREE_ROOT_LABEL,
	patch_html,
	patch_form_sidebar,
	patch_links_widget,
	patch_sidebar_item,
	patch_treeview,
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

	def test_tree_root_label_uses_runtime_translation_without_changing_its_value(self):
		patched = patch_treeview(f"before\n{RAW_TREE_ROOT_LABEL}\nafter")

		self.assertIn(TRANSLATED_TREE_ROOT_LABEL, patched)
		self.assertNotIn(RAW_TREE_ROOT_LABEL, patched)

	def test_tree_root_label_patch_fails_when_pinned_source_changes(self):
		with self.assertRaisesRegex(ValueError, "no longer matches"):
			patch_treeview("label: use_label,")

	def test_single_doctype_sidebar_title_uses_runtime_translation(self):
		patched = patch_form_sidebar(f"before\n{RAW_FORM_SIDEBAR_TITLE}\nafter")

		self.assertIn(TRANSLATED_FORM_SIDEBAR_TITLE, patched)
		self.assertIn("frm.meta.issingle ? __(", patched)
		self.assertNotIn(RAW_FORM_SIDEBAR_TITLE, patched)

	def test_form_sidebar_patch_fails_when_pinned_source_changes(self):
		with self.assertRaisesRegex(ValueError, "no longer matches"):
			patch_form_sidebar("<span>{%= title %}</span>")

	def test_standard_sidebar_labels_translate_without_changing_custom_labels(self):
		source = "\n".join(
			[
				RAW_STANDARD_SIDEBAR_TOOLTIP,
				RAW_STANDARD_SIDEBAR_LABEL,
				RAW_STANDARD_SIDEBAR_LABEL,
			]
		)

		patched = patch_sidebar_item(source)

		self.assertIn(TRANSLATED_STANDARD_SIDEBAR_TOOLTIP, patched)
		self.assertEqual(patched.count(TRANSLATED_STANDARD_SIDEBAR_LABEL), 2)
		self.assertIn("item.standard ? __(item.label) : item.label", patched)

	def test_sidebar_item_patch_fails_when_pinned_source_changes(self):
		with self.assertRaisesRegex(ValueError, "no longer matches"):
			patch_sidebar_item(RAW_STANDARD_SIDEBAR_LABEL)
