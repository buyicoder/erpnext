import re
from string import Formatter
from pathlib import Path
from unittest import TestCase

from scripts.apply_zh_finance_translations import TRANSLATIONS


class TestZhFinanceTranslations(TestCase):
	def test_reviewed_finance_terms_are_translated(self):
		catalog = (Path(__file__).parents[1] / "locale" / "zh.po").read_text()

		for source in TRANSLATIONS:
			with self.subTest(source=source):
				entry = re.search(
					rf'msgid "{re.escape(source)}"\nmsgstr "(.+)"', catalog
				)
				self.assertIsNotNone(entry)

	def test_core_finance_journey_uses_chinese_terms(self):
		for source in (
			"Accounting Onboarding",
			"Custom Financial Statement",
			"Configure Chart of Accounts",
			"Review Accounts Settings",
			"View Balance Sheet",
		):
			self.assertIn(source, TRANSLATIONS)

	def test_format_placeholders_are_preserved(self):
		for source, translation in TRANSLATIONS.items():
			with self.subTest(source=source):
				source_fields = {field for _, field, _, _ in Formatter().parse(source) if field}
				translation_fields = {
					field for _, field, _, _ in Formatter().parse(translation) if field
				}
				self.assertEqual(source_fields, translation_fields)
