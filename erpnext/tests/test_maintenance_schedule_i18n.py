from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.maintenance.doctype.maintenance_schedule import maintenance_schedule


class TestMaintenanceScheduleI18n(TestCase):
	def test_bundle_voucher_type_error_uses_fixed_translated_template(self):
		schedule = SimpleNamespace(items=[SimpleNamespace(serial_and_batch_bundle="SABB-0001")])
		template = "Serial and Batch Bundle {0} should have voucher type as {1}"

		with (
			patch.object(
				maintenance_schedule.frappe,
				"get_all",
				return_value=[SimpleNamespace(name="SABB-0001", voucher_type="Stock Entry")],
			),
			patch.object(
				maintenance_schedule,
				"_",
				side_effect=lambda message: {
					template: "序列号与批号组合 {0} 的单据类型必须为“{1}”",
					"Maintenance Schedule": "维护巡修计划",
				}.get(message, message),
			),
			patch.object(maintenance_schedule.frappe, "throw", side_effect=RuntimeError) as throw,
			self.assertRaises(RuntimeError),
		):
			maintenance_schedule.MaintenanceSchedule.validate_serial_no_bundle(schedule)

		throw.assert_called_once_with("序列号与批号组合 SABB-0001 的单据类型必须为“维护巡修计划”")
