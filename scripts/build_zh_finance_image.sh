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
	expected_bundle="$(basename "$(find /home/frappe/frappe-bench/assets/erpnext/dist/js -name "erpnext.bundle.*.js" -type f | head -1)")"
	expected_css_bundle="$(basename "$(find /home/frappe/frappe-bench/assets/erpnext/dist/css -name "erpnext.bundle.*.css" -type f | head -1)")"
	expected_desk_bundle="$(basename "$(find /home/frappe/frappe-bench/assets/frappe/dist/js -name "desk.bundle.*.js" -type f | head -1)")"
	grep -F "erpnext/dist/js/${expected_bundle}" /home/frappe/frappe-bench/assets/assets.json >/dev/null
	grep -F "erpnext/dist/css/${expected_css_bundle}" /home/frappe/frappe-bench/assets/assets.json >/dev/null
	grep -F "frappe/dist/js/${expected_desk_bundle}" /home/frappe/frappe-bench/assets/assets.json >/dev/null
	grep -F "this.print_format_control.get_value()" /home/frappe/frappe-bench/apps/frappe/frappe/printing/page/print/print.js >/dev/null
	test -s /home/frappe/frappe-bench/assets/locale/zh/LC_MESSAGES/erpnext.mo
'

printf '%s\n' "Built $image from $source_commit"
