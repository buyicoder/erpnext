#!/usr/bin/env python3
from pathlib import Path


RAW_DESKTOP_TITLE = '''		title: "Desktop",'''
TRANSLATED_DESKTOP_TITLE = '''		title: __("Desktop"),'''
RAW_SEARCH_TITLE = '''                    title="Search">'''
TRANSLATED_SEARCH_TITLE = '''                    title="{{ _("Search") |e }}">'''
RAW_WORKSPACE_DEPENDENCIES = '''<div class="small">${item.incomplete_dependencies.join(", ")}</div>'''
TRANSLATED_WORKSPACE_DEPENDENCIES = '''<div class="small">${item.incomplete_dependencies.map((doctype) => __(doctype)).join(", ")}</div>'''
RAW_TREE_ROOT_LABEL = '''\t\t\tlabel: use_label,'''
TRANSLATED_TREE_ROOT_LABEL = '''\t\t\tlabel: __(use_label),'''
RAW_FORM_SIDEBAR_TITLE = '''\t\t\t\t<span class="bold ellipsis mr-3 text-medium">{%= frappe.utils.escape_html(frappe.utils.html2text(title)) %}</span>'''
TRANSLATED_FORM_SIDEBAR_TITLE = '''\t\t\t\t<span class="bold ellipsis mr-3 text-medium">{%= frappe.utils.escape_html(frm.meta.issingle ? __(frappe.utils.html2text(title)) : frappe.utils.html2text(title)) %}</span>'''
RAW_STANDARD_SIDEBAR_TOOLTIP = '''    title="{{ item.label }}"'''
TRANSLATED_STANDARD_SIDEBAR_TOOLTIP = '''    title="{{ item.standard ? __(item.label) : item.label }}"'''
RAW_STANDARD_SIDEBAR_LABEL = '''<span class="sidebar-item-label">{{ item.label }}</span>'''
TRANSLATED_STANDARD_SIDEBAR_LABEL = '''<span class="sidebar-item-label">{{ item.standard ? __(item.label) : item.label }}</span>'''


def patch_text(source: str) -> str:
	if source.count(RAW_DESKTOP_TITLE) != 1:
		raise ValueError("Pinned Frappe desktop page no longer matches the expected source contract")
	return source.replace(RAW_DESKTOP_TITLE, TRANSLATED_DESKTOP_TITLE)


def patch_html(source: str) -> str:
	if source.count(RAW_SEARCH_TITLE) != 1:
		raise ValueError("Pinned Frappe desktop template no longer matches the expected source contract")
	return source.replace(RAW_SEARCH_TITLE, TRANSLATED_SEARCH_TITLE)


def patch_links_widget(source: str) -> str:
	if source.count(RAW_WORKSPACE_DEPENDENCIES) != 1:
		raise ValueError("Pinned Frappe links widget no longer matches the expected source contract")
	return source.replace(RAW_WORKSPACE_DEPENDENCIES, TRANSLATED_WORKSPACE_DEPENDENCIES)


def patch_treeview(source: str) -> str:
	if source.count(RAW_TREE_ROOT_LABEL) != 1:
		raise ValueError("Pinned Frappe tree view no longer matches the expected source contract")
	return source.replace(RAW_TREE_ROOT_LABEL, TRANSLATED_TREE_ROOT_LABEL)


def patch_form_sidebar(source: str) -> str:
	if source.count(RAW_FORM_SIDEBAR_TITLE) != 1:
		raise ValueError("Pinned Frappe form sidebar no longer matches the expected source contract")
	return source.replace(RAW_FORM_SIDEBAR_TITLE, TRANSLATED_FORM_SIDEBAR_TITLE)


def patch_sidebar_item(source: str) -> str:
	if source.count(RAW_STANDARD_SIDEBAR_TOOLTIP) != 1:
		raise ValueError("Pinned Frappe sidebar item tooltip no longer matches the expected source contract")
	if source.count(RAW_STANDARD_SIDEBAR_LABEL) != 2:
		raise ValueError("Pinned Frappe sidebar item labels no longer match the expected source contract")
	return source.replace(
		RAW_STANDARD_SIDEBAR_TOOLTIP, TRANSLATED_STANDARD_SIDEBAR_TOOLTIP
	).replace(RAW_STANDARD_SIDEBAR_LABEL, TRANSLATED_STANDARD_SIDEBAR_LABEL)


def main():
	page_path = Path(
		"/home/frappe/frappe-bench/apps/frappe/frappe/desk/page/desktop/desktop.js"
	)
	page_path.write_text(patch_text(page_path.read_text()))
	template_path = page_path.with_suffix(".html")
	template_path.write_text(patch_html(template_path.read_text()))
	links_widget_path = Path(
		"/home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/widgets/links_widget.js"
	)
	links_widget_path.write_text(patch_links_widget(links_widget_path.read_text()))
	treeview_path = Path(
		"/home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/views/treeview.js"
	)
	treeview_path.write_text(patch_treeview(treeview_path.read_text()))
	form_sidebar_path = Path(
		"/home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/form/templates/form_sidebar.html"
	)
	form_sidebar_path.write_text(patch_form_sidebar(form_sidebar_path.read_text()))
	sidebar_item_path = Path(
		"/home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/ui/sidebar/sidebar_item.html"
	)
	sidebar_item_path.write_text(patch_sidebar_item(sidebar_item_path.read_text()))


if __name__ == "__main__":
	main()
