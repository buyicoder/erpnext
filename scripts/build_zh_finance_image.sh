#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(git -C "$script_dir/.." rev-parse --show-toplevel)"
image="${1:-buyicoder/erpnext-cn:v16.32.3-zh-finance}"
if [[ -n "$(git -C "$repo_root" status --porcelain --untracked-files=all)" ]]; then
	printf '%s\n' "Refusing to build from a dirty worktree; commit the release inputs first." >&2
	exit 1
fi
source_commit="$(git -C "$repo_root" rev-parse HEAD)"

"$repo_root/scripts/fetch_frappe_zh_baseline.sh"

docker build \
	--file "$repo_root/docker/zh-finance/Containerfile" \
	--build-arg "SOURCE_COMMIT=$source_commit" \
	--tag "$image" \
	"$repo_root"

docker run --rm --entrypoint sh "$image" -lc '
	set -eu
	/home/frappe/frappe-bench/env/bin/python - <<"PY"
import json
from pathlib import Path

asset_root = Path("/home/frappe/frappe-bench/assets")
manifest = json.loads((asset_root / "assets.json").read_text())
missing = [path for path in manifest.values() if isinstance(path, str) and path.startswith("/assets/") and not (asset_root / path.removeprefix("/assets/")).is_file()]
if missing:
	raise SystemExit("Asset manifest references missing files: " + ", ".join(missing))
print(f"Verified {len(manifest)} asset manifest entries")
PY
	grep -F "this.print_format_control.get_value()" /home/frappe/frappe-bench/apps/frappe/frappe/printing/page/print/print.js >/dev/null
	test -s /home/frappe/frappe-bench/assets/locale/zh/LC_MESSAGES/erpnext.mo
'

printf '%s\n' "Built $image from $source_commit"
