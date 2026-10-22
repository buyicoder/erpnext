from unittest import TestCase
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

from erpnext.setup.china_money import (
	_candidate_names,
	_get_cny_word_updates,
	cny_amount_in_words,
	format_china_money,
	money_in_words,
	rebuild_cny_amount_in_words,
)


class TestChinaMoney(TestCase):
	def test_formats_chinese_financial_uppercase_amounts(self):
		cases = {
			0: "人民币零元整",
			10: "人民币壹拾元整",
			1001: "人民币壹仟零壹元整",
			10001: "人民币壹万零壹元整",
			229000: "人民币贰拾贰万玖仟元整",
			123456789.01: "人民币壹亿贰仟叁佰肆拾伍万陆仟柒佰捌拾玖元零壹分",
			0.56: "人民币零元伍角陆分",
		}
		for amount, expected in cases.items():
			with self.subTest(amount=amount):
				self.assertEqual(cny_amount_in_words(amount), expected)

	def test_uses_chinese_only_for_cny(self):
		self.assertEqual(money_in_words(229000, "CNY"), "人民币贰拾贰万玖仟元整")
		with patch("erpnext.setup.china_money.frappe_money_in_words", return_value="USD fallback") as fallback:
			self.assertEqual(money_in_words(1, "USD"), "USD fallback")
			fallback.assert_called_once_with(1, "USD")

	def test_formats_exact_cny_amounts_for_printing(self):
		with patch("erpnext.setup.china_money.frappe") as frappe:
			frappe.db.get_default.return_value = "2"
			frappe.utils.cint.side_effect = int
			self.assertEqual(format_china_money(363000, "CNY"), "¥363,000.00")
		self.assertEqual(format_china_money(1.2345, "CNY", precision=4), "¥1.2345")
		with patch("erpnext.setup.china_money.frappe_format_money", return_value="$1.00") as fallback:
			self.assertEqual(format_china_money(1, "USD"), "$1.00")
			fallback.assert_called_once_with(1, currency="USD", precision=None)

	def test_historical_rebuild_only_returns_changed_cny_fields(self):
		doc = MagicMock()
		doc.doctype = "Sales Invoice"
		values = {
			"in_words": "CNY One Hundred",
			"base_in_words": "人民币壹佰元整",
		}
		doc.get.side_effect = values.get

		def set_total_in_words():
			values["in_words"] = "人民币壹佰元整"
			values["base_in_words"] = "人民币壹佰元整"

		doc.set_total_in_words.side_effect = set_total_in_words

		self.assertEqual(_get_cny_word_updates(doc), {"in_words": "人民币壹佰元整"})

	@patch("erpnext.setup.china_money.frappe")
	def test_historical_candidates_are_loaded_in_bounded_batches(self, frappe):
		meta = frappe.get_meta.return_value
		meta.get_field.side_effect = lambda field: field in {"currency", "company"}
		frappe.get_all.side_effect = [["SINV-0001", "SINV-0002"], ["SINV-0003"]]

		names = list(_candidate_names("Sales Invoice", ["示例公司"], page_length=2))

		self.assertEqual(names, ["SINV-0001", "SINV-0002", "SINV-0003"])
		self.assertEqual(frappe.get_all.call_args_list[0].kwargs["limit_start"], 0)
		self.assertEqual(frappe.get_all.call_args_list[1].kwargs["limit_start"], 2)
		self.assertTrue(
			all(call_args.kwargs["limit_page_length"] <= 2 for call_args in frappe.get_all.call_args_list)
		)

	@patch("erpnext.setup.china_money._candidate_names")
	@patch("erpnext.setup.china_money.frappe")
	def test_historical_rebuild_is_dry_run_by_default(self, frappe, candidate_names):
		candidate_names.return_value = ["SINV-0001"]
		doc = SimpleNamespace(doctype="Sales Invoice")
		doc.get = lambda field: "CNY One Hundred" if field == "in_words" else None
		doc.set_total_in_words = lambda: setattr(
			doc, "get", lambda field: "人民币壹佰元整" if field == "in_words" else None
		)
		frappe.get_doc.return_value = doc
		frappe.utils.cint.side_effect = lambda value: int(value) if value is not None else 0

		report = rebuild_cny_amount_in_words(doctypes=["Sales Invoice"])

		self.assertTrue(report["dry_run"])
		self.assertEqual(report["documents_changed"], 1)
		frappe.db.set_value.assert_not_called()
		frappe.db.commit.assert_not_called()

	@patch("erpnext.setup.china_money._candidate_names")
	@patch("erpnext.setup.china_money.frappe")
	def test_historical_rebuild_updates_only_derived_fields_without_modified_timestamp(
		self, frappe, candidate_names
	):
		candidate_names.return_value = ["SINV-0001", "SINV-0002"]
		frappe.get_doc.side_effect = [
			self._historical_doc("人民币壹佰元整"),
			self._historical_doc("CNY Two Hundred"),
		]
		frappe.utils.cint.side_effect = lambda value: int(value) if value is not None else 0

		report = rebuild_cny_amount_in_words(dry_run=False, doctypes=["Sales Invoice"])

		self.assertEqual(report["documents_changed"], 1)
		self.assertEqual(
			frappe.db.set_value.call_args_list,
			[call("Sales Invoice", "SINV-0002", {"in_words": "人民币壹佰元整"}, update_modified=False)],
		)
		frappe.db.commit.assert_called_once_with()

	@staticmethod
	def _historical_doc(current_words):
		doc = SimpleNamespace(doctype="Sales Invoice")
		values = {"in_words": current_words, "base_in_words": None}
		doc.get = values.get
		doc.set_total_in_words = lambda: values.update(in_words="人民币壹佰元整")
		return doc
