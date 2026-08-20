from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from jinja2.sandbox import SandboxedEnvironment

from erpnext.accounts.doctype.process_statement_of_accounts import process_statement_of_accounts


class TestProcessStatementI18n(TestCase):
	def test_validate_calls_default_email_content_before_template_validation(self):
		document = SimpleNamespace(
			validate_account=Mock(),
			validate_company_for_table=Mock(),
			set_default_email_content=Mock(),
			pdf_name="往来对账单",
			subject="主题",
			body="正文",
			customers=["客户"],
			enable_auto_email=False,
			print_format=None,
		)

		with patch.object(process_statement_of_accounts, "validate_template") as validate_template:
			process_statement_of_accounts.ProcessStatementOfAccounts.validate(document)

		document.set_default_email_content.assert_called_once_with()
		self.assertEqual(
			validate_template.call_args_list,
			[
				(("主题",), {"restrict_globals": True}),
				(("正文",), {"restrict_globals": True}),
				(("往来对账单",), {"restrict_globals": True}),
			],
		)

	def test_default_email_content_uses_reviewed_chinese_templates(self):
		subject = "Statement Of Accounts for {{ customer.customer_name }}"
		general_ledger_body = (
			"Hello {{ customer.customer_name }},<br>Please find attached your Statement Of Accounts "
			"from {{ doc.from_date }} to {{ doc.to_date }}."
		)
		accounts_receivable_body = (
			"Hello {{ customer.customer_name }},<br>Please find attached your Statement Of Accounts "
			"until {{ doc.posting_date }}."
		)
		translations = {
			subject: "{{ customer.customer_name }} 往来对账单",
			general_ledger_body: (
				"{{ customer.customer_name }}，您好：<br>附件为 {{ doc.from_date }} 至 "
				"{{ doc.to_date }} 的往来对账单，请查收。"
			),
			accounts_receivable_body: (
				"{{ customer.customer_name }}，您好：<br>附件为截至 {{ doc.posting_date }} 的往来对账单，请查收。"
			),
		}

		with patch.object(
			process_statement_of_accounts,
			"_",
			side_effect=lambda message: translations.get(message, message),
		):
			general_ledger = SimpleNamespace(subject=None, body=None, report="General Ledger")
			process_statement_of_accounts.ProcessStatementOfAccounts.set_default_email_content(
				general_ledger
			)
			accounts_receivable = SimpleNamespace(
				subject=None, body=None, report="Accounts Receivable"
			)
			process_statement_of_accounts.ProcessStatementOfAccounts.set_default_email_content(
				accounts_receivable
			)

		self.assertEqual(general_ledger.subject, translations[subject])
		self.assertEqual(general_ledger.body, translations[general_ledger_body])
		self.assertEqual(accounts_receivable.subject, translations[subject])
		self.assertEqual(accounts_receivable.body, translations[accounts_receivable_body])
		context = {
			"customer": {"customer_name": "华东客户"},
			"doc": {
				"from_date": "2026-01-01",
				"to_date": "2026-06-30",
				"posting_date": "2026-06-30",
			},
		}
		def render(template):
			return SandboxedEnvironment().from_string(template).render(context)
		self.assertEqual(
			render(general_ledger.subject),
			"华东客户 往来对账单",
		)
		self.assertEqual(
			render(general_ledger.body),
			"华东客户，您好：<br>附件为 2026-01-01 至 2026-06-30 的往来对账单，请查收。",
		)
		self.assertEqual(
			render(accounts_receivable.body),
			"华东客户，您好：<br>附件为截至 2026-06-30 的往来对账单，请查收。",
		)

	def test_custom_email_content_is_preserved(self):
		document = SimpleNamespace(subject="自定义主题", body="自定义正文", report="General Ledger")
		process_statement_of_accounts.ProcessStatementOfAccounts.set_default_email_content(document)
		self.assertEqual(document.subject, "自定义主题")
		self.assertEqual(document.body, "自定义正文")

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
