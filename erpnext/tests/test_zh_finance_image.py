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
		self.browser_overrides = (
			self.repo_root / "erpnext" / "public" / "js" / "zh_finance_overrides.js"
		).read_text()

	def test_image_compiles_translations_and_frontend_assets(self):
		self.assertIn("bench compile-po-to-mo --app erpnext --locale zh --force", self.containerfile)
		self.assertIn("bench compile-po-to-mo --app frappe --locale zh --force", self.containerfile)
		self.assertIn("bench build --app frappe", self.containerfile)
		self.assertIn("bench build --app erpnext", self.containerfile)
		self.assertIn("erpnext/public/js/zh_finance_format.mjs", self.containerfile)
		self.assertIn("erpnext/public/js/zh_audit_list.js", self.containerfile)
		self.assertIn("erpnext/public/scss/modern-cn-theme.scss", self.containerfile)
		self.assertIn("erpnext/public/scss/erpnext.bundle.scss", self.containerfile)
		self.assertIn("erpnext/projects/doctype/project/project.py", self.containerfile)
		self.assertIn("erpnext/setup/china_money.py", self.containerfile)
		self.assertIn("erpnext/hooks.py", self.containerfile)
		self.assertIn("erpnext/controllers/selling_controller.py", self.containerfile)
		self.assertIn("erpnext/controllers/buying_controller.py", self.containerfile)
		self.assertIn("erpnext/accounts/doctype/payment_entry/payment_entry.py", self.containerfile)
		self.assertIn("erpnext/accounts/doctype/journal_entry/journal_entry.py", self.containerfile)
		self.assertIn("pos_invoice_with_item_image.json", self.containerfile)
		self.assertIn("sales_invoice_with_item_image.json", self.containerfile)
		self.assertIn("cheque_printing_format.json", self.containerfile)
		self.assertIn("company_letterhead_grey.html", self.containerfile)
		self.assertIn("company_letterhead___grey.json", self.containerfile)
		self.assertIn("erpnext/stock/doctype/item/item.json", self.containerfile)
		self.assertIn("erpnext/setup/china_defaults.py", self.containerfile)
		self.assertIn("erpnext/setup/setup_wizard/operations/defaults_setup.py", self.containerfile)
		self.assertIn("frappe-v16.24.4-zh.po", self.containerfile)
		self.assertIn("localization/frappe/zh.po", self.containerfile)
		self.assertIn("localization/frappe/realtime_utils.js", self.containerfile)
		self.assertIn("apps/frappe/realtime/utils.js", self.containerfile)
		self.assertNotIn("apps/frappe/frappe/realtime/utils.js", self.containerfile)
		self.assertIn("merge_frappe_zh_catalog.py", self.containerfile)
		self.assertIn("patch_frappe_print_page.py", self.containerfile)
		self.assertIn("sync_asset_manifest.py", self.containerfile)
		self.assertIn("/tmp/patch_frappe_print_page.py", self.containerfile)
		self.assertIn("frappe.mo", self.containerfile)

	def test_frappe_catalog_uses_a_pinned_verified_official_baseline(self):
		self.assertIn("fetch_frappe_zh_baseline.sh", self.build_script)
		self.assertIn("frappe/frappe/v16.24.4/frappe/locale/zh.po", self.fetch_script)
		self.assertIn(
			"b0d107adf4e064622b03aefed46e5d3a06c6daae05cca0a4d5d07fb1e5fef586",
			self.fetch_script,
		)

	def test_image_manifest_points_to_the_built_bundle(self):
		self.assertIn("sync_asset_manifest.py", self.containerfile)
		self.assertIn("assets/assets.json", self.containerfile)
		self.assertIn("Asset manifest references missing files", self.build_script)
		self.assertIn("this.print_format_control.get_value()", self.build_script)
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
