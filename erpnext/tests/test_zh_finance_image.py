from pathlib import Path
from unittest import TestCase


class TestZhFinanceImage(TestCase):
	def setUp(self):
		self.repo_root = Path(__file__).parents[2]
		self.containerfile = (
			self.repo_root / "docker" / "zh-finance" / "Containerfile"
		).read_text()

	def test_image_compiles_translations_and_frontend_assets(self):
		self.assertIn("bench compile-po-to-mo --app erpnext --locale zh --force", self.containerfile)
		self.assertIn("bench build --app erpnext", self.containerfile)

	def test_image_manifest_points_to_the_built_bundle(self):
		self.assertIn("js_bundle=", self.containerfile)
		self.assertIn("assets/assets.json", self.containerfile)
		self.assertIn("erpnext/dist/js/${js_bundle}", self.containerfile)
