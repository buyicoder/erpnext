from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.controllers import taxes_and_totals


class AttrDict(dict):
	__getattr__ = dict.__getitem__
	__setattr__ = dict.__setitem__


class TestTaxesAndTotalsI18n(TestCase):
	def test_invalid_tax_breakup_rows_translate_row_and_difference(self):
		tax = AttrDict(
			idx=2,
			charge_type="On Net Total",
			add_deduct_tax="Add",
			base_tax_amount_after_discount_amount=10,
			precision=lambda fieldname: 2,
		)
		detail = AttrDict(tax=tax, rate=5, amount=0)
		doc = SimpleNamespace(
			taxes=[tax],
			_item_wise_tax_details=[detail],
			flags=SimpleNamespace(ignore_validate=False),
			get=lambda fieldname: [detail] if fieldname == "_item_wise_tax_details" else None,
		)
		calculator = SimpleNamespace(doc=doc)
		translations = {
			"Row {0} (Difference: {1})": "第 {0} 行（差额：{1}）",
			"Item Wise Tax Details do not match with Taxes and Charges at the following rows:": "以下行的物料税费明细与税费不一致：",
		}
		with (
			patch.object(taxes_and_totals, "ignore_item_wise_tax_details", return_value=False),
			patch.object(taxes_and_totals, "flt", side_effect=lambda value, precision=None: float(value)),
			patch.object(
				taxes_and_totals,
				"_",
				side_effect=lambda message: translations.get(message, message),
			),
			patch.object(taxes_and_totals.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			taxes_and_totals.calculate_taxes_and_totals.adjust_rounding_in_item_wise_tax_details(
				calculator
			)

		throw.assert_called_once_with("以下行的物料税费明细与税费不一致：<br>第 2 行（差额：10.0）")
