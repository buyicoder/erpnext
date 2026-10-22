import json
from pathlib import Path
from unittest import TestCase


class TestDashboardChartDynamicFilters(TestCase):
	def test_fiscal_year_filters_use_safe_boot_defaults(self):
		chart_files = Path(__file__).parents[1].glob("*/dashboard_chart/*/*.json")
		for chart_file in chart_files:
			chart = json.loads(chart_file.read_text())
			dynamic_filters = chart.get("dynamic_filters_json") or ""
			self.assertNotIn(
				"erpnext.utils.get_fiscal_year()",
				dynamic_filters,
				msg=str(chart_file),
			)
