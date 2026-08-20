from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.accounts.doctype.process_statement_of_accounts import process_statement_of_accounts


class TestProcessStatementI18n(TestCase):
	def test_company_mismatch_translates_dynamic_doctype_without_english_plural(self):
		row = SimpleNamespace(get=lambda fieldname: "华东成本中心")
		document = SimpleNamespace(
			company="示例公司",
			get=lambda fieldname: [row] if fieldname == "cost_center" else None,
		)
		template = "<p>The following {0} records do not belong to Company {1}:</p>"
		translations = {
			template: "<p>以下{0}记录不属于公司 {1}：</p>",
			"Cost Center": "成本中心",
		}
		with (
			patch.object(process_statement_of_accounts.frappe, "scrub", return_value="cost_center"),
			patch.object(
				process_statement_of_accounts.frappe,
				"db",
				SimpleNamespace(get_all=lambda *args, **kwargs: ["外部成本中心"]),
			),
			patch.object(
				process_statement_of_accounts,
				"_",
				side_effect=lambda message: translations.get(message, message),
			),
			patch.object(
				process_statement_of_accounts.frappe,
				"bold",
				side_effect=lambda value: f"<b>{value}</b>",
			),
			patch.object(
				process_statement_of_accounts.frappe, "throw", side_effect=RuntimeError
			) as throw,
			self.assertRaises(RuntimeError),
		):
			process_statement_of_accounts.ProcessStatementOfAccounts.validate_company_for_table(
				document, "Cost Center"
			)

		throw.assert_called_once_with(
			"<p>以下成本中心记录不属于公司 <b>示例公司</b>：</p><ul><li><b>外部成本中心</b></li></ul>"
		)
