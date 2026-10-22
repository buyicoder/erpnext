#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


HASHED_ASSET = re.compile(r"^(?P<logical>.+)\.[A-Z0-9_-]+\.(?P<extension>js|css)$")


def sync_manifest(asset_root: Path, manifest_path: Path) -> int:
	manifest = json.loads(manifest_path.read_text())
	updated = 0

	for logical_name, public_path in manifest.items():
		if not isinstance(public_path, str) or not public_path.startswith("/assets/"):
			continue
		relative_path = Path(public_path.removeprefix("/assets/"))
		match = HASHED_ASSET.match(relative_path.name)
		if not match:
			continue

		parent = asset_root / relative_path.parent
		candidates = sorted(
			path
			for path in parent.glob(f"{match.group('logical')}.*.{match.group('extension')}")
			if not path.name.endswith(".map")
		)
		if len(candidates) != 1:
			raise RuntimeError(
				f"Expected exactly one built asset for {logical_name}, found {len(candidates)}: "
				+ ", ".join(str(path) for path in candidates)
			)

		resolved_path = f"/assets/{candidates[0].relative_to(asset_root)}"
		if resolved_path != public_path:
			manifest[logical_name] = resolved_path
			updated += 1

	manifest_path.write_text(json.dumps(manifest, indent=4, sort_keys=True) + "\n")
	return updated


def main() -> None:
	parser = argparse.ArgumentParser(description="Synchronize Frappe's asset manifest with built bundles")
	parser.add_argument("--asset-root", type=Path, required=True)
	parser.add_argument("--manifest", type=Path, required=True)
	args = parser.parse_args()
	print(f"Synchronized {sync_manifest(args.asset_root, args.manifest)} asset manifest entries")


if __name__ == "__main__":
	main()
