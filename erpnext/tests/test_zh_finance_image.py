from pathlib import Path
from unittest import TestCase


class TestZhFinanceImage(TestCase):
	def setUp(self):
		self.repo_root = Path(__file__).parents[2]
		self.containerfile = (
			self.repo_root / "docker" / "zh-finance" / "Containerfile"
		).read_text()
		self.deploy_script = (self.repo_root / "scripts" / "deploy_local_zh_finance.sh").read_text()

	def test_image_compiles_translations_and_frontend_assets(self):
		self.assertIn("bench compile-po-to-mo --app erpnext --locale zh --force", self.containerfile)
		self.assertIn("bench compile-po-to-mo --app frappe --locale zh --force", self.containerfile)
		self.assertIn("bench build --app erpnext", self.containerfile)
		self.assertIn("erpnext/public/js/zh_finance_format.mjs", self.containerfile)
		self.assertIn("erpnext/projects/doctype/project/project.py", self.containerfile)
		self.assertIn("erpnext/stock/doctype/item/item.json", self.containerfile)
		self.assertIn("erpnext/setup/china_defaults.py", self.containerfile)
		self.assertIn("erpnext/setup/setup_wizard/operations/defaults_setup.py", self.containerfile)
		self.assertIn("localization/frappe/zh.po", self.containerfile)
		self.assertIn("frappe.mo", self.containerfile)

	def test_image_manifest_points_to_the_built_bundle(self):
		self.assertIn("js_bundle=", self.containerfile)
		self.assertIn("assets/assets.json", self.containerfile)
		self.assertIn("erpnext/dist/js/${js_bundle}", self.containerfile)

	def test_local_deploy_clears_runtime_translation_cache(self):
		self.assertIn("up -d --force-recreate", self.deploy_script)
		self.assertIn("bench --site '${site_name}' clear-cache", self.deploy_script)
