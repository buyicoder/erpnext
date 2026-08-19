import json
from io import BytesIO
from pathlib import Path
from string import Formatter
from unittest import TestCase

from babel.messages.pofile import read_po


FRAPPE_OWNED_WORKSPACE_LABELS = {
	"Address",
	"Bulk Update",
	"Campaign",
	"Communication",
	"Contact",
	"Contacts",
	"Department",
	"Download Backups",
	"Email Account",
	"Email Group",
	"Export Data",
	"Feedback",
	"Letter Head",
	"Location",
	"Meeting",
	"Operation",
	"Print Settings",
	"Role Permissions",
	"SMS Log",
	"SMS Settings",
	"System Settings",
	"Task",
	"UTM Source",
	"User",
}


class TestZhFinanceTranslations(TestCase):
	def setUp(self):
		po_path = Path(__file__).parents[1] / "locale" / "zh.po"
		self.catalog = read_po(BytesIO(po_path.read_bytes()), locale="zh")

	def test_core_finance_journey_uses_reviewed_chinese_terms(self):
		translations = {
			"Completion percentage must be between 0 and 100": "完成百分比必须介于 0 和 100 之间",
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
			"Stock Setup": "库存功能引导",
			"Create Warehouses": "创建仓库",
			"Create Item": "创建物料",
			"Create Purchase Receipt": "创建采购入库单",
			"Create Transfer Entry": "创建调拨单",
			"View Stock Balance": "查看库存余额",
			"Review Stock Settings": "检查库存设置",
			"Brand": "品牌",
			"Warehouse": "仓库",
			"List View": "列表视图",
			"Saved Filters": "已保存的筛选条件",
			"Created On": "创建时间",
			"Item Type": "物料类型",
			"Sales & Purchase": "采销",
			"Buying Setup": "采购功能引导",
			"Selling Setup": "销售快速入门",
			"Create Customer": "创建客户",
			"View Sales Order Analysis": "查看销售订单分析",
			"Review Selling Settings": "检查销售设置",
			"Projects Setup": "项目快速入门",
			"Create Project": "创建项目",
			"View Project Summary": "查看项目概览",
			"Completed Projects": "已完成项目",
			"Non Completed Tasks": "未完成任务",
			"Delivered": "已交付",
			"Create supplier": "创建供应商",
			"Create Purchase Invoice": "创建采购发票",
			"View Purchase Order Analysis": "查看采购订单分析",
			"Review Buying Settings": "检查采购设置",
			"Draft": "草稿",
			"Submitted": "已提交",
			"Cancelled": "已取消",
			"Add {0}": "新建{0}",
			"Click to sort by {0}": "点击按{0}排序",
			"{0} of {1}": "显示 {0} 条，共 {1} 条",
			"Title": "标题",
			"Pending": "待处理",
			"Date": "日期",
			"descending": "降序",
			"Average Order Value": "平均订单金额",
			"Average Order Values": "平均订单金额",
			"Purchase Orders Count": "采购订单数量",
			"Item Wise Consumption": "按物料统计用量",
			"Stock Value by Item Group": "按物料组统计库存价值",
			"ERPNext Settings": "ERPNext 设置",
		}

		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_core_transaction_forms_use_reviewed_chinese_terms(self):
		translations = {
			"Customer Name:": "客户名称：",
			"Bill to:": "账单地址：",
			"Invoice Number:": "发票编号：",
			"Invoice Date:": "开票日期：",
			"Payment Due Date:": "付款到期日：",
			"Prepared By": "制单人",
			"Authorised Signatory": "授权签字人",
			"Received Payment as Above": "已收到上述款项",
			"A/C Payee": "仅限收款人入账",
			"Row No.": "序号",
			"Sub Total:": "小计：",
			"In Words:": "金额大写：",
			"Grand Total:": "价税合计：",
			"Amount {0} {1} adjusted against {2} {3}": "金额 {0} {1} 已冲抵 {2} {3}",
			"Amount {0} {1} as adjustment to {2}": "金额 {0} {1} 作为对 {2} 的调整",
			"Consider for Tax Withholding ": "计入代扣税计算",
			"Grand Total (Company Currency": "总计（本币）",
			"Material Request already created for the ordered quantity": "已按订购数量创建物料需求",
			"Payment methods refreshed. Please review before proceeding.": "付款方式已刷新，请核对后继续。",
			"Please save the Sales Order before adding a delivery schedule.": "请先保存销售订单，再添加交付计划。",
			"Purchase Invoice without any outstanding amount cannot be held.": "没有未结金额的采购发票不能暂停付款。",
			"Return Purchase Invoice cannot be held.": "采购退货发票不能暂停付款。",
			"Reversal Of Exchange Rate Revaluation": "汇率重估冲销",
			"Sales Order {0} is not available for production": "销售订单 {0} 当前不可用于生产",
			"Set Supplier": "设置供应商",
			"Source warehouse required for stock item {0}": "库存物料 {0} 必须填写发料仓",
			"Supplier Required": "必须填写供应商",
			"Supplier is required for all selected Items": "所有选中物料都必须填写供应商",
			"Timesheet {0} cannot be invoiced in its current state": "工时表 {0} 当前状态无法开票",
			"UTM Analytics": "营销来源分析",
			"{0} {1} is blocked and on hold until {2}.": "{0} {1} 已被冻结，暂停至 {2}。",
			"{0} {1} is blocked.": "{0} {1} 已被冻结。",
		}

		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_workspace_metrics_and_navigation_use_reviewed_chinese_terms(self):
		translations = {
			"AP Summary": "应付账款汇总",
			"AR Summary": "应收账款汇总",
			"Active Subcontracted Items": "在制委外物料",
			"Bank Reconciliation": "银行对账",
			"Budget Variance": "预算差异",
			"Deduction Certificate": "低税率扣除证明",
			"Feedback Template": "反馈模板",
			"Inward Order": "委外入库订单",
			"Item-wise sales Register": "物料销售台账",
			"Items To Be Received": "待收货委外成品",
			"Manufactured Items Value": "完工物料价值",
			"Material Planning": "物料计划",
			"Materials To Be Transferred": "待调拨委外原材料",
			"Outward Order": "委外发料订单",
			"Quality Inspections": "质检单",
			"Reconciliation Statement": "银行对账单",
			"Subcontracting Inward Order Count": "委外入库订单数量",
			"Subcontracting Outward Order": "委外发料订单",
			"Subcontracting Outward Order Count": "委外发料订单数量",
			"Tax Template": "税费模板",
			"WIP Work Orders": "在制工单",
		}

		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_every_erpnext_workspace_label_has_a_translation_owner(self):
		erpnext_root = Path(__file__).parents[1]
		workspace_files = list(erpnext_root.glob("**/workspace/**/*.json"))
		workspace_files.extend(erpnext_root.glob("workspace_sidebar/*.json"))
		label_sources = {}

		def collect_labels(value, source):
			if isinstance(value, dict):
				for key, child in value.items():
					if key in {"label", "title"} and isinstance(child, str):
						label_sources.setdefault(child, set()).add(str(source.relative_to(erpnext_root)))
					collect_labels(child, source)
			elif isinstance(value, list):
				for child in value:
					collect_labels(child, source)

		for workspace_file in workspace_files:
			collect_labels(json.loads(workspace_file.read_text()), workspace_file)

		missing = {}
		for label, sources in sorted(label_sources.items()):
			if label in FRAPPE_OWNED_WORKSPACE_LABELS:
				continue
			message = self.catalog.get(label)
			if not message or not message.string or "fuzzy" in message.flags:
				missing[label] = sorted(sources)

		self.assertEqual(missing, {})

	def test_master_data_uses_reviewed_chinese_terms(self):
		translations = {
			"Alias": "别名",
			"Allow purchase invoice creation without purchase order": "允许不经采购订单直接创建采购发票",
			"Allow purchase invoice creation without purchase receipt": "允许不经采购入库单直接创建采购发票",
			"Allow sales invoice creation without delivery note": "允许不经送货单直接创建销售发票",
			"Allow sales invoice creation without sales order": "允许不经销售订单直接创建销售发票",
			"Allowed to transact with": "允许交易的公司",
			"Credit & Overdue Limits": "信用与逾期额度",
			"Customer POS ID": "客户 POS 编号",
			"Internal Customer Accounting": "内部客户核算",
			"Invalid Customer Group": "无效的客户组",
			"Overdue Limit Crossed": "已超过逾期额度",
			"Determines which tax rules apply to this supplier": "确定适用于该供应商的税务规则",
			"General information about your Supplier": "供应商基本信息",
			"Internal Supplier Details": "供应商内部信息",
			"Per-Company Accounts": "分公司核算科目",
			"Primary Address Preview": "主要地址预览",
			"RFQ and Purchase Order Settings": "询价与采购订单设置",
			"Tax Identification": "税务识别信息",
			"Used for inter-company transactions": "用于公司间交易",
			"For project - {0}, update your status": "请更新项目 {0} 的状态",
			"On hold": "已暂停",
		}

		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_core_master_data_catalogs_have_no_empty_messages(self):
		targets = ("customer", "supplier", "item", "project")
		for target in targets:
			messages = [
				message
				for message in self.catalog
				if message.id
				and not isinstance(message.id, tuple)
				and any(f"/doctype/{target}/" in filename for filename, _ in message.locations)
			]
			empty_messages = [message.id for message in messages if not message.string]
			self.assertEqual(empty_messages, [], f"Untranslated {target} messages")
			invalid_messages = {
				message.id: [str(error) for error in message.check()]
				for message in messages
				if message.string and message.check()
			}
			self.assertEqual(invalid_messages, {}, f"Invalid {target} translations")

	def _assert_translation(self, source, translation):
		with self.subTest(source=source):
			message = self.catalog.get(source)
			self.assertIsNotNone(message)
			self.assertNotIn("fuzzy", message.flags)
			self.assertEqual(message.string, translation)
			self.assertEqual(message.check(), [])
			self.assertEqual(
				self._format_fields(source),
				self._format_fields(translation),
			)

	@staticmethod
	def _format_fields(value):
		return [field for _, field, _, _ in Formatter().parse(value) if field]
