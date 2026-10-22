from io import BytesIO
from pathlib import Path
from unittest import TestCase

from babel.messages.pofile import read_po


class TestZhFrappeTranslations(TestCase):
	def setUp(self):
		po_path = Path(__file__).parents[2] / "localization" / "frappe" / "zh.po"
		self.catalog = read_po(BytesIO(po_path.read_bytes()), locale="zh")

	def test_public_component_catalog_is_complete_and_valid(self):
		messages = [message for message in self.catalog if message.id]
		self.assertGreaterEqual(len(messages), 480)
		self.assertEqual([message.id for message in messages if not message.string], [])
		self.assertEqual(
			{
				message.id: [str(error) for error in message.check()]
				for message in messages
				if message.check()
			},
			{},
		)

	def test_critical_public_actions_use_reviewed_terms(self):
		expected = {
			"Save": "保存",
			"Cancel": "取消",
			"Submit": "提交",
			"Search": "搜索",
			"Filter": "筛选",
			"Permissions": "权限",
			"Add a Row": "新增一行",
			"No Results found": "未找到结果",
			"Begin typing for results.": "输入关键词搜索。",
			"Framework": "系统管理",
			"Filter based on {0}": "按 {0} 筛选",
			"Last Edited By You": "最后由你编辑",
			"Last Edited By {0}": "最后由 {0} 编辑",
			"Created By You": "由你创建",
			"Created By {0}": "由 {0} 创建",
			"System User": "系统用户",
			"Website User": "网站用户",
			"Audits": "审计",
			"Customize Quick Filters": "自定义快捷筛选条件",
			"Open Link": "打开链接",
			"Current Series": "当前编号",
			"Transaction": "单据类型",
			"Please select a transaction.": "请选择单据类型。",
			"All Results": "全部结果",
			"Preferences": "偏好设置",
			"Manage your preferences": "管理偏好设置",
			"Copied {0} {1} to clipboard": "已将 {0} {1} 复制到剪贴板",
			"Desktop": "工作台",
			"DocType Missing": "缺少单据类型",
			"Edit Sidebar": "编辑侧边栏",
			"No rows selected": "未选择任何行",
			"Not permitted. {0}.": "无权执行此操作。{0}。",
			"Open in new tab": "在新标签页中打开",
			"Please select a DocType in options before setting filters": "设置筛选条件前，请先在选项中选择单据类型",
			"Saving Changes...": "正在保存更改……",
			"Saving Sidebar": "正在保存侧边栏",
			"XMLHttpRequest Error": "网络请求错误",
			"esc": "Esc",
			"to close": "关闭",
			"to navigate": "导航",
			"to select": "选择",
		}
		for source, translation in expected.items():
			with self.subTest(source=source):
				message = self.catalog.get(source)
				self.assertNotIn("fuzzy", message.flags)
				self.assertEqual(message.string, translation)

	def test_contextual_number_fallback_is_not_mislabeled(self):
		expected = {
			("N/A", "Number not available"): "暂无数值",
			("1 row from {0}", "User removed row from child table"): "从 {0} 移除 1 行",
			("1 row to {0}", "User added row to child table"): "向 {0} 添加 1 行",
			("{0} rows from {1}", "User removed rows from child table"): "从 {1} 移除 {0} 行",
			("{0} rows to {1}", "User added rows to child table"): "向 {1} 添加 {0} 行",
		}
		for (source, context), translation in expected.items():
			with self.subTest(source=source, context=context):
				message = self.catalog.get(source, context=context)
				self.assertIsNotNone(message)
				self.assertNotIn("fuzzy", message.flags)
				self.assertEqual(message.string, translation)
