#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
compose_dir="${COMPOSE_DIR:-$(cd "${repo_dir}/../erpnext-frappe-docker" && pwd)}"
project_name="${COMPOSE_PROJECT_NAME:-erpnext-cn}"
site_name="${SITE_NAME:-frontend}"
backend_container="${project_name}-backend-1"
backup_root="${BACKUP_ROOT:-${repo_dir}/.backups/pre-deploy}"

verify_backup_set() {
	local directory="$1"
	local pattern database config public_files private_files
	for pattern in "*-database*.sql.gz" "*-site_config_backup*.json" "*-files*.tgz" "*-private-files*.tgz"; do
		if ! find "${directory}" -maxdepth 1 -type f -name "${pattern}" -size +0c -print -quit | grep -q .; then
			printf 'Required backup artifact %s is missing or empty in %s\n' "${pattern}" "${directory}" >&2
			return 1
		fi
	done

	database="$(find "${directory}" -maxdepth 1 -type f -name '*-database*.sql.gz' -print -quit)"
	config="$(find "${directory}" -maxdepth 1 -type f -name '*-site_config_backup*.json' -print -quit)"
	public_files="$(find "${directory}" -maxdepth 1 -type f -name '*-files*.tgz' ! -name '*-private-files*.tgz' -print -quit)"
	private_files="$(find "${directory}" -maxdepth 1 -type f -name '*-private-files*.tgz' -print -quit)"
	gzip -t "${database}"
	tar -tzf "${public_files}" >/dev/null
	tar -tzf "${private_files}" >/dev/null
	python3 -m json.tool "${config}" >/dev/null
}

backup_existing_site() {
	local sites_volume="${project_name}_sites"
	if ! docker inspect "${backend_container}" >/dev/null 2>&1; then
		if docker volume inspect "${sites_volume}" >/dev/null 2>&1; then
			printf 'Refusing deployment: sites volume %s exists but backend container %s is unavailable for a verified backup.\n' \
				"${sites_volume}" "${backend_container}" >&2
			exit 1
		fi
		return
	fi

	if [[ "$(docker inspect -f '{{.State.Running}}' "${backend_container}")" != "true" ]]; then
		printf 'Refusing deployment: backend container %s is not running, so the existing site cannot be backed up safely.\n' \
			"${backend_container}" >&2
		exit 1
	fi

	if ! docker exec "${backend_container}" bash -lc \
		"cd /home/frappe/frappe-bench && timeout 10s bench --site '${site_name}' execute frappe.utils.now" \
		>/dev/null 2>&1; then
		printf 'Refusing deployment: existing site %s is not ready for backup.\n' "${site_name}" >&2
		exit 1
	fi

	local timestamp remote_dir host_dir
	timestamp="$(date -u +%Y%m%d_%H%M%S)"
	remote_dir="/home/frappe/frappe-bench/sites/.pre-deploy-backups/${site_name}/${timestamp}"
	host_dir="${backup_root}/${site_name}/${timestamp}"
	mkdir -p "${host_dir}"

	docker exec "${backend_container}" bash -lc \
		"cd /home/frappe/frappe-bench && bench --site '${site_name}' backup --with-files --compress --backup-path '${remote_dir}'"
	docker exec "${backend_container}" bash -lc \
		"for pattern in '*-database*.sql.gz' '*-site_config_backup*.json' '*-files*.tgz' '*-private-files*.tgz'; do find '${remote_dir}' -maxdepth 1 -type f -name \"\${pattern}\" -size +0c -print -quit | grep -q . || exit 1; done"
	docker cp "${backend_container}:${remote_dir}/." "${host_dir}/"
	chmod -R go-rwx "${host_dir}"
	verify_backup_set "${host_dir}"
	printf 'Verified pre-deploy backup for site %s at %s\n' "${site_name}" "${host_dir}"
}

backup_existing_site

if [[ "${BACKUP_ONLY:-0}" == "1" ]]; then
	exit 0
fi

docker compose \
	-p "${project_name}" \
	-f "${compose_dir}/pwd.yml" \
	-f "${compose_dir}/compose.cn-image.yaml" \
	up -d --force-recreate

ready=0
for attempt in {1..30}; do
	if docker exec "${backend_container}" bash -lc \
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

docker exec "${backend_container}" bash -lc \
	"cd /home/frappe/frappe-bench && \
	bench --site '${site_name}' migrate && \
	bench --site '${site_name}' execute erpnext.setup.china_defaults.localize_bundled_demo_data && \
	bench --site '${site_name}' execute erpnext.setup.china_defaults.apply_china_defaults --kwargs '{\"clear_cache\":False}' && \
	bench --site '${site_name}' execute frappe.reload_doc --kwargs '{\"module\":\"accounts\",\"dt\":\"print_format\",\"dn\":\"pos_invoice_with_item_image\",\"force\":True}' && \
	bench --site '${site_name}' execute frappe.reload_doc --kwargs '{\"module\":\"accounts\",\"dt\":\"print_format\",\"dn\":\"sales_invoice_with_item_image\",\"force\":True}' && \
	bench --site '${site_name}' execute frappe.reload_doc --kwargs '{\"module\":\"accounts\",\"dt\":\"print_format\",\"dn\":\"cheque_printing_format\",\"force\":True}' && \
	bench --site '${site_name}' execute frappe.reload_doc --kwargs '{\"module\":\"accounts\",\"dt\":\"print_format\",\"dn\":\"purchase_auditing_voucher\",\"force\":True}' && \
	bench --site '${site_name}' execute frappe.reload_doc --kwargs '{\"module\":\"accounts\",\"dt\":\"print_format\",\"dn\":\"sales_auditing_voucher\",\"force\":True}' && \
	bench --site '${site_name}' execute frappe.reload_doc --kwargs '{\"module\":\"accounts\",\"dt\":\"print_format\",\"dn\":\"bank_and_cash_payment_voucher\",\"force\":True}' && \
	bench --site '${site_name}' execute frappe.reload_doc --kwargs '{\"module\":\"accounts\",\"dt\":\"print_format\",\"dn\":\"journal_auditing_voucher\",\"force\":True}' && \
	bench --site '${site_name}' execute frappe.reload_doc --kwargs '{\"module\":\"accounts\",\"dt\":\"letter_head\",\"dn\":\"company_letterhead___grey\",\"force\":True}' && \
	bench --site '${site_name}' execute frappe.reload_doc --kwargs '{\"module\":\"accounts\",\"dt\":\"notification\",\"dn\":\"notification_for_new_fiscal_year\",\"force\":True}' && \
	bench --site '${site_name}' clear-cache"

printf 'Deployed %s, applied China defaults, migrated, and cleared translation cache for site %s\n' \
	"${project_name}" "${site_name}"
