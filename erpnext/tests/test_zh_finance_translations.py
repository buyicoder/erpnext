from pathlib import Path
from unittest import TestCase

class TestZhFinanceTranslations(TestCase):
	def setUp(self):
		catalog = (Path(__file__).parents[1] / "locale" / "zh.po").read_text()
		self.catalog = catalog

	def test_core_finance_journey_uses_reviewed_chinese_terms(self):
		translations = {
			"Accounting Onboarding": "会计功能引导",
			"Custom Financial Statement": "自定义财务报表",
			"Configure Chart of Accounts": "配置会计科目表",
			"Review Accounts Settings": "检查会计设置",
			"View Balance Sheet": "查看资产负债表",
			"Consolidated Report": "合并财务报表",
			"Customer Ledger": "客户明细账",
			"Supplier Ledger": "供应商明细账",
			"Report View": "报表视图",
			"Account": "科目",
			"Search": "搜索",
			"Notification": "通知",
			"steps completed": "项已完成",
			"completed": "已完成",
		}

		for source, translation in translations.items():
			with self.subTest(source=source):
				self.assertIn(
					f'msgid "{source}"\nmsgstr "{translation}"',
					self.catalog,
				)
