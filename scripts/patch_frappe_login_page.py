#!/usr/bin/env python3
from pathlib import Path


RAW_LOGIN_TITLE = 'context["title"] = "Login"'
TRANSLATED_LOGIN_TITLE = 'context["title"] = _("Login")'


def patch_text(source: str) -> str:
	if source.count(RAW_LOGIN_TITLE) != 1:
		raise ValueError("Pinned Frappe login page no longer matches the expected source contract")
	return source.replace(RAW_LOGIN_TITLE, TRANSLATED_LOGIN_TITLE)


def main():
	login_path = Path("/home/frappe/frappe-bench/apps/frappe/frappe/www/login.py")
	login_path.write_text(patch_text(login_path.read_text()))


if __name__ == "__main__":
	main()
