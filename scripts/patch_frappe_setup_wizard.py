#!/usr/bin/env python3
from pathlib import Path


RAW_LANGUAGE_DEFAULT = '\t\t\t\tdefault: "English",'
CHINA_LANGUAGE_DEFAULT = '\t\t\t\tdefault: "中文",'


def patch_text(source: str) -> str:
	if source.count(RAW_LANGUAGE_DEFAULT) != 1:
		raise ValueError("Pinned Frappe setup wizard no longer matches the expected source contract")
	return source.replace(RAW_LANGUAGE_DEFAULT, CHINA_LANGUAGE_DEFAULT)


def main():
	wizard_path = Path(
		"/home/frappe/frappe-bench/apps/frappe/frappe/desk/page/setup_wizard/setup_wizard.js"
	)
	wizard_path.write_text(patch_text(wizard_path.read_text()))


if __name__ == "__main__":
	main()
