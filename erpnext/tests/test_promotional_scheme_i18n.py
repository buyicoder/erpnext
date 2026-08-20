from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.accounts.doctype.promotional_scheme import promotional_scheme


class TestPromotionalSchemeI18n(TestCase):
	def test_required_applicable_for_field_uses_fixed_template_and_translated_label(self):
		scheme = SimpleNamespace(
			applicable_for="Customer Group",
			get=lambda fieldname: None,
		)
		template = "Field {0} is required."
		translations = {
			template: "必须填写字段“{0}”。",
			"Customer Group": "客户组",
		}
		with (
			patch.object(promotional_scheme.frappe, "scrub", return_value="customer_group"),
			patch.object(promotional_scheme.frappe, "bold", side_effect=lambda value: f"<b>{value}</b>"),
			patch.object(
				promotional_scheme,
				"_",
				side_effect=lambda message: translations.get(message, message),
			),
			patch.object(promotional_scheme.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			promotional_scheme.PromotionalScheme.validate_applicable_for(scheme)

		throw.assert_called_once_with("必须填写字段“<b>客户组</b>”。")
