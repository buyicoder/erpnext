from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.stock.doctype.stock_entry import stock_entry


class TestStockEntryI18n(TestCase):
	def test_missing_job_card_item_uses_fixed_translated_template(self):
		entry = SimpleNamespace(
			job_card="JOB-CARD-0001",
			purpose="Material Transfer for Manufacture",
			items=[SimpleNamespace(idx=3, job_card_item=None, s_warehouse="Stores - TC")],
		)
		template = (
			"Row #{0}: The Job Card Item reference is missing. Create the Stock Entry from the Job Card; "
			"rows added manually cannot be linked to a Job Card Item."
		)
		with (
			patch.object(
				stock_entry.frappe,
				"db",
				SimpleNamespace(get_single_value=lambda *args, **kwargs: 0),
			),
			patch.object(
				stock_entry,
				"_",
				side_effect=lambda message: (
					"第 {0} 行：缺少生产任务单明细引用。请从生产任务单创建物料移动；手工添加的明细无法关联生产任务单明细。"
					if message == template
					else message
				),
			),
			patch.object(stock_entry.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			stock_entry.StockEntry.validate_job_card_item(entry)

		throw.assert_called_once_with(
			"第 3 行：缺少生产任务单明细引用。请从生产任务单创建物料移动；手工添加的明细无法关联生产任务单明细。"
		)

	def test_valid_job_card_item_does_not_raise(self):
		entry = SimpleNamespace(
			job_card="JOB-CARD-0001",
			purpose="Material Transfer for Manufacture",
			items=[SimpleNamespace(idx=1, job_card_item="JOB-CARD-ITEM-0001", s_warehouse="Stores - TC")],
		)
		with (
			patch.object(
				stock_entry.frappe,
				"db",
				SimpleNamespace(get_single_value=lambda *args, **kwargs: 0),
			),
			patch.object(stock_entry.frappe, "throw") as throw,
		):
			stock_entry.StockEntry.validate_job_card_item(entry)

		throw.assert_not_called()
