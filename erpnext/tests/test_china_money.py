from unittest import TestCase
from unittest.mock import patch

from erpnext.setup.china_money import cny_amount_in_words, money_in_words


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
