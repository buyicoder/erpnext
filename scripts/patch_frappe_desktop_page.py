#!/usr/bin/env python3
from pathlib import Path


RAW_DESKTOP_TITLE = '''		title: "Desktop",'''
TRANSLATED_DESKTOP_TITLE = '''		title: __("Desktop"),'''
RAW_SEARCH_TITLE = '''                    title="Search">'''
TRANSLATED_SEARCH_TITLE = '''                    title="{{ _("Search") |e }}">'''


def patch_text(source: str) -> str:
	if source.count(RAW_DESKTOP_TITLE) != 1:
		raise ValueError("Pinned Frappe desktop page no longer matches the expected source contract")
	return source.replace(RAW_DESKTOP_TITLE, TRANSLATED_DESKTOP_TITLE)


def patch_html(source: str) -> str:
	if source.count(RAW_SEARCH_TITLE) != 1:
		raise ValueError("Pinned Frappe desktop template no longer matches the expected source contract")
	return source.replace(RAW_SEARCH_TITLE, TRANSLATED_SEARCH_TITLE)


def main():
	page_path = Path(
		"/home/frappe/frappe-bench/apps/frappe/frappe/desk/page/desktop/desktop.js"
	)
	page_path.write_text(patch_text(page_path.read_text()))
	template_path = page_path.with_suffix(".html")
	template_path.write_text(patch_html(template_path.read_text()))


if __name__ == "__main__":
	main()
