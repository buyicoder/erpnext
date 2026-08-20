#!/usr/bin/env python3
import argparse
from pathlib import Path


RAW_LANGUAGE_DEFAULT = '\t\t\t\tdefault: "English",'
CHINA_LANGUAGE_DEFAULT = '\t\t\t\tdefault: "中文",'
RAW_SETUP_DATE_LANGUAGE = '\t\tlet lang = "en";\n\t\tfrappe.boot.user && (lang = frappe.boot.user.language);'
CHINA_SETUP_DATE_LANGUAGE = (
	'\t\tlet lang = document.documentElement.lang || frappe.boot.user?.language || "en";'
)
RAW_BUILT_DATE_LANGUAGE = 'let e="en";frappe.boot.user&&(e=frappe.boot.user.language),'
CHINA_BUILT_DATE_LANGUAGE = (
	'let e=document.documentElement.lang||frappe.boot.user?.language||"en";'
)


def patch_text(source: str) -> str:
	if source.count(RAW_LANGUAGE_DEFAULT) != 1:
		raise ValueError("Pinned Frappe setup wizard no longer matches the expected source contract")
	return source.replace(RAW_LANGUAGE_DEFAULT, CHINA_LANGUAGE_DEFAULT)


def patch_date_control_text(source: str) -> str:
	if source.count(RAW_SETUP_DATE_LANGUAGE) != 1:
		raise ValueError("Pinned Frappe date control no longer matches the expected source contract")
	return source.replace(RAW_SETUP_DATE_LANGUAGE, CHINA_SETUP_DATE_LANGUAGE)


def patch_built_date_control_text(source: str) -> str:
	if source.count(RAW_BUILT_DATE_LANGUAGE) != 1:
		raise ValueError("Built Frappe date control no longer matches the expected asset contract")
	return source.replace(RAW_BUILT_DATE_LANGUAGE, CHINA_BUILT_DATE_LANGUAGE)


def patch_built_assets(asset_root: Path) -> None:
	bundles = list(asset_root.glob("controls.bundle.*.js"))
	if len(bundles) != 1:
		raise ValueError(f"Expected exactly one built controls bundle, found {len(bundles)}")
	bundle = bundles[0]
	bundle.write_text(patch_built_date_control_text(bundle.read_text()))


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--built-assets", action="store_true")
	args = parser.parse_args()
	if args.built_assets:
		patch_built_assets(Path("/home/frappe/frappe-bench/assets/frappe/dist/js"))
		return

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
