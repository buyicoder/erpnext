from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.stock.doctype.repost_item_valuation import repost_item_valuation


class TestRepostItemValuationI18n(TestCase):
	def test_period_closing_error_uses_fixed_translated_template_and_inclusive_boundary(self):
		document = SimpleNamespace(
			company="示例公司",
			posting_date="2026-12-31",
			get_max_period_closing_date=lambda company: "2026-12-31",
		)
		template = "Due to period closing, item valuation cannot be reposted on or before {0}."
		with (
			patch.object(repost_item_valuation, "getdate", side_effect=lambda value: value),
			patch.object(repost_item_valuation.frappe, "format", return_value="2026年12月31日"),
			patch.object(
				repost_item_valuation,
				"_",
				side_effect=lambda message: (
					"会计期间已结账，不能对 {0} 或更早日期的物料成本价进行追溯调整。"
					if message == template
					else message
				),
			),
			patch.object(repost_item_valuation.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			repost_item_valuation.RepostItemValuation.validate_period_closing_voucher(document)

		throw.assert_called_once_with(
			"会计期间已结账，不能对 2026年12月31日 或更早日期的物料成本价进行追溯调整。"
		)

	def test_stock_closing_entry_error_uses_reviewed_terms_and_inclusive_boundary(self):
		document = SimpleNamespace(
			company="示例公司",
			posting_date="2026-12-31",
			voucher_type=None,
			get_max_period_closing_date=lambda company: None,
			get_closing_stock_balance=lambda: [
				SimpleNamespace(name="STOCK-CLOSING-0001", posting_date="2026-12-31")
			],
		)
		template = "Due to Stock Closing Entry {0}, item valuation cannot be reposted on or before {1}."
		with (
			patch.object(repost_item_valuation, "get_link_to_form", return_value="STOCK-CLOSING-0001"),
			patch.object(repost_item_valuation.frappe, "format", return_value="2026年12月31日"),
			patch.object(
				repost_item_valuation,
				"_",
				side_effect=lambda message: (
					"因存在库存结转分录 {0}，不能对 {1} 或更早日期的物料成本价进行追溯调整。"
					if message == template
					else message
				),
			),
			patch.object(repost_item_valuation.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			repost_item_valuation.RepostItemValuation.validate_period_closing_voucher(document)

		throw.assert_called_once_with(
			"因存在库存结转分录 STOCK-CLOSING-0001，不能对 2026年12月31日 或更早日期的物料成本价进行追溯调整。"
		)
