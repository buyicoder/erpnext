#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
compose_dir="${COMPOSE_DIR:-$(cd "${repo_dir}/../erpnext-frappe-docker" && pwd)}"
project_name="${COMPOSE_PROJECT_NAME:-erpnext-cn}"
site_name="${SITE_NAME:-frontend}"

docker compose \
	-p "${project_name}" \
	-f "${compose_dir}/pwd.yml" \
	-f "${compose_dir}/compose.cn-image.yaml" \
	up -d --force-recreate

ready=0
for attempt in {1..30}; do
	if docker exec "${project_name}-backend-1" bash -lc \
		"cd /home/frappe/frappe-bench && timeout 5s bench --site '${site_name}' execute frappe.utils.now" \
		>/dev/null 2>&1; then
		ready=1
		break
	fi
	sleep 2
done

if [[ "${ready}" != 1 ]]; then
	printf 'Local ERPNext did not become ready for site %s. Inspect with: docker compose -p %s logs backend db redis-cache redis-queue\n' \
		"${site_name}" "${project_name}" >&2
	exit 1
fi

docker exec "${project_name}-backend-1" bash -lc \
	"cd /home/frappe/frappe-bench && \
	bench --site '${site_name}' migrate && \
	bench --site '${site_name}' execute erpnext.setup.china_defaults.apply_china_defaults && \
	bench --site '${site_name}' execute frappe.reload_doc --kwargs '{\"module\":\"accounts\",\"dt\":\"print_format\",\"dn\":\"pos_invoice_with_item_image\",\"force\":True}' && \
	bench --site '${site_name}' execute frappe.reload_doc --kwargs '{\"module\":\"accounts\",\"dt\":\"print_format\",\"dn\":\"sales_invoice_with_item_image\",\"force\":True}' && \
	bench --site '${site_name}' execute frappe.reload_doc --kwargs '{\"module\":\"accounts\",\"dt\":\"print_format\",\"dn\":\"cheque_printing_format\",\"force\":True}' && \
	bench --site '${site_name}' clear-cache"

printf 'Deployed %s, applied China defaults, migrated, and cleared translation cache for site %s\n' \
	"${project_name}" "${site_name}"
