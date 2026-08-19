from io import BytesIO
from pathlib import Path
from string import Formatter
from unittest import TestCase

from babel.messages.pofile import read_po

class TestZhFinanceTranslations(TestCase):
	def setUp(self):
		po_path = Path(__file__).parents[1] / "locale" / "zh.po"
		self.catalog = read_po(BytesIO(po_path.read_bytes()), locale="zh")

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
			"Set Level": "设置层级",
			"Collapse All": "全部折叠",
			"Tree Level": "树形层级",
			"Filter based on {0}": "按 {0} 筛选",
			"Execution Time: {0} sec": "执行用时：{0} 秒",
			"Home": "首页",
			"Dashboard": "仪表板",
			"Desktop": "工作台",
			"Workspaces": "工作区",
			"Session Defaults": "会话默认值",
			"Logout": "退出登录",
			"Keyboard Shortcuts": "键盘快捷键",
			"Plaid Settings": "Plaid 设置",
			"Due Date": "到期日",
			"Today": "今天",
			"Total": "合计",
		}

		for source, translation in translations.items():
			with self.subTest(source=source):
				message = self.catalog.get(source)
				self.assertIsNotNone(message)
				self.assertNotIn("fuzzy", message.flags)
				self.assertEqual(message.string, translation)
				self.assertEqual(
					self._format_fields(source),
					self._format_fields(translation),
				)

	@staticmethod
	def _format_fields(value):
		return [field for _, field, _, _ in Formatter().parse(value) if field]
