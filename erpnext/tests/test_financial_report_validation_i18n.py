from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.accounts.doctype.financial_report_template import financial_report_validation


class TestFinancialReportValidationI18n(TestCase):
	def test_dynamic_values_are_inserted_after_translating_the_message_template(self):
		translations = {
			"Row {0}: ": "第 {0} 行：",
			"Formula": "公式",
			"Duplicate line reference: '{0}'": "行引用重复：“{0}”",
		}

		with patch.object(
			financial_report_validation,
			"_",
			side_effect=lambda message: translations.get(message, message),
		):
			validator = financial_report_validation.TemplateStructureValidator()
			template = SimpleNamespace(
				rows=[
					SimpleNamespace(
						idx=1,
						reference_code="REV",
						data_source="Account Data",
						balance_type="Debit",
						calculation_formula="[]",
					),
					SimpleNamespace(
						idx=2,
						reference_code="REV",
						data_source="Account Data",
						balance_type="Debit",
						calculation_formula="[]",
					),
				]
			)
			result = validator.validate(template)
			issue = result.issues[0]
			issue.field = "Formula"

			self.assertEqual(str(issue), "第 2 行：[公式] 行引用重复：“REV”")

	def test_validation_source_does_not_translate_interpolated_messages(self):
		text = Path(financial_report_validation.__file__).read_text()

		self.assertNotIn("return _(message)", text)
		self.assertNotIn('message=f"', text)
