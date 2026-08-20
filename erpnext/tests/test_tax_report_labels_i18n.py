from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from erpnext.accounts.report.tax_withholding_details import tax_withholding_details
from erpnext.accounts.report.tds_computation_summary import tds_computation_summary


TRANSLATIONS = {
	"Customer": "客户",
	"Customer Name": "客户名称",
	"Customer Type": "客户类型",
	"Supplier": "供应商",
	"Supplier Name": "供应商名称",
	"Supplier Type": "供应商类型",
	"Party": "往来单位",
	"Party Name": "往来单位名称",
	"Party Type": "往来类型",
}


class TestTaxReportLabelsI18n(TestCase):
	def _labels(self, report_class, party_type):
		report = object.__new__(report_class)
		report.filters = SimpleNamespace(get=lambda key: party_type)
		with patch.object(
			tax_withholding_details,
			"_",
			side_effect=lambda message: TRANSLATIONS.get(message, message),
		):
			return {column["fieldname"]: column["label"] for column in report.get_columns()}

	def test_both_reports_cover_customer_supplier_and_empty_default(self):
		reports = (
			tds_computation_summary.TDSComputationSummaryReport,
			tax_withholding_details.TaxWithholdingDetailsReport,
		)
		expected = {
			"Customer": ("客户", "客户名称", "客户类型"),
			"Supplier": ("供应商", "供应商名称", "供应商类型"),
			"": ("往来单位", "往来单位名称", "往来类型"),
		}
		for report_class in reports:
			for party_type, labels_expected in expected.items():
				with self.subTest(report=report_class.__name__, party_type=party_type):
					labels = self._labels(report_class, party_type)
					self.assertEqual(
						(labels["party"], labels["party_name"], labels["party_entity_type"]),
						labels_expected,
					)
