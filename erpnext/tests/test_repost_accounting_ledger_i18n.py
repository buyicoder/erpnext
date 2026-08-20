from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.accounts.doctype.repost_accounting_ledger import repost_accounting_ledger


class TestRepostAccountingLedgerI18n(TestCase):
	def test_disallowed_document_types_are_translated_without_dynamic_grammar(self):
		template = (
			"The following document types cannot be reposted:<ul>{0}</ul>"
			"Add them to {1} in {2} to enable reposting."
		)
		translations = {
			template: "以下单据类型不能重新过账：<ul>{0}</ul>如需启用，请将这些单据类型添加到“{1}”表格（位于{2}）。",
			"Allowed DocTypes": "允许的单据类型",
			"Purchase Invoice": "采购发票",
			"Sales Invoice": "销售发票",
		}
		escaped_values = []

		def escape_html(value):
			escaped_values.append(value)
			return f"[escaped]{value}"

		with (
			patch.object(repost_accounting_ledger, "get_allowed_types_from_settings", return_value=[]),
			patch.object(
				repost_accounting_ledger,
				"_",
				side_effect=lambda message: translations.get(message, message),
			),
			patch.object(
				repost_accounting_ledger.frappe,
				"bold",
				side_effect=lambda value: f"<b>{value}</b>",
			),
			patch.object(
				repost_accounting_ledger.frappe.utils,
				"escape_html",
				side_effect=escape_html,
			),
			patch.object(
				repost_accounting_ledger.frappe.utils,
				"get_link_to_form",
				return_value='<a href="/app/accounts-settings">会计设置</a>',
			),
			patch.object(
				repost_accounting_ledger.frappe,
				"throw",
				side_effect=RuntimeError,
			) as throw,
			self.assertRaises(RuntimeError),
		):
			repost_accounting_ledger.validate_docs_for_voucher_types(
				["Sales Invoice", "Purchase Invoice"]
			)

		throw.assert_called_once_with(
			"以下单据类型不能重新过账：<ul><li><b>[escaped]采购发票</b></li>"
			"<li><b>[escaped]销售发票</b></li></ul>如需启用，请将这些单据类型添加到“"
			'<b>允许的单据类型</b>”表格（位于<a href="/app/accounts-settings">会计设置</a>）。'
		)
		self.assertEqual(escaped_values, ["采购发票", "销售发票"])

	def test_deferred_documents_remain_visible_in_the_localized_error(self):
		template = (
			"The following documents have deferred revenue or expense enabled and cannot be reposted:<ul>{0}</ul>"
		)
		translations = {
			template: "以下单据已启用递延收入或递延费用，不能重新过账：<ul>{0}</ul>"
		}
		escaped_values = []

		def escape_html(value):
			escaped_values.append(value)
			return f"[escaped]{value}"

		def get_all(doctype, **_kwargs):
			return {
				"Sales Invoice Item": [("SINV-0002",), ("SINV-0001",)],
				"Purchase Invoice Item": [("PINV-0001",), ("SINV-0001",)],
			}[doctype]

		with (
			patch.object(
				repost_accounting_ledger.frappe,
				"db",
				SimpleNamespace(get_all=get_all),
			),
			patch.object(
				repost_accounting_ledger,
				"_",
				side_effect=lambda message: translations.get(message, message),
			),
			patch.object(
				repost_accounting_ledger.frappe,
				"bold",
				side_effect=lambda value: f"<b>{value}</b>",
			),
			patch.object(
				repost_accounting_ledger.frappe.utils,
				"escape_html",
				side_effect=escape_html,
			),
			patch.object(
				repost_accounting_ledger.frappe,
				"throw",
				side_effect=RuntimeError,
			) as throw,
			self.assertRaises(RuntimeError),
		):
			repost_accounting_ledger.validate_docs_for_deferred_accounting(
				["SINV-0001", "SINV-0002"], ["PINV-0001"]
			)

		throw.assert_called_once_with(
			"以下单据已启用递延收入或递延费用，不能重新过账："
			"<ul><li><b>[escaped]PINV-0001</b></li><li><b>[escaped]SINV-0001</b></li>"
			"<li><b>[escaped]SINV-0002</b></li></ul>"
		)
		self.assertEqual(escaped_values, ["PINV-0001", "SINV-0001", "SINV-0002"])

	def test_deferred_validation_supports_sales_or_purchase_documents_independently(self):
		template = (
			"The following documents have deferred revenue or expense enabled and cannot be reposted:<ul>{0}</ul>"
		)
		translations = {
			template: "以下单据已启用递延收入或递延费用，不能重新过账：<ul>{0}</ul>"
		}
		cases = (
			(["SINV-0001"], [], "Sales Invoice Item", "SINV-0001"),
			([], ["PINV-0001"], "Purchase Invoice Item", "PINV-0001"),
		)

		for sales_docs, purchase_docs, expected_doctype, expected_name in cases:
			with self.subTest(expected_doctype=expected_doctype):
				queried_doctypes = []

				def get_all(doctype, **_kwargs):
					queried_doctypes.append(doctype)
					return [(expected_name,)]

				with (
					patch.object(
						repost_accounting_ledger.frappe,
						"db",
						SimpleNamespace(get_all=get_all),
					),
					patch.object(
						repost_accounting_ledger,
						"_",
						side_effect=lambda message: translations.get(message, message),
					),
					patch.object(
						repost_accounting_ledger.frappe,
						"bold",
						side_effect=lambda value: f"<b>{value}</b>",
					),
					patch.object(
						repost_accounting_ledger.frappe.utils,
						"escape_html",
						side_effect=lambda value: value,
					),
					patch.object(
						repost_accounting_ledger.frappe,
						"throw",
						side_effect=RuntimeError,
					) as throw,
					self.assertRaises(RuntimeError),
				):
					repost_accounting_ledger.validate_docs_for_deferred_accounting(
						sales_docs, purchase_docs
					)

				self.assertEqual(queried_doctypes, [expected_doctype])
				throw.assert_called_once_with(
					"以下单据已启用递延收入或递延费用，不能重新过账："
					f"<ul><li><b>{expected_name}</b></li></ul>"
				)
