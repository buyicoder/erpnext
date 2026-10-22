from pathlib import Path
from unittest import TestCase


class TestZhCoreTemplates(TestCase):
	def setUp(self):
		self.erpnext_root = Path(__file__).parents[1]

	def test_dashboard_and_preview_labels_use_client_template_translation(self):
		contracts = {
			"projects/doctype/project/project_dashboard.html": ('{{ __("Activity Summary") }}',),
			"manufacturing/doctype/work_order/work_order_preview.html": (
				'{{ __("Status") }}',
				'{{ __("Qty to Produce") }}',
				'{{ __("Produced Qty") }}',
			),
			"stock/dashboard/item_dashboard.html": ('{{ __("More") }}',),
			"stock/doctype/delivery_trip/dispatch_notification_template.html": (
				'{{ _("Dispatch Notification") }}',
				'{{ _("Delivery Note") }}',
				'{{ _("Driver") }}',
				'{{ _("Vehicle Number") }}',
			),
			"setup/doctype/email_digest/templates/default.html": (
				'{{ _("Item Code") }}',
				'{{ _("Quantity") }}',
				'{{ _("Rate") }}',
				'{{ _("Amount") }}',
				'{{ _("Please take necessary action") }}',
			),
		}

		for relative_path, expected_calls in contracts.items():
			source = (self.erpnext_root / relative_path).read_text()
			for expected_call in expected_calls:
				with self.subTest(path=relative_path, call=expected_call):
					self.assertIn(expected_call, source)
