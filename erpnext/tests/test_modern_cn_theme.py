from pathlib import Path
from unittest import TestCase


class TestModernChinaTheme(TestCase):
	def setUp(self):
		self.scss_root = Path(__file__).parents[1] / "public" / "scss"

	def test_theme_is_part_of_the_erpnext_desk_bundle(self):
		bundle = (self.scss_root / "erpnext.bundle.scss").read_text()

		self.assertIn('@import "./modern-cn-theme";', bundle)

	def test_theme_covers_core_desk_surfaces_and_responsive_layout(self):
		theme = (self.scss_root / "modern-cn-theme.scss").read_text()

		for selector in (
			"body",
			".navbar",
			".desk-sidebar",
			".layout-main-section",
			".btn-primary",
			".list-row",
			".form-control",
		):
			self.assertIn(selector, theme)

		self.assertIn("@media (max-width: 768px)", theme)
		self.assertIn('[data-theme="light"]', theme)
		self.assertIn("--navbar-height: 56px", theme)
		self.assertIn("--navbar-height: 52px", theme)
		self.assertIn(".layout-main-section.frappe-card", theme)
		self.assertIn("--cn-brand-500: #3370ff", theme)
		self.assertIn("--cn-radius-md: var(--border-radius-md)", theme)
		self.assertIn("border-radius: var(--border-radius-full)", theme)
		self.assertIn("&:focus-visible", theme)
		self.assertIn("box-shadow: var(--focus-default) !important", theme)
		self.assertNotIn("overflow: hidden", theme)

	def test_chinese_quill_toolbar_does_not_expose_english_pseudo_labels(self):
		theme = (self.scss_root / "modern-cn-theme.scss").read_text()

		for translation in (
			'content: "正文"',
			'content: "标题 #{$level}"',
			'content: "表格"',
			'content: "插入表格"',
			'content: "访问链接："',
			'content: "输入链接："',
			'content: "输入公式："',
			'content: "输入视频地址："',
			'content: "编辑"',
			'content: "保存"',
			'content: "移除"',
		):
			self.assertIn(translation, theme)
