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
		}
		for source, translation in expected.items():
			with self.subTest(source=source):
				self.assertEqual(self.catalog.get(source).string, translation)
