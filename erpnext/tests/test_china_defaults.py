from unittest import TestCase

from erpnext.setup.china_defaults import CHINA_SYSTEM_DEFAULTS


class TestChinaDefaults(TestCase):
	def test_china_business_display_defaults(self):
		self.assertEqual(CHINA_SYSTEM_DEFAULTS["language"], "zh")
		self.assertEqual(CHINA_SYSTEM_DEFAULTS["currency"], "CNY")
		self.assertEqual(CHINA_SYSTEM_DEFAULTS["time_zone"], "Asia/Shanghai")
		self.assertEqual(CHINA_SYSTEM_DEFAULTS["date_format"], "yyyy-mm-dd")
		self.assertEqual(CHINA_SYSTEM_DEFAULTS["time_format"], "HH:mm:ss")
		self.assertEqual(CHINA_SYSTEM_DEFAULTS["currency_precision"], "2")
		self.assertEqual(CHINA_SYSTEM_DEFAULTS["first_day_of_the_week"], "Monday")
		self.assertEqual(CHINA_SYSTEM_DEFAULTS["rounding_method"], "Commercial Rounding")
