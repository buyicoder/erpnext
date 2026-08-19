# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.projects.report.project_wise_stock_tracking import project_wise_stock_tracking


class TestProjectWiseStockTracking(TestCase):
	@patch.object(project_wise_stock_tracking, "frappe")
	def test_delivery_note_and_pos_net_amounts_accumulate_by_project(self, frappe_mock):
		frappe_mock.db.sql.side_effect = [
			[SimpleNamespace(project="PROJECT-001", amount=120)],
			[SimpleNamespace(project="PROJECT-001", amount=35)],
		]

		amounts = project_wise_stock_tracking.get_delivered_items_net_amount()

		self.assertEqual(amounts, {"PROJECT-001": 155})
		self.assertEqual(frappe_mock.db.sql.call_count, 2)
