#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(git -C "$script_dir/.." rev-parse --show-toplevel)"
source "$script_dir/frappe_zh_baseline.conf"
translation_output="$repo_root/.build/frappe-v${FRAPPE_ZH_BASELINE_VERSION}-zh.po"
runtime_pot_output="$repo_root/.build/frappe-v${FRAPPE_RUNTIME_VERSION}-main.pot"

mkdir -p "$repo_root/.build"

fetch_verified() {
	local source_url="$1"
	local output="$2"
	local expected_sha="$3"
	local label="$4"

	if [[ -f "$output" ]] && [[ "$(shasum -a 256 "$output" | awk '{print $1}')" == "$expected_sha" ]]; then
		printf '%s\n' "Using verified $label: $output"
		return
	fi

	local temporary="${output}.tmp"
	curl --fail --location --silent --show-error "$source_url" --output "$temporary"
	local actual_sha
	actual_sha="$(shasum -a 256 "$temporary" | awk '{print $1}')"
	if [[ "$actual_sha" != "$expected_sha" ]]; then
		printf '%s checksum mismatch: expected %s, got %s\n' "$label" "$expected_sha" "$actual_sha" >&2
		return 1
	fi
	mv "$temporary" "$output"
	printf '%s\n' "Downloaded verified $label: $output"
}

fetch_verified \
	"https://raw.githubusercontent.com/frappe/frappe/v${FRAPPE_ZH_BASELINE_VERSION}/frappe/locale/zh.po" \
	"$translation_output" \
	"$FRAPPE_ZH_BASELINE_SHA256" \
	"Frappe zh baseline"
fetch_verified \
	"https://raw.githubusercontent.com/frappe/frappe/v${FRAPPE_RUNTIME_VERSION}/frappe/locale/main.pot" \
	"$runtime_pot_output" \
	"$FRAPPE_RUNTIME_POT_SHA256" \
	"Frappe runtime source catalog"
