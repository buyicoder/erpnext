import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from scripts.sync_asset_manifest import sync_manifest


class TestZhFinanceImage(TestCase):
	def setUp(self):
		self.repo_root = Path(__file__).parents[2]
		self.containerfile = (
			self.repo_root / "docker" / "zh-finance" / "Containerfile"
		).read_text()
		self.deploy_script = (self.repo_root / "scripts" / "deploy_local_zh_finance.sh").read_text()
		self.build_script = (self.repo_root / "scripts" / "build_zh_finance_image.sh").read_text()
		self.fetch_script = (
			self.repo_root / "scripts" / "fetch_frappe_zh_baseline.sh"
		).read_text()
		self.baseline_config = (
			self.repo_root / "scripts" / "frappe_zh_baseline.conf"
		).read_text()
		self.runtime_i18n_validator = (
			self.repo_root / "scripts" / "validate_frappe_runtime_i18n.py"
		).read_text()
		self.patches = (self.repo_root / "erpnext" / "patches.txt").read_text()
		self.localization_readme = (self.repo_root / "localization" / "README.md").read_text()
		self.browser_overrides = (
			self.repo_root / "erpnext" / "public" / "js" / "zh_finance_overrides.js"
		).read_text()
		self.account_tree = (
			self.repo_root / "erpnext" / "accounts" / "doctype" / "account" / "account_tree.js"
		).read_text()

	def test_final_image_verifier_uses_literal_heredoc_input(self):
		self.assertIn('--env "FRAPPE_RUNTIME_VERSION=$FRAPPE_RUNTIME_VERSION"', self.build_script)
		self.assertIn('"$image" -s <<\'VERIFY_SCRIPT\'', self.build_script)
		self.assertIn("/home/frappe/frappe-bench/env/bin/python - <<'PY'", self.build_script)
		self.assertIn("\nVERIFY_SCRIPT\n", self.build_script)
		self.assertNotIn('"$image" -lc \'', self.build_script)

	def test_image_compiles_translations_and_frontend_assets(self):
		self.assertIn("bench compile-po-to-mo --app erpnext --locale zh --force", self.containerfile)
		self.assertIn("bench compile-po-to-mo --app frappe --locale zh --force", self.containerfile)
		self.assertIn("bench build --app frappe", self.containerfile)
		self.assertIn("bench build --app erpnext", self.containerfile)
		self.assertIn("erpnext/public/js/zh_finance_format.mjs", self.containerfile)
		self.assertIn("erpnext/tests/zh_finance_format.test.mjs", self.containerfile)
		self.assertIn("node --test /workspace/erpnext/tests/zh_finance_format.test.mjs", self.containerfile)
		self.assertIn("erpnext/public/js/zh_audit_list.js", self.containerfile)
		self.assertIn("erpnext/public/js/controllers/transaction.js", self.containerfile)
		self.assertIn("erpnext/public/scss/modern-cn-theme.scss", self.containerfile)
		self.assertIn("erpnext/public/scss/erpnext.bundle.scss", self.containerfile)
		self.assertIn("erpnext/accounts/doctype/account/account_tree.js", self.containerfile)
		self.assertIn(
			"erpnext/accounts/doctype/financial_report_template/financial_report_validation.py",
			self.containerfile,
		)
		self.assertIn("erpnext/projects/doctype/project/project.py", self.containerfile)
		self.assertIn("erpnext/projects/doctype/project/project_dashboard.html", self.containerfile)
		self.assertIn("erpnext/manufacturing/doctype/work_order/work_order_preview.html", self.containerfile)
		self.assertIn("erpnext/stock/dashboard/item_dashboard.html", self.containerfile)
		self.assertIn(
			"erpnext/stock/doctype/delivery_trip/dispatch_notification_template.html",
			self.containerfile,
		)
		self.assertIn("erpnext/setup/doctype/email_digest/templates/default.html", self.containerfile)
		self.assertIn(
			"erpnext/projects/report/project_wise_stock_tracking/project_wise_stock_tracking.py",
			self.containerfile,
		)
		self.assertIn(
			"erpnext/projects/report/project_wise_stock_tracking/project_wise_stock_tracking.json",
			self.containerfile,
		)
		self.assertIn("erpnext/setup/china_money.py", self.containerfile)
		self.assertIn(
			"COPY --chown=frappe:frappe erpnext/assets/doctype/asset/asset.py "
			"/home/frappe/frappe-bench/apps/erpnext/erpnext/assets/doctype/asset/asset.py",
			self.containerfile,
		)
		self.assertIn("Verified asset purchase document translation source", self.build_script)
		self.assertIn(
			"COPY --chown=frappe:frappe erpnext/subcontracting/doctype/subcontracting_order/subcontracting_order.py "
			"/home/frappe/frappe-bench/apps/erpnext/erpnext/subcontracting/doctype/subcontracting_order/subcontracting_order.py",
			self.containerfile,
		)
		self.assertNotIn("erpnext/tests/test_subcontracting_order_i18n.py", self.containerfile)
		self.assertIn("test_subcontracting_order_i18n.py,dst=/tmp/test_subcontracting_order_i18n.py,readonly", self.build_script)
		self.assertIn("Verified subcontracting order translation behavior", self.build_script)
		self.assertIn(
			"COPY --chown=frappe:frappe erpnext/maintenance/doctype/maintenance_schedule/maintenance_schedule.py "
			"/home/frappe/frappe-bench/apps/erpnext/erpnext/maintenance/doctype/maintenance_schedule/maintenance_schedule.py",
			self.containerfile,
		)
		self.assertNotIn("erpnext/tests/test_maintenance_schedule_i18n.py", self.containerfile)
		self.assertIn("test_maintenance_schedule_i18n.py,dst=/tmp/test_maintenance_schedule_i18n.py,readonly", self.build_script)
		self.assertIn("Verified maintenance schedule translation behavior", self.build_script)
		self.assertIn(
			"COPY --chown=frappe:frappe erpnext/stock/doctype/inventory_dimension/inventory_dimension.py "
			"/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/inventory_dimension/inventory_dimension.py",
			self.containerfile,
		)
		self.assertNotIn("erpnext/tests/test_inventory_dimension_i18n.py", self.containerfile)
		self.assertIn("test_inventory_dimension_i18n.py,dst=/tmp/test_inventory_dimension_i18n.py,readonly", self.build_script)
		self.assertIn("Verified inventory dimension translation behavior", self.build_script)
		self.assertIn(
			"COPY --chown=frappe:frappe erpnext/stock/doctype/stock_entry/stock_entry.py "
			"/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/stock_entry/stock_entry.py",
			self.containerfile,
		)
		self.assertNotIn("erpnext/tests/test_stock_entry_i18n.py", self.containerfile)
		self.assertIn("test_stock_entry_i18n.py,dst=/tmp/test_stock_entry_i18n.py,readonly", self.build_script)
		self.assertIn("Verified stock entry translation behavior", self.build_script)
		self.assertIn(
			"COPY --chown=frappe:frappe erpnext/stock/serial_batch_bundle.py "
			"/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/serial_batch_bundle.py",
			self.containerfile,
		)
		self.assertNotIn("erpnext/tests/test_serial_batch_bundle_i18n.py", self.containerfile)
		self.assertIn("test_serial_batch_bundle_i18n.py,dst=/tmp/test_serial_batch_bundle_i18n.py,readonly", self.build_script)
		self.assertIn("Verified serial and batch bundle translation behavior", self.build_script)
		self.assertIn(
			"COPY --chown=frappe:frappe erpnext/stock/doctype/item_price/item_price.py "
			"/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/item_price/item_price.py",
			self.containerfile,
		)
		self.assertNotIn("erpnext/tests/test_item_price_i18n.py", self.containerfile)
		self.assertIn("test_item_price_i18n.py,dst=/tmp/test_item_price_i18n.py,readonly", self.build_script)
		self.assertIn("Verified item price translation behavior", self.build_script)
		self.assertIn(
			"COPY --chown=frappe:frappe erpnext/stock/doctype/purchase_receipt/purchase_receipt.py "
			"/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/purchase_receipt/purchase_receipt.py",
			self.containerfile,
		)
		self.assertNotIn("erpnext/tests/test_purchase_receipt_i18n.py", self.containerfile)
		self.assertIn("test_purchase_receipt_i18n.py,dst=/tmp/test_purchase_receipt_i18n.py,readonly", self.build_script)
		self.assertIn("Verified purchase receipt translation behavior", self.build_script)
		self.assertIn(
			"COPY --chown=frappe:frappe erpnext/stock/doctype/repost_item_valuation/repost_item_valuation.py "
			"/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/repost_item_valuation/repost_item_valuation.py",
			self.containerfile,
		)
		self.assertNotIn("erpnext/tests/test_repost_item_valuation_i18n.py", self.containerfile)
		self.assertIn("test_repost_item_valuation_i18n.py,dst=/tmp/test_repost_item_valuation_i18n.py,readonly", self.build_script)
		self.assertIn("Verified repost item valuation translation behavior", self.build_script)
		self.assertIn(
			"COPY --chown=frappe:frappe erpnext/accounts/doctype/promotional_scheme/promotional_scheme.py "
			"/home/frappe/frappe-bench/apps/erpnext/erpnext/accounts/doctype/promotional_scheme/promotional_scheme.py",
			self.containerfile,
		)
		self.assertNotIn("erpnext/tests/test_promotional_scheme_i18n.py", self.containerfile)
		self.assertIn("test_promotional_scheme_i18n.py,dst=/tmp/test_promotional_scheme_i18n.py,readonly", self.build_script)
		self.assertIn("Verified promotional scheme translation behavior", self.build_script)
		self.assertIn(
			"COPY --chown=frappe:frappe erpnext/controllers/taxes_and_totals.py "
			"/home/frappe/frappe-bench/apps/erpnext/erpnext/controllers/taxes_and_totals.py",
			self.containerfile,
		)
		self.assertNotIn("erpnext/tests/test_taxes_and_totals_i18n.py", self.containerfile)
		self.assertIn("test_taxes_and_totals_i18n.py,dst=/tmp/test_taxes_and_totals_i18n.py,readonly", self.build_script)
		self.assertIn("Verified taxes and totals translation behavior", self.build_script)
		self.assertIn(
			"COPY --chown=frappe:frappe erpnext/accounts/doctype/process_statement_of_accounts/process_statement_of_accounts.py "
			"/home/frappe/frappe-bench/apps/erpnext/erpnext/accounts/doctype/process_statement_of_accounts/process_statement_of_accounts.py",
			self.containerfile,
		)
		self.assertNotIn("erpnext/tests/test_process_statement_i18n.py", self.containerfile)
		self.assertIn("test_process_statement_i18n.py,dst=/tmp/test_process_statement_i18n.py,readonly", self.build_script)
		self.assertIn("Verified process statement translation behavior", self.build_script)
		self.assertIn(
			"erpnext/accounts/report/tds_computation_summary/tds_computation_summary.py",
			self.containerfile,
		)
		self.assertIn(
			"erpnext/accounts/report/tax_withholding_details/tax_withholding_details.py",
			self.containerfile,
		)
		self.assertNotIn("erpnext/tests/test_tax_report_labels_i18n.py", self.containerfile)
		self.assertIn("test_tax_report_labels_i18n.py,dst=/tmp/test_tax_report_labels_i18n.py,readonly", self.build_script)
		self.assertIn("Verified tax report label translation behavior", self.build_script)
		self.assertIn(
			"erpnext/stock/doctype/serial_and_batch_bundle/serial_and_batch_bundle.py",
			self.containerfile,
		)
		self.assertIn(
			"COPY --chown=frappe:frappe erpnext/stock/doctype/stock_ledger_entry/stock_ledger_entry.py "
			"/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/stock_ledger_entry/stock_ledger_entry.py",
			self.containerfile,
		)
		self.assertIn("Verified Stock Ledger Entry translation source", self.build_script)
		self.assertIn(
			"COPY --chown=frappe:frappe erpnext/stock/stock_ledger.py "
			"/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/stock_ledger.py",
			self.containerfile,
		)
		self.assertIn("Verified stock reposting translation source", self.build_script)
		self.assertIn("erpnext/hooks.py", self.containerfile)
		self.assertIn("erpnext/controllers/selling_controller.py", self.containerfile)
		self.assertIn("erpnext/selling/doctype/customer/customer.py", self.containerfile)
		self.assertIn("erpnext/selling/page/point_of_sale/pos_payment.js", self.containerfile)
		self.assertIn("erpnext/selling/page/point_of_sale/pos_item_details.js", self.containerfile)
		self.assertIn("erpnext/controllers/buying_controller.py", self.containerfile)
		self.assertIn("erpnext/controllers/accounts_controller.py", self.containerfile)
		self.assertIn("erpnext/buying/doctype/purchase_order/purchase_order.js", self.containerfile)
		self.assertNotIn("erpnext/tests/test_buying_controller_i18n.py", self.containerfile)
		self.assertIn(
			"test_buying_controller_i18n.py,dst=/tmp/test_buying_controller_i18n.py,readonly",
			self.build_script,
		)
		self.assertIn("Verified buying controller translation behavior", self.build_script)
		self.assertIn("erpnext/controllers/stock_controller.py", self.containerfile)
		self.assertIn("erpnext/controllers/subcontracting_controller.py", self.containerfile)
		self.assertIn("erpnext/controllers/trends.py", self.containerfile)
		self.assertIn("erpnext/accounts/doctype/payment_entry/payment_entry.py", self.containerfile)
		self.assertIn("erpnext/accounts/doctype/journal_entry/journal_entry.py", self.containerfile)
		self.assertIn("erpnext/accounts/doctype/exchange_rate_revaluation/exchange_rate_revaluation.py", self.containerfile)
		self.assertIn("erpnext/accounts/doctype/bank_reconciliation_tool/bank_reconciliation_tool.js", self.containerfile)
		self.assertIn("erpnext/accounts/doctype/opening_invoice_creation_tool/opening_invoice_creation_tool.py", self.containerfile)
		self.assertIn("erpnext/accounts/doctype/financial_report_template/financial_report_engine.py", self.containerfile)
		self.assertIn("erpnext/accounts/notification/notification_for_new_fiscal_year/notification_for_new_fiscal_year.html", self.containerfile)
		self.assertIn("erpnext/accounts/notification/notification_for_new_fiscal_year/notification_for_new_fiscal_year.json", self.containerfile)
		self.assertIn("erpnext/accounts/party.py", self.containerfile)
		for source_path in (
			"erpnext/accounts/report/financial_statements.py",
			"erpnext/accounts/report/dimension_wise_accounts_balance_report/dimension_wise_accounts_balance_report.py",
			"erpnext/accounts/doctype/accounts_settings/accounts_settings.py",
			"erpnext/accounts/doctype/account/account.py",
			"erpnext/accounts/doctype/accounting_dimension/accounting_dimension.js",
			"erpnext/stock/utils.py",
			"erpnext/stock/doctype/stock_closing_entry/stock_closing_entry.py",
			"erpnext/accounts/doctype/bank_transaction/bank_transaction_upload.py",
			"erpnext/accounts/doctype/subscription/subscription.py",
			"erpnext/accounts/doctype/ledger_merge/ledger_merge.py",
			"erpnext/accounts/doctype/bank_statement_import/bank_statement_import.py",
			"erpnext/accounts/doctype/bank_clearance/bank_clearance.py",
			"erpnext/stock/reorder_item.py",
			"erpnext/stock/doctype/repost_item_valuation/repost_item_valuation.py",
			"erpnext/stock/report/stock_and_account_value_comparison/stock_and_account_value_comparison.js",
			"erpnext/stock/report/stock_ledger_invariant_check/stock_ledger_invariant_check.js",
			"erpnext/stock/report/stock_ledger_variance/stock_ledger_variance.js",
			"erpnext/stock/get_item_details.py",
			"erpnext/stock/doctype/item/item.py",
			"erpnext/stock/doctype/inventory_dimension/inventory_dimension.py",
			"erpnext/stock/doctype/landed_cost_voucher/landed_cost_voucher.py",
			"erpnext/stock/doctype/stock_entry/stock_entry.py",
		):
			self.assertIn(source_path, self.containerfile)
		self.assertIn("erpnext/crm/doctype/email_campaign/email_campaign.py", self.containerfile)
		self.assertIn("erpnext/utilities/bulk_transaction.py", self.containerfile)
		self.assertIn("erpnext/utilities/doctype/video/video.py", self.containerfile)
		self.assertIn("erpnext/utilities/doctype/video_settings/video_settings.py", self.containerfile)
		self.assertIn(
			"erpnext/crm/doctype/appointment_booking_settings/appointment_booking_settings.py",
			self.containerfile,
		)
		self.assertIn("pos_invoice_with_item_image.json", self.containerfile)
		self.assertIn("sales_invoice_with_item_image.json", self.containerfile)
		self.assertIn("cheque_printing_format.json", self.containerfile)
		self.assertIn("company_letterhead_grey.html", self.containerfile)
		self.assertIn("erpnext/accounts/letterhead/company_letterhead.html", self.containerfile)
		for portal_template in (
			"erpnext/www/support/index.html",
			"erpnext/templates/includes/projects/project_search_box.html",
			"erpnext/templates/pages/projects.html",
			"erpnext/templates/includes/macros.html",
		):
			self.assertIn(portal_template, self.containerfile)
		self.assertIn("company_letterhead___grey.json", self.containerfile)
		self.assertIn("erpnext/stock/doctype/item/item.json", self.containerfile)
		self.assertIn("erpnext/stock/utils.py", self.containerfile)
		self.assertIn("erpnext/manufacturing/doctype/production_plan/production_plan.py", self.containerfile)
		self.assertIn("erpnext/setup/china_defaults.py", self.containerfile)
		self.assertIn("erpnext/patches.txt", self.containerfile)
		self.assertIn("erpnext/patches/v16_0/localize_china_demo_cached_values.py", self.containerfile)
		self.assertIn("erpnext.patches.v16_0.localize_china_demo_cached_values", self.patches)
		self.assertIn("erpnext/setup/demo_data/customer.json", self.containerfile)
		self.assertIn("erpnext/setup/demo_data/customer_group.json", self.containerfile)
		self.assertIn("erpnext/setup/demo_data/item.json", self.containerfile)
		self.assertIn("erpnext/setup/demo_data/item_group.json", self.containerfile)
		self.assertIn("erpnext/setup/demo_data/purchase_order.json", self.containerfile)
		self.assertIn("erpnext/setup/demo_data/sales_order.json", self.containerfile)
		self.assertIn("erpnext/setup/demo_data/supplier.json", self.containerfile)
		self.assertIn("erpnext/setup/demo_data/supplier_group.json", self.containerfile)
		self.assertIn("localize_bundled_demo_data", self.deploy_script)
		self.assertIn("Verified bundled Chinese demo data", self.build_script)
		self.assertIn("erpnext/setup/setup_wizard/operations/defaults_setup.py", self.containerfile)
		self.assertIn(
			'\\\"module\\\":\\\"accounts\\\",\\\"dt\\\":\\\"notification\\\",\\\"dn\\\":\\\"notification_for_new_fiscal_year\\\",\\\"force\\\":True',
			self.deploy_script,
		)
		self.assertIn("AS banking-builder", self.containerfile)
		self.assertIn("COPY banking/ ./", self.containerfile)
		self.assertIn("yarn test:localization && mkdir -p /erpnext/www && yarn build", self.containerfile)
		self.assertIn("/home/frappe/frappe-bench/assets/erpnext/banking", self.containerfile)
		self.assertIn("/home/frappe/frappe-bench/apps/erpnext/erpnext/www/banking.html", self.containerfile)
		self.assertGreater(
			self.containerfile.index("COPY --from=banking-builder"),
			self.containerfile.index("bench build --app erpnext"),
		)
		self.assertIn("assets/erpnext/banking", self.containerfile)
		banking_main = (self.repo_root / "banking" / "src" / "main.tsx").read_text()
		banking_html = (self.repo_root / "banking" / "index.html").read_text()
		self.assertIn("await resolveTranslationMessages", banking_main)
		self.assertIn("window.frappe?._translations_loaded", banking_main)
		self.assertIn("function renderApp", banking_main)
		self.assertIn("frappe._messages = frappe.boot.__messages || {};", banking_html)
		self.assertIn("data.message || {}", banking_html)
		self.assertIn("frappe-v16.24.4-zh.po", self.containerfile)
		self.assertIn("localization/frappe/zh.po", self.containerfile)
		self.assertIn("localization/frappe/realtime_utils.js", self.containerfile)
		self.assertIn("apps/frappe/realtime/utils.js", self.containerfile)
		self.assertNotIn("apps/frappe/frappe/realtime/utils.js", self.containerfile)
		self.assertIn("merge_frappe_zh_catalog.py", self.containerfile)
		self.assertIn("merge_erpnext_zh_banking.py", self.containerfile)
		self.assertIn("localization/erpnext/zh_banking.json", self.containerfile)
		self.assertIn("patch_frappe_print_page.py", self.containerfile)
		self.assertIn("patch_frappe_desktop_page.py", self.containerfile)
		self.assertIn("patch_frappe_login_page.py", self.containerfile)
		self.assertIn("sync_asset_manifest.py", self.containerfile)
		self.assertIn("/tmp/patch_frappe_print_page.py", self.containerfile)
		self.assertIn("/tmp/patch_frappe_desktop_page.py", self.containerfile)
		self.assertIn("/tmp/patch_frappe_login_page.py", self.containerfile)
		self.assertIn("Verified translated standard workspace sidebar labels", self.build_script)
		self.assertIn("frappe.mo", self.containerfile)
		for name in (
			"purchase_auditing_voucher",
			"sales_auditing_voucher",
			"bank_and_cash_payment_voucher",
			"journal_auditing_voucher",
		):
			self.assertIn(f"accounts/print_format/{name}/{name}.json", self.containerfile)
			self.assertIn(f"accounts/print_format/{name}/{name}.html", self.containerfile)
			self.assertIn(f'\\"dn\\":\\"{name}\\"', self.deploy_script)

	def test_frappe_catalog_uses_a_pinned_verified_official_baseline(self):
		self.assertIn("fetch_frappe_zh_baseline.sh", self.build_script)
		self.assertIn('source "$script_dir/frappe_zh_baseline.conf"', self.fetch_script)
		self.assertIn("FRAPPE_ZH_BASELINE_VERSION=16.24.4", self.baseline_config)
		self.assertIn("FRAPPE_RUNTIME_VERSION=16.31.0", self.baseline_config)
		self.assertIn(
			"FRAPPE_ZH_BASELINE_SHA256=b0d107adf4e064622b03aefed46e5d3a06c6daae05cca0a4d5d07fb1e5fef586",
			self.baseline_config,
		)
		self.assertIn(
			"FRAPPE_RUNTIME_POT_SHA256=85b83712b6c5e7ceeaa34648acf4443971974e873f3c1c677e614c581749744f",
			self.baseline_config,
		)
		self.assertIn("frappe/locale/main.pot", self.fetch_script)
		self.assertIn("frappe.__version__ != expected_frappe_version", self.build_script)
		self.assertIn("Compiled Frappe translations do not match", self.build_script)
		self.assertIn("validate_frappe_runtime_i18n.py", self.containerfile)
		self.assertIn("validate_frappe_runtime_i18n.py", self.build_script)
		self.assertIn("frappe/public/js", self.runtime_i18n_validator)

	def test_image_manifest_points_to_the_built_bundle(self):
		self.assertIn("sync_asset_manifest.py", self.containerfile)
		self.assertIn("assets/assets.json", self.containerfile)
		self.assertIn("Asset manifest references missing files", self.build_script)
		self.assertIn("Compiled ERPNext translations do not match", self.build_script)
		self.assertIn('"Statement PDF Password": "对账单 PDF 密码"', self.build_script)
		self.assertIn('"Matching Rules": "匹配规则"', self.build_script)
		self.assertIn('"A new fiscal year has been automatically created.": "已自动创建新会计年度。"', self.build_script)
		self.assertIn('"No <strong>Account Data</strong> row found": "未找到<strong>科目数据</strong>行。"', self.build_script)
		self.assertIn('"Appointment Booking Portal Settings": "预约门户设置"', self.build_script)
		self.assertIn('"Email Campaign Send Error": "邮件营销活动发送错误"', self.build_script)
		self.assertIn('"Invalid Discount Amount": "折扣金额无效"', self.build_script)
		self.assertIn('"Reserved Batch Conflict": "预留批次冲突"', self.build_script)
		self.assertIn('"Stock Frozen": "库存已冻结"', self.build_script)
		self.assertIn('"Duplicate Serial Number Error": "序列号重复错误"', self.build_script)
		self.assertIn('"Quality Inspection Not Configured": "质量检验单未配置"', self.build_script)
		self.assertIn('"Select Company Address": "选择公司地址"', self.build_script)
		self.assertIn('"Invite Users": "邀请用户"', self.build_script)
		self.assertIn('"Use Posting Datetime for Naming Documents": "使用记账日期时间生成单据编号"', self.build_script)
		self.assertIn('"BOM Stock Analysis": "物料清单库存分析"', self.build_script)
		self.assertIn('"Subcontracting Setup": "委外设置"', self.build_script)
		self.assertIn('"Subcontracting Inward Order": "受托加工订单"', self.build_script)
		self.assertIn('"Subcontracting Delivery": "受托加工交付"', self.build_script)
		self.assertIn('"Subcontracted Purchase Order": "委外采购订单"', self.build_script)
		self.assertIn('"Subcontract BOM": "委外物料清单"', self.build_script)
		self.assertIn("this.print_format_control.get_value()", self.build_script)
		self.assertIn("Banking HTML references missing assets", self.build_script)
		self.assertIn("Banking entry bundle lacks translation readiness contract", self.build_script)
		self.assertIn("Refusing to build from a dirty worktree", self.build_script)

	def test_asset_manifest_syncs_every_built_bundle(self):
		with TemporaryDirectory() as temporary_directory:
			asset_root = Path(temporary_directory)
			(asset_root / "frappe/dist/css").mkdir(parents=True)
			(asset_root / "erpnext/dist/js").mkdir(parents=True)
			(asset_root / "frappe/dist/css/desk.bundle.NEW123.css").write_text("desk")
			(asset_root / "erpnext/dist/js/erpnext.bundle.NEW456.js").write_text("erpnext")
			manifest_path = asset_root / "assets.json"
			manifest_path.write_text(
				json.dumps(
					{
						"desk.bundle.css": "/assets/frappe/dist/css/desk.bundle.OLD.css",
						"erpnext.bundle.js": "/assets/erpnext/dist/js/erpnext.bundle.OLD.js",
					}
				)
			)

			self.assertEqual(sync_manifest(asset_root, manifest_path), 2)
			manifest = json.loads(manifest_path.read_text())
			self.assertEqual(
				manifest["desk.bundle.css"], "/assets/frappe/dist/css/desk.bundle.NEW123.css"
			)
			self.assertEqual(
				manifest["erpnext.bundle.js"], "/assets/erpnext/dist/js/erpnext.bundle.NEW456.js"
			)

	def test_chart_month_localization_is_scoped_to_the_x_axis(self):
		self.assertIn(
			'const chart_date_selector = ".chart-container svg .x.axis text";',
			self.browser_overrides,
		)
		self.assertNotIn(
			'const chart_date_selector = ".chart-container svg text";',
			self.browser_overrides,
		)

	def test_account_tree_uses_the_account_specific_root_label(self):
		self.assertIn('root_label: "All Accounts"', self.account_tree)
		self.assertNotIn('root_label: "Accounts"', self.account_tree)

	def test_audit_list_localization_uses_doctype_hooks(self):
		hooks = (self.repo_root / "erpnext" / "hooks.py").read_text()
		self.assertIn('"Activity Log": "public/js/zh_audit_list.js"', hooks)
		self.assertIn('"Access Log": "public/js/zh_audit_list.js"', hooks)
		self.assertIn('"User": "public/js/zh_audit_list.js"', hooks)

	def test_timeline_localization_is_scoped_to_timeline_content(self):
		self.assertIn('const timeline_selector = ".timeline-content";', self.browser_overrides)
		self.assertIn('a[href="/desk/user/Administrator"]', self.browser_overrides)
		self.assertIn('a[href^="/desk/version/"] b', self.browser_overrides)
		self.assertIn('"Book Advance Payments In Separate Party Account": "启用预收/付款科目"', self.browser_overrides)

	def test_report_datatable_controls_are_localized(self):
		self.assertIn("input.dt-filter[title^='Filter based on ']", self.browser_overrides)
		self.assertIn("#tree-level[aria-label='Tree Level']", self.browser_overrides)
		self.assertIn("div[style*='text-align: right']", self.browser_overrides)
		self.assertIn(".list-row-head [data-sort-by][title]", self.browser_overrides)
		self.assertIn(".list-row .ellipsis[title]", self.browser_overrides)
		self.assertIn('attributeFilter: ["aria-label", "title"]', self.browser_overrides)

	def test_realtime_proxy_preserves_the_browser_origin(self):
		self.assertIn("proxy_set_header Origin \\$frappe_socket_origin", self.containerfile)
		self.assertIn("default $http_origin", self.containerfile)
		self.assertIn('"" $scheme://$http_host', self.containerfile)
		realtime_utils = (
			self.repo_root / "localization" / "frappe" / "realtime_utils.js"
		).read_text()
		self.assertIn('["localhost", "127.0.0.1"]', realtime_utils)
		self.assertIn('"http://frontend:8080"', realtime_utils)

	def test_local_deploy_clears_runtime_translation_cache(self):
		backup_position = self.deploy_script.index("\nbackup_existing_site\n")
		compose_position = self.deploy_script.index("docker compose")
		migrate_position = self.deploy_script.index("bench --site '${site_name}' migrate")
		self.assertLess(backup_position, compose_position)
		self.assertLess(compose_position, migrate_position)
		self.assertIn("backup --with-files --compress", self.deploy_script)
		self.assertIn('docker cp "${backend_container}:${remote_dir}/."', self.deploy_script)
		self.assertIn('verify_backup_set "${host_dir}"', self.deploy_script)
		self.assertIn('chmod -R go-rwx "${host_dir}"', self.deploy_script)
		self.assertIn('BACKUP_ONLY:-0', self.deploy_script)
		self.assertIn("*-database*.sql.gz", self.deploy_script)
		self.assertIn("*-site_config_backup*.json", self.deploy_script)
		self.assertIn("*-files*.tgz", self.deploy_script)
		self.assertIn("*-private-files*.tgz", self.deploy_script)
		self.assertIn('gzip -t "${database}"', self.deploy_script)
		self.assertIn('tar -tzf "${public_files}"', self.deploy_script)
		self.assertIn('tar -tzf "${private_files}"', self.deploy_script)
		self.assertIn('python3 -m json.tool "${config}"', self.deploy_script)
		self.assertIn("Refusing deployment: sites volume", self.deploy_script)
		self.assertIn("BACKUP_ONLY=1 ./scripts/deploy_local_zh_finance.sh", self.localization_readme)
		self.assertIn("bench --site frontend restore", self.localization_readme)
		self.assertIn("site_config_backup.json", self.localization_readme)
		self.assertIn("up -d --force-recreate", self.deploy_script)
		self.assertIn("for attempt in {1..30}", self.deploy_script)
		self.assertIn("timeout 5s bench --site '${site_name}' execute frappe.utils.now", self.deploy_script)
		self.assertIn("bench --site '${site_name}' execute frappe.utils.now", self.deploy_script)
		self.assertIn("Local ERPNext did not become ready", self.deploy_script)
		self.assertIn("bench --site '${site_name}' migrate", self.deploy_script)
		self.assertIn(
			"bench --site '${site_name}' execute erpnext.setup.china_defaults.apply_china_defaults --kwargs '{\\\"clear_cache\\\":False}'",
			self.deploy_script,
		)
		self.assertIn("bench --site '${site_name}' execute frappe.reload_doc", self.deploy_script)
		self.assertIn("pos_invoice_with_item_image", self.deploy_script)
		self.assertIn("sales_invoice_with_item_image", self.deploy_script)
		self.assertIn("cheque_printing_format", self.deploy_script)
		self.assertIn("company_letterhead___grey", self.deploy_script)
		self.assertIn("bench --site '${site_name}' clear-cache", self.deploy_script)
		self.assertIn(
			"bench --site '${site_name}' execute erpnext.setup.china_defaults.get_china_localization_status",
			self.deploy_script,
		)
