#!/usr/bin/env python3
"""Validate translations against the exact Frappe public-JS sources in an image."""

import argparse
import re
import sys
from io import BytesIO
from pathlib import Path

from babel.messages.extract import extract_from_dir
from babel.messages.jslexer import unquote_string
from babel.messages.pofile import read_po


LITERAL_TRANSLATION_CALL = re.compile(r"\b__\(\s*(['\"])(?P<message>(?:\\.|(?!\1).)*)\1")


def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("--frappe-app", type=Path, required=True)
	parser.add_argument("--catalog", type=Path, required=True)
	return parser.parse_args()


def main():
	args = parse_args()
	sys.path.insert(0, str(args.frappe_app))

	from frappe.gettext.translate import PYTHON_KEYWORDS, get_method_map

	public_js = args.frappe_app / "frappe/public/js"

	def only_public_js(path):
		path = Path(path)
		return (
			path == args.frappe_app
			or path in public_js.parents
			or path == public_js
			or public_js in path.parents
		)

	runtime_messages = set()
	extracted_message_ids = set()
	for filename, _line, message, _comments, context in extract_from_dir(
		args.frappe_app,
		get_method_map("frappe"),
		directory_filter=only_public_js,
		keywords=PYTHON_KEYWORDS,
	):
		if filename.startswith("frappe/public/js/") and isinstance(message, str) and message:
			runtime_messages.add((message, context))
			extracted_message_ids.add(message)

	# Marker comments and nested calls intentionally skipped by Frappe's
	# extractor can still provide dynamic UI labels. Check their literal keys too.
	for path in public_js.rglob("*.js"):
		code = path.read_text(encoding="utf-8")
		for match in LITERAL_TRANSLATION_CALL.finditer(code):
			quoted_message = f"{match.group(1)}{match.group('message')}{match.group(1)}"
			message_id = unquote_string(quoted_message)
			if message_id not in extracted_message_ids:
				runtime_messages.add((message_id, None))

	catalog = read_po(BytesIO(args.catalog.read_bytes()), locale="zh")
	missing = []
	for message_id, context in sorted(runtime_messages, key=lambda item: (item[0], item[1] or "")):
		message = catalog.get(message_id, context=context)
		if not message or not message.string or "fuzzy" in message.flags or message.check():
			missing.append((message_id, context))

	if missing:
		for message_id, context in missing:
			print(f"missing runtime translation: {message_id!r} context={context!r}", file=sys.stderr)
		raise SystemExit(f"Frappe runtime public-JS translation coverage failed: {len(missing)} missing")

	print(f"Verified {len(runtime_messages)} runtime Frappe public-JS translations")


if __name__ == "__main__":
	main()
