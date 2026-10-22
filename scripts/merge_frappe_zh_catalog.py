#!/usr/bin/env python3
"""Merge reviewed Chinese overrides onto a pinned official Frappe catalog."""

import argparse
from pathlib import Path

from babel.messages.pofile import read_po, write_po


KNOWN_INCORRECT_FORMAT_FLAGS = {"Use % for any non empty value."}


def load_catalog(path: Path):
	with path.open("rb") as source:
		return read_po(source, locale="zh")


def merge_catalogs(baseline_path: Path, overrides_path: Path, output_path: Path):
	baseline = load_catalog(baseline_path)
	overrides = load_catalog(overrides_path)

	for override in overrides:
		if not override.id:
			continue
		existing = baseline.get(override.id, context=override.context)
		if existing is None:
			baseline.add(
				override.id,
				override.string,
				context=override.context,
				flags=override.flags,
			)
		else:
			existing.string = override.string

	for message_id in KNOWN_INCORRECT_FORMAT_FLAGS:
		message = baseline.get(message_id)
		if message:
			message.flags.discard("python-format")

	errors = {
		message.id: [str(error) for error in message.check()]
		for message in baseline
		if message.id and message.check()
	}
	if errors:
		raise ValueError(f"Merged Frappe zh catalog is invalid: {errors}")

	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("wb") as destination:
		write_po(destination, baseline, width=0)

	translated = sum(1 for message in baseline if message.id and message.string)
	print(f"Merged Frappe zh catalog: {translated} translated messages")


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--baseline", type=Path, required=True)
	parser.add_argument("--overrides", type=Path, required=True)
	parser.add_argument("--output", type=Path, required=True)
	args = parser.parse_args()
	merge_catalogs(args.baseline, args.overrides, args.output)


if __name__ == "__main__":
	main()
