#!/usr/bin/env python3
from pathlib import Path


RAW_LANGUAGE_DEFAULT = '\t\t\t\tdefault: "English",'
CHINA_LANGUAGE_DEFAULT = '\t\t\t\tdefault: "中文",'
RAW_SETUP_DATE_LANGUAGE = '\t\tlet lang = "en";\n\t\tfrappe.boot.user && (lang = frappe.boot.user.language);'
CHINA_SETUP_DATE_LANGUAGE = (
	'\t\tlet lang = document.documentElement.lang || frappe.boot.user?.language || "en";'
)


def patch_text(source: str) -> str:
	if source.count(RAW_LANGUAGE_DEFAULT) != 1:
		raise ValueError("Pinned Frappe setup wizard no longer matches the expected source contract")
	return source.replace(RAW_LANGUAGE_DEFAULT, CHINA_LANGUAGE_DEFAULT)


def patch_date_control_text(source: str) -> str:
	if source.count(RAW_SETUP_DATE_LANGUAGE) != 1:
		raise ValueError("Pinned Frappe date control no longer matches the expected source contract")
	return source.replace(RAW_SETUP_DATE_LANGUAGE, CHINA_SETUP_DATE_LANGUAGE)


def main():
	wizard_path = Path(
		"/home/frappe/frappe-bench/apps/frappe/frappe/desk/page/setup_wizard/setup_wizard.js"
	)
	wizard_path.write_text(patch_text(wizard_path.read_text()))
	date_control_path = Path(
		"/home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/form/controls/date.js"
	)
	date_control_path.write_text(patch_date_control_text(date_control_path.read_text()))


if __name__ == "__main__":
	main()
