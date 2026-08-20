#!/usr/bin/env python3
from pathlib import Path


RAW_DESKTOP_TITLE = '''		title: "Desktop",'''
TRANSLATED_DESKTOP_TITLE = '''		title: __("Desktop"),'''


def patch_text(source: str) -> str:
	if source.count(RAW_DESKTOP_TITLE) != 1:
		raise ValueError("Pinned Frappe desktop page no longer matches the expected source contract")
	return source.replace(RAW_DESKTOP_TITLE, TRANSLATED_DESKTOP_TITLE)


def main():
	path = Path(
		"/home/frappe/frappe-bench/apps/frappe/frappe/desk/page/desktop/desktop.js"
	)
	path.write_text(patch_text(path.read_text()))


if __name__ == "__main__":
	main()
