#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(git -C "$script_dir/.." rev-parse --show-toplevel)"
image="${1:-buyicoder/erpnext-cn:v16.32.3-zh-finance}"
source_commit="$(git -C "$repo_root" rev-parse HEAD)"

"$repo_root/scripts/fetch_frappe_zh_baseline.sh"

docker build \
	--file "$repo_root/docker/zh-finance/Containerfile" \
	--build-arg "SOURCE_COMMIT=$source_commit" \
	--tag "$image" \
	"$repo_root"

docker run --rm --entrypoint sh "$image" -lc '
	set -eu
	expected_bundle="$(basename "$(find /home/frappe/frappe-bench/assets/erpnext/dist/js -name "erpnext.bundle.*.js" -type f | head -1)")"
	grep -F "erpnext/dist/js/${expected_bundle}" /home/frappe/frappe-bench/assets/assets.json >/dev/null
	test -s /home/frappe/frappe-bench/assets/locale/zh/LC_MESSAGES/erpnext.mo
'

printf '%s\n' "Built $image from $source_commit"
