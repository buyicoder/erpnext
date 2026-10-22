#!/usr/bin/env python3
"""Merge reviewed Banking Chinese strings into the ERPNext catalog."""

import argparse
import json
from pathlib import Path

from babel.messages.pofile import read_po, write_po


LITERAL_PERCENT_MESSAGES = {
	"In this case, the amount will be calculated as 25% of the transaction amount. If the transaction amount is 200, then this will be calculated as 200 * 0.25 = 50."
}


def merge_banking_catalog(baseline_path: Path, translations_path: Path, output_path: Path):
	with baseline_path.open("rb") as source:
		catalog = read_po(source, locale="zh")
	translations = json.loads(translations_path.read_text())

	for source, translation in translations.items():
		message = catalog.get(source)
		if message is None:
			catalog.add(source, translation)
		else:
			message.string = translation
			message.flags.discard("fuzzy")
		if source in LITERAL_PERCENT_MESSAGES:
			message = catalog.get(source)
			message.flags.discard("python-format")
			message.flags.add("no-python-format")

	errors = {
		message.id: [str(error) for error in message.check()]
		for message in catalog
		if message.id in translations and message.check()
	}
	if errors:
		raise ValueError(f"Merged Banking translations are invalid: {errors}")

	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("wb") as destination:
		write_po(destination, catalog, width=0)
	print(f"Merged {len(translations)} reviewed Banking translations")


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--baseline", type=Path, required=True)
	parser.add_argument("--translations", type=Path, required=True)
	parser.add_argument("--output", type=Path, required=True)
	args = parser.parse_args()
	merge_banking_catalog(args.baseline, args.translations, args.output)


if __name__ == "__main__":
	main()
