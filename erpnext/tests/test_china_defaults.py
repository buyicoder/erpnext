from unittest import TestCase
from unittest.mock import MagicMock, patch

from erpnext.setup import china_defaults
from erpnext.setup.china_defaults import CHINA_ADDRESS_TEMPLATE, CHINA_SYSTEM_DEFAULTS


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

	def test_china_address_template_uses_domestic_order_and_labels(self):
		self.assertLess(CHINA_ADDRESS_TEMPLATE.index("{{ state }}"), CHINA_ADDRESS_TEMPLATE.index("{{ city }}"))
		self.assertLess(CHINA_ADDRESS_TEMPLATE.index("{{ city }}"), CHINA_ADDRESS_TEMPLATE.index("{{ county }}"))
		self.assertLess(CHINA_ADDRESS_TEMPLATE.index("{{ county }}"), CHINA_ADDRESS_TEMPLATE.index("{{ address_line1 }}"))
		self.assertIn("邮编：{{ pincode }}", CHINA_ADDRESS_TEMPLATE)
		self.assertIn("电话：{{ phone }}", CHINA_ADDRESS_TEMPLATE)
		self.assertNotIn("Phone", CHINA_ADDRESS_TEMPLATE)

	def test_custom_address_template_is_not_overwritten(self):
		custom_template = MagicMock(template="用户自定义模板")
		fake_db = MagicMock()
		fake_db.exists.return_value = True
		with (
			patch.object(china_defaults.frappe, "db", fake_db),
			patch.object(china_defaults.frappe, "get_doc", return_value=custom_template),
		):
			self.assertFalse(china_defaults.ensure_china_address_template())

		custom_template.save.assert_not_called()

	def test_existing_site_preferences_are_preserved_unless_forced(self):
		system_settings = MagicMock(
			language="zh",
			time_zone="Asia/Urumqi",
			date_format="dd/mm/yyyy",
			currency_precision="4",
		)
		global_defaults = MagicMock(country="China", default_currency="CNY")
		with (
			patch.object(
				china_defaults.frappe,
				"get_single",
				side_effect=[system_settings, global_defaults],
			),
			patch.object(china_defaults, "ensure_china_address_template"),
			patch.object(china_defaults.frappe, "clear_cache"),
		):
			china_defaults.apply_china_defaults()

		system_settings.update.assert_not_called()
		system_settings.save.assert_not_called()
		global_defaults.update.assert_not_called()
		global_defaults.save.assert_not_called()

	def test_setup_can_force_china_defaults(self):
		system_settings = MagicMock(time_zone="Asia/Urumqi")
		global_defaults = MagicMock(country="Singapore", default_currency="SGD")
		with (
			patch.object(
				china_defaults.frappe,
				"get_single",
				side_effect=[system_settings, global_defaults],
			),
			patch.object(china_defaults, "ensure_china_address_template"),
			patch.object(china_defaults.frappe, "clear_cache"),
		):
			china_defaults.apply_china_defaults(force=True)

		system_settings.update.assert_called_once_with(CHINA_SYSTEM_DEFAULTS)
		global_defaults.update.assert_called_once_with({"country": "China", "default_currency": "CNY"})

	def test_current_managed_address_template_is_a_noop(self):
		template = MagicMock(template=CHINA_ADDRESS_TEMPLATE, is_default=1)
		fake_db = MagicMock()
		fake_db.exists.return_value = True
		with (
			patch.object(china_defaults.frappe, "db", fake_db),
			patch.object(china_defaults.frappe, "get_doc", return_value=template),
		):
			self.assertFalse(china_defaults.ensure_china_address_template())

		template.save.assert_not_called()
