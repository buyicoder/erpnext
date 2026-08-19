#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(git -C "$script_dir/.." rev-parse --show-toplevel)"
output="$repo_root/.build/frappe-v16.24.4-zh.po"
expected_sha="b0d107adf4e064622b03aefed46e5d3a06c6daae05cca0a4d5d07fb1e5fef586"
source_url="https://raw.githubusercontent.com/frappe/frappe/v16.24.4/frappe/locale/zh.po"

mkdir -p "$(dirname "$output")"

if [[ -f "$output" ]] && [[ "$(shasum -a 256 "$output" | awk '{print $1}')" == "$expected_sha" ]]; then
	printf '%s\n' "Using verified Frappe zh baseline: $output"
	exit 0
fi

temporary="${output}.tmp"
trap 'rm -f "$temporary"' EXIT
curl --fail --location --silent --show-error "$source_url" --output "$temporary"
actual_sha="$(shasum -a 256 "$temporary" | awk '{print $1}')"
if [[ "$actual_sha" != "$expected_sha" ]]; then
	printf 'Frappe zh baseline checksum mismatch: expected %s, got %s\n' "$expected_sha" "$actual_sha" >&2
	exit 1
fi

mv "$temporary" "$output"
printf '%s\n' "Downloaded verified Frappe zh baseline: $output"
