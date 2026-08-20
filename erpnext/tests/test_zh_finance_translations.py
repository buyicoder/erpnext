import ast
import json
import os
import re
from io import BytesIO
from pathlib import Path
from string import Formatter
from tempfile import TemporaryDirectory
from unittest import TestCase

from babel.messages.pofile import read_po

from scripts.merge_frappe_zh_catalog import merge_catalogs
from scripts.merge_erpnext_zh_banking import merge_banking_catalog


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

CORE_BUSINESS_DOCTYPES = {
	"BOM",
	"BOM Creator",
	"Customer",
	"Delivery Note",
	"Item",
	"Journal Entry",
	"Job Card",
	"Landed Cost Voucher",
	"Material Request",
	"Manufacturing Settings",
	"Opportunity",
	"Payment Entry",
	"Pick List",
	"POS Closing Entry",
	"POS Invoice",
	"POS Invoice Merge Log",
	"POS Opening Entry",
	"POS Profile",
	"Project",
	"Project Update",
	"Purchase Invoice",
	"Purchase Order",
	"Purchase Receipt",
	"Quality Inspection",
	"Quality Inspection Template",
	"Request for Quotation",
	"Sales Invoice",
	"Sales Order",
	"Serial and Batch Bundle",
	"Serial No",
	"Stock Reconciliation",
	"Stock Entry",
	"Supplier",
	"Supplier Quotation",
	"Batch",
	"Timesheet",
	"Task",
	"Activity Cost",
	"Activity Type",
	"Work Order",
}

CORE_ACCOUNTING_MASTER_DOCTYPES = {
	"Account",
	"Bank Account",
	"Cost Center",
	"Currency Exchange",
	"Customer Group",
	"Item Group",
	"Item Price",
	"Mode of Payment",
	"Payment Terms Template",
	"Price List",
	"Purchase Taxes and Charges Template",
	"Sales Taxes and Charges Template",
	"Supplier Group",
	"UOM",
	"UOM Category",
	"Warehouse",
}

CORE_OPERATIONAL_MASTER_DOCTYPES = {
	"Accounting Dimension",
	"Activity Type",
	"Asset",
	"Asset Capitalization",
	"Asset Depreciation Schedule",
	"Asset Maintenance",
	"Asset Maintenance Log",
	"Asset Movement",
	"Asset Repair",
	"Asset Value Adjustment",
	"Bank",
	"Bank Clearance",
	"Bank Statement Import",
	"Bank Statement Import Log",
	"Bank Transaction",
	"Bank Transaction Rule",
	"Branch",
	"Brand",
	"Budget",
	"Buying Settings",
	"Department",
	"Dunning",
	"Employee",
	"Finance Book",
	"Fiscal Year",
	"Loyalty Program",
	"Payment Reconciliation",
	"Payment Request",
	"Payment Term",
	"Pricing Rule",
	"Project Template",
	"Project Type",
	"Promotional Scheme",
	"Sales Partner",
	"Sales Person",
	"Selling Settings",
	"Shipping Rule",
	"Stock Reposting Settings",
	"Stock Settings",
	"Repost Item Valuation",
	"Repost Accounting Ledger",
	"Task Type",
	"Territory",
	"Transaction Deletion Record",
}

CHINA_COMPLIANCE_DOCTYPES = {
	"Account Closing Balance",
	"Accounting Period",
	"Accounts Settings",
	"Advance Taxes and Charges",
	"Cashier Closing",
	"Company",
	"Item Tax Template",
	"POS Closing Entry",
	"Period Closing Voucher",
	"Process Period Closing Voucher",
	"Purchase Taxes and Charges Template",
	"Sales Taxes and Charges Template",
	"Stock Closing Balance",
	"Stock Closing Entry",
	"Tax Category",
	"Tax Rule",
	"Tax Withholding Category",
	"Tax Withholding Entry",
	"Tax Withholding Group",
	"Tax Withholding Rate",
}

# These are literal field descriptions, not printf templates. Babel infers the
# leading "% o" as a printf placeholder even though Frappe never interpolates it.
BABEL_LITERAL_PERCENT_MESSAGES = {
	"% of materials delivered against this Pick List",
	"% Finished Item Quantity",
	"Row #{0}: Process Loss Percentage should be less than 100% for {1} Item {2}",
	"% of materials billed against this Sales Order",
	"% of materials delivered against this Sales Order",
	"Progress % for a task cannot be more than 100.",
	"Check if this tax is not applicable to items (distinct from 0% rate)",
	"In this case, the amount will be calculated as 25% of the transaction amount. If the transaction amount is 200, then this will be calculated as 200 * 0.25 = 50.",
	"{0}% of total invoice value will be given as discount.",
	"Maximum discount % allowed when selling this item. Eg: if set to 20%, a discount greater than 20% cannot be applied in sales transactions.",
}

ERPNext_IDENTITY_TRANSLATION_ALLOWLIST = {
	"0-30",
	"1-10",
	"1000+",
	"11-50",
	"1{0}",
	"201-500",
	"30-60",
	"501-1000",
	"51-200",
	"60-90",
	"<0",
	'<div class="text-muted text-center">{0}</div>',
	'<div id="stock-levels-placeholder"></div>',
	'<div id=\\"item-prices-container\\"></div>',
	"<li>{}</li>",
	"A - B",
	"A - C",
	"A4",
	"A+",
	"A-",
	"AB-",
	"AB+",
	"ACC-PINV-.YYYY.-",
	"API",
	"B-",
	"B+",
	"D - E",
	"DFS",
	"EAN",
	"EAN-13",
	"EAN-8",
	"ERPNext",
	"Frappe CRM",
	"G - D",
	"GTIN-14",
	"H - F",
	"I - J",
	"I - K",
	"IBAN",
	"IRS 1099",
	"ISBN-10",
	"ISBN-13",
	"Lft",
	"JAN",
	"O-",
	"O+",
	"POS",
	"Rgt",
	"Sazhen",
	"Skype ID",
	"Slug",
	"UPC-A",
	"URL",
	"WhatsApp",
	"frankfurter.dev",
	"frankfurter.dev - v2",
	"rgt",
	"{0}%",
	"{0} {1}",
	"{}",
}

ERPNext_APPROVED_NON_CJK_TRANSLATIONS = {
	"{0} for {1}": "{0}（{1}）",
}


class TestZhFinanceTranslations(TestCase):
	maxDiff = None

	@classmethod
	def setUpClass(cls):
		po_path = Path(__file__).parents[1] / "locale" / "zh.po"
		cls.catalog = read_po(BytesIO(po_path.read_bytes()), locale="zh")
		pot_path = Path(__file__).parents[1] / "locale" / "main.pot"
		cls.source_catalog = read_po(BytesIO(pot_path.read_bytes()), locale="en")
		repo_root = Path(__file__).parents[2]
		frappe_baseline_path = repo_root / ".build/frappe-v16.24.4-zh.po"
		frappe_runtime_pot_path = repo_root / ".build/frappe-v16.31.0-main.pot"
		cls.frappe_runtime_catalog = read_po(
			BytesIO(frappe_runtime_pot_path.read_bytes()), locale="zh"
		)
		with TemporaryDirectory() as temporary_directory:
			merged_erpnext_path = Path(temporary_directory) / "erpnext-zh-merged.po"
			merge_banking_catalog(
				po_path,
				repo_root / "localization/erpnext/zh_banking.json",
				merged_erpnext_path,
			)
			cls.merged_erpnext_catalog = read_po(
				BytesIO(merged_erpnext_path.read_bytes()), locale="zh"
			)
			merged_path = Path(temporary_directory) / "frappe-zh-merged.po"
			merge_catalogs(
				frappe_baseline_path,
				repo_root / "localization/frappe/zh.po",
				merged_path,
			)
			cls.merged_frappe_catalog = read_po(BytesIO(merged_path.read_bytes()), locale="zh")

	def test_every_banking_translation_key_has_a_runtime_owner(self):
		repo_root = Path(__file__).parents[2]
		keys = json.loads((repo_root / "banking/translation-keys.json").read_text())
		technical_literals = {"0.00"}
		missing = []
		for source in keys:
			if source in technical_literals:
				continue
			messages = [
				self.merged_erpnext_catalog.get(source),
				self.merged_frappe_catalog.get(source),
			]
			if not any(
				message
				and message.string
				and "fuzzy" not in message.flags
				and self._message_is_valid(message)
				for message in messages
			):
				missing.append(source)
		self.assertEqual(missing, [])

	def test_every_erpnext_source_message_has_a_chinese_runtime_owner(self):
		from babel.messages.extract import extract_from_dir
		from frappe.gettext.translate import PYTHON_KEYWORDS, get_method_map

		repo_root = Path(__file__).parents[2]
		erpnext_source_root = repo_root / "erpnext"
		method_map = get_method_map("erpnext")
		method_map.extend(get_method_map("frappe"))

		def include_directory(path):
			name = os.path.basename(path)
			return not name.startswith(".") and name not in {"__pycache__", "locale", "node_modules"}

		source_messages = {}
		for filename, line, message_id, _comments, context in extract_from_dir(
			erpnext_source_root,
			method_map,
			directory_filter=include_directory,
			keywords=PYTHON_KEYWORDS,
		):
			if (
				message_id
				and not (isinstance(message_id, str) and not message_id.strip())
			):
				source_messages.setdefault((message_id, context), []).append(
					(f"erpnext/{filename}", line)
				)

		missing = []
		for (message_id, context), locations in source_messages.items():
			owners = [
				self.merged_erpnext_catalog.get(message_id, context=context),
				self.merged_frappe_catalog.get(message_id, context=context),
			]
			if not any(self._is_usable_translation(message, message_id) for message in owners):
				missing.append(
					{
						"id": message_id,
						"context": context,
						"locations": locations,
					}
				)
		self.assertEqual(missing, [])

	def test_remaining_erpnext_source_messages_use_reviewed_chinese(self):
		translations = {
			"<li>Item {0} in row(s) {1} billed more than {2}</li>": "<li>物料 {0} 在第 {1} 行的开票金额超过 {2}</li>",
			"Accounts cannot be removed, as user doesn't have access to all the accounts of {0}": "无法移除科目，因为用户无权访问 {0} 的全部科目",
			"Appointment has been closed. Please book the appointment again.": "预约已关闭，请重新预约。",
			"Appointment is already verified.": "预约已经验证。",
			"BOM Explorer": "物料清单浏览器",
			"Body": "正文",
			"Completed Quantity ({0}), Pending Quantity ({1}) and Process Loss Quantity ({2}) must add up to the Qty to Manufacture ({3}).": "完成数量（{0}）、待处理数量（{1}）与制程损耗数量（{2}）之和必须等于生产数量（{3}）。",
			"Completed Quantity cannot be greater than {0}": "完成数量不能大于 {0}",
			"Completed, Pending and Process Loss quantities must add up to this.": "完成数量、待处理数量与制程损耗数量之和必须等于此数量。",
			"Company {0} is not in South Africa.": "公司 {0} 不在南非。",
			"Defense": "国防",
			"Importing Code Lists from remote URLs is not allowed.": "不允许从远程网址导入代码列表。",
			"Invalid Upload": "上传内容无效",
			"Folio no.": "登记册编号",
			"Job Card {0}: As per the sequence of the operations in the work order {1}, submit the manufacturing entry for the operation {2} before the operation {3}.": "生产任务单 {0}：请按生产工单 {1} 的工序顺序，先提交工序 {2} 的生产入库单，再处理工序 {3}。",
			"Logo": "标志",
			"Manage": "管理",
			"Modified By": "修改人",
			"No.": "编号",
			"No file uploaded or URL provided.": "未上传文件，也未提供网址。",
			"Please set Fiscal Code for the customer '%s'": "请为客户“%s”设置税务代码",
			"Please set Fiscal Code for the public administration '%s'": "请为公共管理机构“%s”设置税务代码",
			"Please set Tax ID for the customer '%s'": "请为客户“%s”设置税号",
			"Please set an Address on the Company '%s'": "请为公司“%s”设置地址",
			"Process Loss Quantity": "制程损耗数量",
			"Process Loss Quantity cannot be greater than {0}": "制程损耗数量不能大于 {0}",
			"Qty left for a later cycle or for another job card.": "留待后续轮次或其他生产任务单处理的数量。",
			"Qty scrapped in this cycle, nobody will produce it.": "本轮已报废且不再生产的数量。",
			"Qty to Manufacture in this Cycle": "本轮生产数量",
			"Row #{0}: FG / Semi FG Item is required for the operation {1} as 'Track Semi Finished Goods' is enabled.": "第 {0} 行：已启用“追踪半成品”，因此工序 {1} 必须设置成品/半成品物料。",
			"Row #{0}: The operation {1} has 'Is Final Finished Good' checked, so its FG / Semi FG Item must be {2}.": "第 {0} 行：工序 {1} 已勾选“最终成品”，因此其成品/半成品物料必须为 {2}。",
			"Set this value to 0 to disable the feature.": "将此值设为 0 可停用该功能。",
			"Started a background job to create {1} {0}. {2}": "已启动后台任务，将创建 {1} 个{0}。{2}",
			"The company {0} is not in South Africa. VAT Audit Report is only available for companies in South Africa.": "公司 {0} 不在南非。增值税审计报表仅适用于南非公司。",
			"The company {0} is not in United Arab Emirates. UAE VAT 201 report is only available for companies in United Arab Emirates.": "公司 {0} 不在阿拉伯联合酋长国。阿联酋 VAT 201 报表仅适用于阿联酋公司。",
			"The uploaded file could not be parsed as a genericode XML document.": "无法将上传的文件解析为 genericode XML 文档。",
			"The Job Card {0} has only {1} left to produce, but this entry books {2} ({3} finished goods and {4} process loss). Cancel or update its other manufacture entries first.": "生产任务单 {0} 仅剩 {1} 待生产，但本单据登记了 {2}（成品 {3}、制程损耗 {4}）。请先取消或更新该任务单的其他生产入库单。",
			"The completed quantity {0} of an operation {1} cannot be greater than the manufactured quantity {2} of a previous operation {3}. Submit the manufacturing entry for the operation {3} first.": "完成数量 {0}（工序 {1}）不能大于生产数量 {2}（上一工序 {3}）。请先提交工序 {3} 的生产入库单。",
			"This email was sent from {0}": "此邮件由 {0} 发送",
			"This link is valid for {0} minutes": "此链接在 {0} 分钟内有效",
			"This module is scheduled for deprecation and will be completely removed in version 17, please use <a href=\"https://frappe.io/helpdesk\">Frappe Helpdesk</a> instead.": "此模块计划弃用，并将在版本 17 中完全移除，请改用 <a href=\"https://frappe.io/helpdesk\">Frappe Helpdesk</a>。",
			"This verification link is invalid. Please book the appointment again.": "此验证链接无效，请重新预约。",
			"Verification link has expired.": "验证链接已过期。",
			"Stage": "阶段",
			"Total Completed Qty ({0}), Process Loss Qty ({1}) and Pending Qty ({2}) must add up to the Qty to Manufacture ({3}).": "完成数量（{0}）、制程损耗数量（{1}）与待处理数量（{2}）之和必须等于生产数量（{3}）。",
			"Used": "已使用",
			"We look forward to meeting you": "期待与您见面",
			"Youtube ID": "YouTube 标识",
			"{0} for {1}": "{0}（{1}）",
			"Your email has been verified and your appointment has been confirmed for {0}": "您的邮箱已验证，预约时间已确认为 {0}",
			"{0} creation for the following records will be skipped.": "将跳过为以下记录创建{0}。",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)
			self._assert_erpnext_runtime_translation(source, translation)

	def test_reviewed_core_visible_sinks_use_translation_helpers(self):
		repo_root = Path(__file__).parents[2]
		contracts = {
			"erpnext/accounts/doctype/process_statement_of_accounts/process_statement_of_accounts.js":
				'frappe.throw(__("Enter {0} name.", [__(frm.doc.customer_collection)]));',
			"erpnext/buying/doctype/purchase_order/purchase_order.js":
				'frappe.msgprint(__("Splitting {0} units of {1}", [qty, d.item_code]));',
			"erpnext/selling/doctype/sales_order/sales_order.js":
				'message: __("Please select Items from the Table"),',
			"erpnext/selling/page/point_of_sale/pos_payment.js":
				'this.addl_dlg.primary_action_label = __("Submit");',
			"erpnext/stock/doctype/delivery_trip/delivery_trip.js": [
				'message: __("Calculating Arrival Times"),',
				'message: __("Optimizing Route"),',
			],
			"erpnext/stock/page/warehouse_capacity_summary/warehouse_capacity_summary.html":
				'title="{{ __("Occupied Qty") }}: {{ d.actual_qty }}"',
		}
		for relative_path, expected in contracts.items():
			text = (repo_root / relative_path).read_text()
			for snippet in expected if isinstance(expected, list) else [expected]:
				self.assertIn(snippet, text, relative_path)

	def test_core_finance_journey_uses_reviewed_chinese_terms(self):
		translations = {
			"Calculating Arrival Times": "正在计算预计到达时间",
			"Enter {0} name.": "请输入{0}名称。",
			"Occupied Qty": "已占用数量",
			"Optimizing Route": "正在优化路线",
			"Please select Items from the Table": "请从表格中选择物料",
			"Splitting {0} units of {1}": "正在按 {0} 个单位拆分 {1}",
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
			"Advance Paid (Company Currency)": "已付预付款（本位币）",
			"Series": "编号规则",
			"References": "关联资料",
			"Margin": "利润空间",
			"Automation": "自动化",
			"Variants": "变体",
			"Partially Billed": "部分开票",
			"Task Progress": "任务进度",
			"Co-Product": "联产品",
			"By-Product": "副产品",
			"Scrap": "废料",
			"Additional Finished Good": "额外成品",
			"% of materials billed against this Sales Order": "销售订单中已开票物料的百分比",
			"% of materials delivered against this Sales Order": "销售订单中已交付物料的百分比",
			"Source Stock Entry (Manufacture)": "来源生产入库单",
			"Overdue Limit": "逾期额度",
			"New Sales Invoices are blocked when the customer's overdue amount exceeds this. Requires 'Restrict Customer Over Billing' in Accounts Settings.": "客户逾期金额超过此额度时，将禁止新建销售发票。需在会计设置中启用“限制客户超额开票”。",
			"Bypass credit limit check at sales order": "销售订单跳过信用额度检查",
			"Enter the Item Code that this customer uses at their end. This will be shown in Sales Orders for the customer's reference.": "填写客户使用的物料编码；该编码会显示在销售订单中供客户核对。",
			"Default price list for buying or selling this item": "该物料采购或销售时默认使用的价格表",
			"Cost center used for tracking purchase expenses for this item": "用于归集该物料采购费用的成本中心",
			"This supplier will be auto-selected in new purchase transactions": "新建采购单据时将自动选择此供应商",
			"Account where the cost of this item will be debited on purchase": "采购该物料时用于借记成本的科目",
			"Cost center used for tracking sales revenue for this item": "用于归集该物料销售收入的成本中心",
			"Account where revenue from selling this item will be credited": "销售该物料时用于贷记收入的科目",
			"Provisional liability account used for service items before invoice is received": "服务类物料在收到发票前使用的暂估负债科目",
			"Account where cost of goods sold will be posted when this item is sold": "销售该物料时结转销售成本所使用的科目",
			"Expenses Added To Stock Account": "计入存货的费用科目",
			"Account to track value added to stock via Stock Entry, Stock Reconciliation or Landed Cost Voucher": "用于核算通过库存单、库存盘点或到岸成本单计入存货价值的科目",
			"Expenses Added To Stock Contra Account": "计入存货费用的对方科目",
			"Used to balance the books when recording expenses added to stock": "记录计入存货的费用时用于平衡账务的对方科目",
			"Stock account where inventory value for this item will be tracked": "用于核算该物料库存价值的存货科目",
			"Check Availability in Warehouse": "检查仓库可用量",
			"Has Operating Cost": "包含运营成本",
			"Delivered by Supplier": "由供应商交付",
			"Allocate Full Amount to Stock Items": "全部分摊至库存物料",
			"If checked, the entire amount (e.g. Freight) is allocated to the valuation of stock & asset items only. If unchecked, the amount is distributed across all items and the portion belonging to non-stock items is not added to valuation.": "勾选后，全部金额（如运费）仅分摊至库存物料和资产物料的估值；未勾选时，金额按全部物料分摊，其中非库存物料对应的部分不计入估值。",
			"BOM Secondary Item": "物料清单副产品",
			"Is Legacy Scrap Item": "旧版废料物料",
			"Transaction from which tax is withheld": "发生税款扣缴的来源交易",
			"Transaction for which tax is withheld": "被扣缴税款所对应的交易",
			"Created By Migration": "由数据迁移创建",
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
			"Enter Company Details": "填写公司信息",
			"Assets Setup": "资产功能引导",
			"Learn Asset": "了解资产管理",
			"Create Asset Category": "创建资产类别",
			"Create Asset Item": "创建资产物料",
			"Create Asset Location": "创建资产地点",
			"Create Existing Asset": "录入现有资产",
			"Manufacturing Setup": "生产功能引导",
			"Create Raw Material": "创建原材料",
			"Create Raw Materials": "创建原材料",
			"Create Finished Good": "创建成品",
			"Create Finished Goods": "创建成品",
			"Create Operation": "创建工序",
			"Create Operations": "创建工序",
			"Create Bill of Materials": "创建物料清单",
			"Create Work Order": "创建生产工单",
			"View Work Order Summary": "查看工单进度追踪表",
			"View Work Order Summary Report": "查看工单进度追踪表",
			"Work Order Summary Report": "工单进度追踪表",
			"Review Manufacturing Settings": "检查生产设置",
		}

		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_core_onboarding_has_no_untranslated_visible_copy(self):
		erpnext_root = Path(__file__).parents[1]
		roots = (
			erpnext_root / "assets/module_onboarding",
			erpnext_root / "assets/onboarding_step",
			erpnext_root / "buying/module_onboarding",
			erpnext_root / "buying/onboarding_step",
			erpnext_root / "manufacturing/module_onboarding",
			erpnext_root / "manufacturing/onboarding_step",
			erpnext_root / "selling/module_onboarding",
			erpnext_root / "selling/onboarding_step",
		)
		visible_keys = ("title", "action_label", "report_description")
		missing = []

		for root in roots:
			for path in sorted(root.glob("**/*.json")):
				data = json.loads(path.read_text())
				for key in visible_keys:
					source = data.get(key)
					if not isinstance(source, str) or not source.strip():
						continue
					message = self.catalog.get(source)
					if not message or not message.string or "fuzzy" in message.flags:
						missing.append(f"{path.relative_to(erpnext_root)}:{key}:{source}")

		self.assertEqual(missing, [])

	def test_selling_and_buying_entry_points_use_reviewed_chinese_terms(self):
		translations = {
			"A disabled Product Bundle cannot be selected in transactions.": "已禁用的套件不能用于交易。",
			"Create delivery note": "创建销售出库",
			"Items not found.": "未找到物料。",
			"Onboarding for Stock!": "库存功能引导",
			"Quantity Available": "可用数量",
			"View Stock Balance Report": "查看库存余额报表",
			"Create Supplier": "创建供应商",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_core_business_source_locations_have_chinese_translations(self):
		prefixes = (
			"erpnext/accounts/",
			"erpnext/selling/",
			"erpnext/buying/",
			"erpnext/crm/",
			"erpnext/controllers/",
			"erpnext/stock/",
			"erpnext/public/",
			"erpnext/setup/",
			"erpnext/manufacturing/",
			"erpnext/subcontracting/",
		)
		missing = []
		for source_message in self.source_catalog:
			locations = [path for path, _line in source_message.locations if path.startswith(prefixes)]
			if not locations:
				continue
			source_id = source_message.id[0] if isinstance(source_message.id, tuple) else source_message.id
			if not source_id.strip():
				continue
			message = self.catalog.get(source_id, context=source_message.context)
			if message is None:
				missing.append(f"{','.join(locations)}:{source_message.context or ''}:{source_id}")
				continue
			translations = message.string if isinstance(message.string, tuple) else (message.string,)
			if (
				any(not translation for translation in translations)
				or "fuzzy" in message.flags
				or not self._message_is_valid(message)
			):
				missing.append(f"{','.join(locations)}:{message.context or ''}:{message.id}")

		self.assertEqual(missing, [])

	def test_crm_workflows_use_reviewed_chinese_terms(self):
		translations = {
			"'Verification Link Expiry Duration' must be between 15 to 60 minutes.": "“验证链接有效时长”必须设置为 15 至 60 分钟。",
			"A verified appointment cannot be moved back to 'Unverified' status.": "已验证的预约不能恢复为“未验证”状态。",
			"Action for Expired Unverified Appointments": "未验证预约过期后的处理方式",
			"Advance Booking Days is mandatory for Appointment Scheduling.": "启用预约安排时必须设置可提前预约天数。",
			"Allowed Users": "允许的用户",
			"Allowed Users is not required as Frappe CRM is already installed on the site.": "本站点已安装 Frappe CRM，无需设置允许的用户。",
			"Allowed Users is required for data synchronization from remote Frappe CRM site.": "从远程 Frappe CRM 站点同步数据时必须设置允许的用户。",
			"An appointment booked through the portal can only be opened via email verification.": "通过门户预约后，必须完成邮件验证才能打开该预约。",
			"Appointment Booking Portal Settings": "预约门户设置",
			"Appointment Confirmed": "预约已确认",
			"Appointment Scheduling": "预约安排",
			"Appointment Scheduling needs to be enabled for Appointment Booking through portal.": "通过门户提供预约服务前，必须启用预约安排。",
			"Appointment can only be scheduled up to {0} day(s) in advance.": "最多只能提前 {0} 天安排预约。",
			"Appointment cannot be scheduled for a past time.": "不能将预约安排在过去的时间。",
			"Appointment cannot be scheduled on a holiday.": "不能在节假日安排预约。",
			"Appointment must be scheduled within the available slot timings.": "预约必须安排在可用时段内。",
			"Appointments created manually cannot have 'Unverified' status.": "手动创建的预约不能设为“未验证”状态。",
			"Campaign {0} not found": "未找到营销活动 {0}",
			"Cannot enable Opportunity creation from Contact Us because the Contact Us form is disabled.": "“联系我们”表单已停用，无法启用由该表单创建商机。",
			"Created through Portal": "通过门户创建",
			"Delete Permanently": "永久删除",
			"Email Campaign Error": "邮件营销活动错误",
			"Email Campaign Send Error": "邮件营销活动发送错误",
			"Email Verified": "邮件已验证",
			"Enable Appointment Booking Through Portal": "启用门户预约",
			"Enable Frappe CRM Data Synchronization": "启用 Frappe CRM 数据同步",
			"Enable Opportunity Creation from Contact Us": "允许通过“联系我们”创建商机",
			"Failed to send email for campaign {0} to {1}": "为营销活动 {0} 向 {1} 发送邮件失败",
			"Frappe CRM Allowed User": "Frappe CRM 允许的用户",
			"Frappe CRM data synchronization is not enabled on ERPNext. Contact System Manager of ERPNext.": "ERPNext 尚未启用 Frappe CRM 数据同步，请联系 ERPNext 系统管理员。",
			"Holiday List - {0} is not valid for current date.": "节假日列表 {0} 当前未生效。",
			"In Minutes (min: 15 mins, max: 60 mins)": "单位：分钟（最少 15 分钟，最多 60 分钟）",
			"Mark as Closed": "标记为已关闭",
			"No availability of slots are found. Please add on Appointment Booking Settings.": "未找到可用时段，请在预约设置中添加。",
			"No email found for {0} {1}": "未找到{0} {1}的电子邮箱",
			"No recipients found for campaign {0}": "未找到营销活动 {0} 的收件人",
			"Please add a valid Holiday List on Appointment Booking Settings.": "请在预约设置中添加有效的节假日列表。",
			"Please add atleast one user on Allowed Users to allow Data Synchronization from Frappe CRM site.": "请在允许的用户中至少添加一名用户，以便从 Frappe CRM 站点同步数据。",
			"Please fill up the Availability of Slots table to enable Appointment Scheduling.": "请填写可用时段表后再启用预约安排。",
			"Please select a Holiday List to enable Appointment Scheduling.": "请选择节假日列表后再启用预约安排。",
			"User not allowed to synchronize data from Frappe CRM on ERPNext. Contact System Manager of ERPNext.": "该用户无权将 Frappe CRM 数据同步到 ERPNext，请联系 ERPNext 系统管理员。",
			"Verification Link Expiry Duration": "验证链接有效时长",
			"Verification Token": "验证令牌",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)
			self._assert_erpnext_runtime_translation(source, translation)

	def test_crm_dynamic_messages_translate_visible_business_values(self):
		repo_root = Path(__file__).parents[2]
		contracts = {
			"erpnext/crm/doctype/email_campaign/email_campaign.py": [
				"self.campaign_name, _(self.email_campaign_for), self.recipient",
				'.format(_(campaign_for), recipient)',
			],
			"erpnext/crm/doctype/appointment_booking_settings/appointment_booking_settings.py": [
				"_(record.day_of_week)",
			],
		}
		for relative_path, snippets in contracts.items():
			text = (repo_root / relative_path).read_text()
			for snippet in snippets:
				self.assertIn(snippet, text, relative_path)

		for source in ("Lead", "Contact", "Email Group", "Monday"):
			messages = [self.catalog.get(source), self.merged_frappe_catalog.get(source)]
			self.assertTrue(
				any(message and message.string and "fuzzy" not in message.flags for message in messages),
				source,
			)

	def test_transaction_controllers_use_reviewed_chinese_terms(self):
		translations = {
			"Additional Discount Amount ({discount_amount}) cannot exceed the total before such discount ({total_before_discount})": "附加折扣金额（{discount_amount}）不能超过折扣前合计（{total_before_discount}）",
			"Cannot delete an item which has been ordered": "不能删除已下单的物料",
			"Cannot find a default warehouse for item {0}. Please select one in the Update Items dialog, or set a default in the Item Master or in Stock Settings.": "未找到物料 {0} 的默认仓库。请在“更新物料”对话框中选择仓库，或在物料主数据或库存设置中设置默认仓库。",
			"Cannot reduce quantity than ordered or purchased quantity": "数量不能低于已下单或已采购的数量",
			"Cannot update rate as item {0} is already ordered or purchased against this quotation": "物料 {0} 已基于此报价下单或采购，不能更新单价",
			"Company Address is missing. You don't have permission to create an Address. Please contact your System Manager.": "缺少公司地址，并且您无权创建地址。请联系系统管理员。",
			"Expenses Added To Stock for Item {0}": "计入物料 {0} 库存成本的费用",
			"Invalid Discount Amount": "折扣金额无效",
			"Item Wise Tax Details do not match with Taxes and Charges at the following rows:": "以下行的物料税费明细与税费不一致：",
			"Please select at least one attribute value": "请至少选择一个属性值",
			"Please set {0} in Company {1} or in the Item Defaults of Item {2}": "请将 {0} 配置在公司 {1} 或物料 {2} 的物料默认设置中",
			"Reserved Batch Conflict": "预留批次冲突",
			"Row #{0}: Cannot cancel this Manufacturing Stock Entry as quantity of Secondary Item {1} produced cannot be less than quantity delivered.": "第 {0} 行：不能取消此生产物料移动，因为已生产的副产品 {1} 数量不能少于已交付数量。",
			"Row #{0}: Cannot delete item {1} which is already ordered against this Sales Order.": "第 {0} 行：物料 {1} 已基于此销售订单下单，不能删除。",
			"Row #{0}: Item {1} has zero rate but '{2}' is not enabled.": "第 {0} 行：物料 {1} 的单价为零，但未启用“{2}”。",
			"Row #{0}: Warehouse {1} does not match with the warehouse {2} in Serial and Batch Bundle {3}.": "第 {0} 行：仓库 {1} 与仓库 {2} 不一致，序列号与批号组合编号为 {3}。",
			"Row #{0}: {1} is mandatory for the Inventory Dimension {2}.": "第 {0} 行：{1} 是库存辅助核算 {2} 的必填项。",
			"Row #{0}:Quantity for Item {1} cannot be zero.": "第 {0} 行：物料 {1} 的数量不能为零。",
			"Row {0}: Cannot sell item {1} from Sample Retention Warehouse {2}": "第 {0} 行：不能销售物料 {1}，其来源为样品仓 {2}",
			"Row {0}: Item {1} must be linked to a {2}.": "第 {0} 行：物料 {1} 必须关联到{2}。",
			"The batch {0} is reserved for {1} in the warehouse {2} and the remaining quantity is not enough to cover the reservations. So, cannot proceed with the {3} {4}.": "批次 {0} 已为 {1} 在仓库 {2} 中预留，剩余数量不足以满足预留需求，因此不能继续处理{3} {4}。",
			"The following cancelled repost entries exist for <b>{0}</b>:<br><br>{1}<br><br>Kindly delete these entries before continuing.": "<b>{0}</b> 存在以下已取消的重新过账记录：<br><br>{1}<br><br>请删除这些记录后再继续。",
			"The outstanding amount {0} in {1} is lesser than {2}. Updating the outstanding to this invoice.": "未结金额 {0} 在 {1} 中小于 {2}，正在将未结金额更新到此发票。",
			'To allow over ordering, update "Over Order Allowance" in Buying Settings.': "如需允许超量订购，请在采购设置中更新“超订容差（%）”。",
			"Unit Price": "单价",
			"We can see {0} is made against {1}. If you want {1}'s outstanding to be updated, uncheck the '{2}' checkbox.": "{0} 是基于 {1} 创建的。如需更新 {1} 的未结金额，请取消勾选“{2}”。",
			"You can use {0} to reconcile against {1} later.": "您可以稍后使用 {0} 与 {1} 进行核销。",
			"You don't have permission to create a Company Address. Please contact your System Manager.": "您无权创建公司地址。请联系系统管理员。",
			"You don't have permission to update Company details. Please contact your System Manager.": "您无权更新公司信息。请联系系统管理员。",
			"You don't have permission to update this document. Please contact your System Manager.": "您无权更新此单据。请联系系统管理员。",
			"{0} can be either {1} or {2}.": "{0} 只能是 {1} 或 {2}。",
			"{0} does not belong to the Company {1}.": "{0} 不属于公司 {1}。",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)
			self._assert_erpnext_runtime_translation(source, translation)

	def test_transaction_controller_dynamic_messages_translate_visible_types_and_labels(self):
		repo_root = Path(__file__).parents[2]
		contracts = {
			"erpnext/controllers/stock_controller.py": [
				"frappe.bold(_(voucher_type))",
				"frappe.bold(_(self.doctype))",
			],
			"erpnext/controllers/subcontracting_controller.py": ["item.idx, item.item_name, _(order_item_doctype)"],
			"erpnext/controllers/trends.py": [
				'frappe.bold(_("Period based On"))',
				'frappe.bold(_("Posting Date"))',
				'frappe.bold(_("Billing Date"))',
			],
		}
		for relative_path, snippets in contracts.items():
			text = (repo_root / relative_path).read_text()
			for snippet in snippets:
				self.assertIn(snippet, text, relative_path)

		for source in (
			"Stock Reservation Entry",
			"Sales Order",
			"Purchase Order Item",
			"Sales Order Item",
			"Period based On",
			"Posting Date",
			"Billing Date",
		):
			messages = [self.catalog.get(source), self.merged_frappe_catalog.get(source)]
			self.assertTrue(
				any(message and message.string and "fuzzy" not in message.flags for message in messages),
				source,
			)

	def test_stock_workflows_use_reviewed_chinese_terms(self):
		translations = {
			"A naming series conflict occurred while creating serial numbers. Please change the naming series for the item {0}.": "创建序列号时发生命名规则冲突。请更改物料 {0} 的命名规则。",
			"Available / Future Inventory": "可用库存／未来库存",
			"Bin Values Recalculated": "库存汇总值已重新计算",
			"Consumed quantity of item {0} exceeds transferred quantity.": "物料 {0} 的消耗数量超过调拨数量。",
			"Duplicate Serial Number Error": "序列号重复错误",
			"Full Name, Email or Phone/Mobile of the user are mandatory to continue.": "必须填写用户的姓名、电子邮箱或电话／手机号码后才能继续。",
			"GTIN-14": "GTIN-14",
			"Item Price added for {0} in Price List - {1}": "已为 {0} 在价格表 {1} 中添加物料价格",
			"Item Where Used": "物料使用情况",
			"Mandatory Depends On (Backend)": "必填条件（后端）",
			"Maximum discount % allowed when selling this item. Eg: if set to 20%, a discount greater than 20% cannot be applied in sales transactions.": "销售此物料时允许的最大折扣比例。例如设为 20%，销售交易不能应用超过 20% 的折扣。",
			"Negative Batch Report": "负库存批次报表",
			"Please first set Full Name, Email and Phone for the user": "请先为用户设置姓名、电子邮箱和电话号码",
			"Python expression evaluated on the server. Use doc.fieldname for the row and parent.fieldname for the parent document. When it evaluates to true the dimension becomes mandatory. Example: doc.t_warehouse and doc.qty > 0": "在服务器上计算的 Python 表达式。使用 doc.fieldname 引用当前行字段，使用 parent.fieldname 引用父单据字段。表达式结果为真时，该辅助核算项成为必填项。例如：doc.t_warehouse and doc.qty > 0",
			"Quantity must be greater than zero": "数量必须大于零",
			"Quantity must be less than or equal to {0}": "数量必须小于或等于 {0}",
			"Recalculate Values": "重新计算数值",
			"Reserved Inventory": "已预留库存",
			"Setup Warehouse": "设置仓库",
			"Stock Frozen": "库存已冻结",
			"Stock Qty vs Batch Qty": "库存数量与批次数量对比",
			"Stock not available to reserve for the Item {0} in Warehouse {1}.": "物料 {0} 在仓库 {1} 中没有可供预留的库存。",
			"Stock transactions dated on or before {0} are frozen because the period is closed and the Stock Closing Entry {1} has been generated. To make changes, cancel the Period Closing Voucher first.": "日期为 {0} 或更早的库存交易已冻结，因为期间已结账并生成库存结转分录 {1}。如需修改，请先取消期末结账凭证。",
			"The stock for the item {0} in the {1} warehouse was negative on the {2}. You should create a positive entry {3} before the date {4} and time {5} to post the correct valuation rate. For more details, please read the <a href='https://docs.erpnext.com/docs/user/manual/en/stock-adjustment-cogs-with-negative-stock'>documentation<a>.": "物料 {0} 在仓库 {1} 中的库存于 {2} 为负数。您应创建正数记录 {3}，并使其早于日期 {4}、时间 {5}，以便过账正确的成本价。详情请阅读<a href='https://docs.erpnext.com/docs/user/manual/en/stock-adjustment-cogs-with-negative-stock'>说明文档<a>。",
			"{0} is not a valid {1} fieldname.": "{0} 不是有效的 {1} 字段名。",
			"{0} units of {1} are required in {2} with the inventory dimension: {3} on {4} {5} for {6} to complete the transaction.": "需要 {0} 个 {1} 存放于 {2}，库存辅助核算为 {3}，日期 {4}、时间 {5}，供 {6} 完成交易。",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)
			self._assert_erpnext_runtime_translation(source, translation)

	def test_stock_dynamic_validation_translates_inventory_dimension_label(self):
		text = (Path(__file__).parents[2] / "erpnext/stock/utils.py").read_text()
		self.assertIn('frappe.bold(_("Inventory Dimension"))', text)
		messages = [self.catalog.get("Inventory Dimension"), self.merged_frappe_catalog.get("Inventory Dimension")]
		self.assertTrue(
			any(message and message.string and "fuzzy" not in message.flags for message in messages)
		)

	def test_public_frontend_uses_reviewed_chinese_terms(self):
		translations = {
			" Phantom Item": " 虚拟物料",
			"A few quick questions so we can set things up the way you work.": "请回答几个简单问题，以便按您的工作方式完成系统设置。",
			"A little about you": "关于您",
			"Add Phantom Item": "添加虚拟物料",
			"Clear Last Scanned Warehouse": "清除上次扫描的仓库",
			"Create Payment Request": "创建收付款申请",
			"Delete Demo Data": "删除演示数据",
			"Enable <b>{0}</b> on the Item master to proceed with {1} inspection.": "请在物料主数据中启用<b>{0}</b>，然后再进行{1}检验。",
			"How big is the team?": "您的团队规模有多大？",
			"Payment Schedules": "付款计划",
			"Phantom Item is mandatory": "必须选择虚拟物料",
			"Please select at least one schedule.": "请至少选择一项付款计划。",
			"Project Management": "项目管理",
			"Quality Inspection Not Configured": "质量检验单未配置",
			"Schedule Name": "计划名称",
			"Select Company Address": "选择公司地址",
			"Select Payment Schedule": "选择付款计划",
			"Select the modules that you plan to implement": "选择计划启用的业务模块",
			"Total Advance Paid": "预付款合计",
			"Total Advance Paid: {0}": "预付款合计：{0}",
			"Total Advance Received": "预收款合计",
			"Total Advance Received: {0}": "预收款合计：{0}",
			"Total Unpaid": "未付合计",
			"What do you use today?": "您目前使用什么系统？",
			"What kind of work do you do?": "您从事哪类业务？",
			"Who are you setting this up for?": "您在为谁设置这套系统？",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)
			self._assert_erpnext_runtime_translation(source, translation)

	def test_public_quality_inspection_message_translates_visible_arguments(self):
		text = (Path(__file__).parents[2] / "erpnext/public/js/controllers/transaction.js").read_text()
		self.assertIn("__(fieldname)", text)
		self.assertIn("__(type)", text)
		for source in (
			"Inspection Required before Purchase",
			"Inspection Required before Delivery",
			"Purchase",
			"Delivery",
		):
			messages = [self.catalog.get(source), self.merged_frappe_catalog.get(source)]
			self.assertTrue(
				any(message and message.string and "fuzzy" not in message.flags for message in messages),
				source,
			)

	def test_setup_and_onboarding_use_reviewed_chinese_terms(self):
		translations = {
			"Copy Attachments to Transaction": "将附件复制到交易单据",
			"Creating demo data": "正在创建演示数据",
			"Demo Data creation failed.": "演示数据创建失败。",
			"Demo data creation failed. Check notifications for more info.": "演示数据创建失败。请查看通知了解详情。",
			"Failed to create demo data": "创建演示数据失败",
			"Failed to personalize your setup": "个性化系统设置失败",
			"Failed to set defaults": "设置默认值失败",
			"Frappe School": "Frappe 学堂",
			"Invite Users": "邀请用户",
			"Is Half Day": "是否为半天",
			"Messaging CRM Campaign": "消息 CRM 营销活动",
			"Personalizing your setup": "正在个性化系统设置",
			"Review System Settings": "检查系统设置",
			"Setup Company": "设置公司",
			"Setup Email Account": "设置电子邮箱账户",
			"Setup Organization": "设置组织",
			"Setup Role Permissions": "设置角色权限",
			"Use Posting Datetime for Naming Documents": "使用记账日期时间生成单据编号",
			"When checked, the system will use the posting datetime of the document for naming the document instead of the creation datetime of the document.": "勾选后，系统将使用单据的记账日期时间生成单据编号，而不是使用单据创建日期时间。",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)
			self._assert_erpnext_runtime_translation(source, translation)

	def test_source_location_gate_ignores_whitespace_only_extraction_noise(self):
		whitespace = self.source_catalog.get("  ")
		self.assertIsNotNone(whitespace)
		self.assertFalse(whitespace.id.strip())

	def test_manufacturing_workflows_use_reviewed_chinese_terms(self):
		translations = {
			"BOM Stock Analysis": "物料清单库存分析",
			"FG Items to Make": "成品生产数量",
			"From BOM No": "来源物料清单编号",
			"If you still want to proceed, please disable '{0}' checkbox.": "如仍要继续，请取消勾选“{0}”。",
			"Main Item Code": "主物料编码",
			"Maximum Producible Items": "最大可生产数量",
			"Method {0} is not allowed to be run on a Job Card.": "生产任务单不允许执行方法 {0}。",
			"Please set actual demand or sales forecast to generate Material Requirements Planning Report.": "请设置实际需求或销售预测，以生成物料需求计划报表。",
			"Show availability of exploded items": "显示展开后物料的可用库存",
			"Sub Assembly Item Reference": "子装配件物料引用",
			"Sub assembly item references are missing. Please fetch the sub assemblies and raw materials again.": "缺少子装配件物料引用。请重新获取子装配件和原材料。",
			"The Company {0} of Sales Forecast {1} does not match with the Company {2} of Master Production Schedule {3}.": "公司 {0} 的销售预测 {1} 与公司 {2} 的主生产计划 {3} 不一致。",
			"Warehouse is required to get producible FG Items": "必须选择仓库才能获取可生产成品",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)
			self._assert_erpnext_runtime_translation(source, translation)

	def test_production_plan_messages_translate_dynamic_field_labels(self):
		text = (
			Path(__file__).parents[2]
			/ "erpnext/manufacturing/doctype/production_plan/production_plan.py"
		).read_text()
		self.assertIn('_(self.meta.get_field("skip_available_sub_assembly_item").label)', text)
		self.assertIn(
			'_(frappe.get_meta("Production Plan").get_field("ignore_existing_ordered_qty").label)',
			text,
		)
		for source in ("Consider Projected Qty in Calculation", "Consider Projected Qty in Calculation (RM)"):
			messages = [self.catalog.get(source), self.merged_frappe_catalog.get(source)]
			self.assertTrue(
				any(message and message.string and "fuzzy" not in message.flags for message in messages),
				source,
			)

	def test_subcontracting_workflows_use_reviewed_chinese_terms(self):
		translations = {
			'<span class="h4"><b>Subcontracting Inward and Outward</b></span>': '<span class="h4"><b>受托加工与委外加工</b></span>',
			"All linked Sales Orders must be subcontracted.": "所有关联的销售订单必须为受托加工订单。",
			"Additional {0} {1} of item {2} required as per BOM to complete this transaction": "要完成此交易，根据物料清单还需要 {0} {1} 的物料 {2}",
			"Create Service Item": "创建服务物料",
			"Create Subcontracted Item": "创建委外物料",
			"Create Subcontracting Order": "创建委外订单",
			"Create Subcontracting PO": "创建委外采购订单",
			"Create Subcontracting Purchase Order": "创建委外采购订单",
			"Creating Return of Components ...": "正在创建退回原材料单据……",
			"Get Secondary Items": "获取副产品",
			"Getting Secondary Items": "正在获取副产品",
			"Has Subcontracted": "已受托加工",
			"Job Worker Currency": "委外供应商币种",
			"Learn Subcontracting": "了解委外加工",
			"Qty (As per BOM)": "数量（按物料清单）",
			"Quantity is mandatory for the selected items.": "所选物料必须填写数量。",
			"Row #{0}: Finished Good reference is mandatory for Secondary Item {1}.": "第 {0} 行：副产品 {1} 必须关联成品。",
			"Row #{0}: Rejected Qty cannot be set for Secondary Item {1}.": "第 {0} 行：副产品 {1} 不能设置拒收数量。",
			"Row #{0}: Secondary Item Qty cannot be zero": "第 {0} 行：副产品数量不能为零",
			"Secondary Items Cost Per Qty": "每单位副产品成本",
			"Secondary Items Generated": "已生成副产品",
			"Select Items to Receive": "选择待收物料",
			"Stock Reservation Entries created": "已创建库存预留单",
			"Subcontract BOM": "委外物料清单",
			"Subcontracted Purchase Order": "委外采购订单",
			"Subcontracting Inward Order": "受托加工订单",
			"Subcontracting Inward Order Secondary Item": "受托加工订单副产品",
			"Subcontracting Purchase Order": "委外采购订单",
			"Subcontracting Sales Order": "受托加工销售订单",
			"Subcontracting Delivery": "受托加工交付",
			"Subcontracting Setup": "委外设置",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)
			self._assert_erpnext_runtime_translation(source, translation)

	def test_subcontracting_vocabulary_rejects_legacy_ambiguous_terms(self):
		forbidden_terms = ("外包", "外协", "分包")
		allowed_terms = ("委外", "受托加工")
		violations = []

		for message in self.catalog:
			sources = message.id if isinstance(message.id, tuple) else (message.id,)
			if not any(
				isinstance(source, str) and re.search(r"sub[- ]?contract", source, re.IGNORECASE)
				for source in sources
			):
				continue

			translations = message.string if isinstance(message.string, tuple) else (message.string,)
			if "fuzzy" in message.flags or not translations or any(not translation for translation in translations):
				violations.append(f"{message.id} => missing or fuzzy translation")
				continue
			for translation in translations:
				if any(term in translation for term in forbidden_terms):
					violations.append(f"{message.id} => {translation}")
				elif not any(term in translation for term in allowed_terms):
					violations.append(f"{message.id} => missing approved terminology: {translation}")

		self.assertEqual(violations, [])

	def test_accounts_workflows_use_reviewed_chinese_terms(self):
		translations = {
			"A Period Closing Voucher is already submitted and an Opening Entry can no longer be created. {0} to learn more.": "期末结账凭证已提交，无法再创建开账凭证。请查看 {0} 了解详情。",
			"A draft reverse journal for {0} has been created: {1}": "已为 {0} 创建草稿冲销日记账凭证：{1}",
			"A new fiscal year has been automatically created.": "已自动创建新会计年度。",
			"At least one row is required for a financial report template": "财务报表模板至少需要一行。",
			"Bold Text": "粗体文字",
			"Bold text for emphasis (totals, major headings)": "使用粗体强调（合计、主要标题）",
			"Cannot merge {0} '{1}' into '{2}' as both have existing accounting entries in different currencies for company '{3}'.": "无法将 {0}“{1}”合并到“{2}”，因为两者在公司“{3}”中已有不同币种的会计分录。",
			"Check row {0} for account {1}: Party Type is only allowed for Receivable or Payable accounts": "请检查第 {0} 行的科目 {1}：仅应收或应付科目可设置往来类型。",
			"Check row {0} for account {1}: Party is only allowed if Party Type is set": "请检查第 {0} 行的科目 {1}：设置往来类型后才能选择往来单位。",
			"Code to reference this line in formulas (e.g., REV100, EXP200, ASSET100)": "在公式中引用此行的代码（例如 REV100、EXP200、ASSET100）",
			"Color to highlight values (e.g., red for exceptions)": "用于突出显示数值的颜色（例如异常项使用红色）",
			"Descriptive name for your template (e.g., 'Standard P&L', 'Detailed Balance Sheet')": "模板的描述性名称（例如“标准利润表”、“详细资产负债表”）",
			"Disable template to prevent use in reports": "禁用模板，防止其用于报表。",
			"Duplicate languages found on Dunning Letter Text. Keep only one of them.": "催款信文本中存在重复语言，请每种语言仅保留一条。",
			"How to format and present values in the financial report (only if different from column fieldtype)": "财务报表中数值的格式和展示方式（仅在与列字段类型不同时设置）",
			"If enabled, this row's values will be displayed on financial charts": "启用后，此行数值将显示在财务图表中。",
			"If party does not exist, create it using the Customer Name field.": "如果往来单位不存在，则使用客户名称字段创建。",
			"If party does not exist, create it using the Supplier Name field.": "如果往来单位不存在，则使用供应商名称字段创建。",
			"Indentation level: 0 = Main heading, 1 = Sub-category, 2 = Individual accounts, etc.": "缩进级别：0 = 主标题，1 = 子类别，2 = 明细科目，依此类推。",
			"Italic Text": "斜体文字",
			"Italic text for subtotals or notes": "小计或备注使用斜体文字",
			"No <strong>Account Data</strong> row found": "未找到<strong>科目数据</strong>行。",
			"Opening Balance = Start of period, Closing Balance = End of period, Period Movement = Net change during period": "期初余额 = 期间开始时余额，期末余额 = 期间结束时余额，本期变动 = 期间净变动额",
			"Party ID": "往来单位编号",
			"Please review the {0} configuration and complete any required financial setup activities.": "请检查 {0} 配置，并完成必要的财务设置。",
			"Reversal Journal Entries": "冲销日记账凭证",
			"Reverse {0} already available in draft status: {1}": "已有草稿状态的冲销{0}：{1}",
			"Reversing Journals...": "正在冲销日记账凭证……",
			"Row #{0}: {1} account is not of type {2}": "第 {0} 行：{1} 科目不是 {2} 类型。",
			"Setup Sales taxes": "设置销售税",
			"Text displayed on the financial statement (e.g., 'Total Revenue', 'Cash and Cash Equivalents')": "财务报表上显示的文字（例如“营业收入合计”、“货币资金”）",
			"The fiscal year has been automatically created in a Disabled state to maintain consistency with the previous fiscal year's status.": "为与上一会计年度的状态保持一致，新会计年度已自动创建为禁用状态。",
			"Try the {0} for a better experience.": "建议使用 {0} 以获得更好的操作体验。",
			"Updated {0} Financial Report Row(s) with new category name": "已使用新类别名称更新 {0} 个财务报表行。",
			"Use <strong>Python</strong> filters to get Accounts": "使用 <strong>Python</strong> 筛选条件获取科目",
			"User don't have permissions to select/read this account.": "用户无权选择或读取此科目。",
			"frankfurter.dev": "frankfurter.dev",
			"frankfurter.dev - v2": "frankfurter.dev - v2",
			"{0} doesn't belong to Company {1}. Please select a Cost Center that belongs to Company {1}.": "{0} 不属于公司 {1}。请选择属于公司 {1} 的成本中心。",
			"{0} doesn't belong to Company {1}. Please select an Income Account that belongs to Company {1}.": "{0} 不属于公司 {1}。请选择属于公司 {1} 的收入科目。",
			"{0} is a group Cost Center. Please select a non-group Cost Center.": "{0} 是成本中心组。请选择非组成本中心。",
			"{0} is a group account. Please select a non-group Income Account.": "{0} 是组科目。请选择非组收入科目。",
			"{0} is disabled. Please select a valid Income Account.": "{0} 已禁用。请选择有效的收入科目。",
			"{0} is disabled. Please select an enabled Cost Center.": "{0} 已禁用。请选择已启用的成本中心。",
			"{0} is not an Income Account. Please select a valid Income Account.": "{0} 不是收入科目。请选择有效的收入科目。",
			"{0} languages are marked as default languages. Please select only one of them.": "{0} 种语言被标记为默认语言。请仅保留一种默认语言。",
			"{0} view is currently unsupported in Custom Financial Report.": "自定义财务报表当前不支持“{0}”视图。",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)
			self._assert_erpnext_runtime_translation(source, translation)

	def test_accounts_dynamic_messages_translate_visible_arguments(self):
		repo_root = Path(__file__).parents[2]
		contracts = {
			"erpnext/accounts/doctype/exchange_rate_revaluation/exchange_rate_revaluation.py": [
				'part = _("Journal Entries") if len(drafts) > 1 else _("Journal Entry")',
			],
			"erpnext/accounts/doctype/bank_reconciliation_tool/bank_reconciliation_tool.js": [
				'`<a href=\'/banking\'>${__("Banking")}</a>`',
			],
			"erpnext/accounts/party.py": ["_(party_type),"],
			"erpnext/accounts/doctype/opening_invoice_creation_tool/opening_invoice_creation_tool.py": [
				'row.idx, row.temporary_opening_account, _("Temporary")',
			],
			"erpnext/accounts/notification/notification_for_new_fiscal_year/notification_for_new_fiscal_year.html": [
				'frappe.bold(_("Fiscal Year"))',
			],
			"erpnext/accounts/doctype/financial_report_template/financial_report_engine.py": [
				'.format(_(view))',
			],
		}
		for relative_path, snippets in contracts.items():
			text = (repo_root / relative_path).read_text()
			for snippet in snippets:
				self.assertIn(snippet, text, relative_path)

		dynamic_examples = {
			"Journal Entry": "日记账凭证",
			"Journal Entries": "日记账凭证",
			"Banking": "银行",
			"Customer": "客户",
			"Supplier": "供应商",
			"Temporary": "临时",
			"Fiscal Year": "财年",
			"Margin": "利润空间",
		}
		for source, translation in dynamic_examples.items():
			self._assert_translation(source, translation)
			self._assert_erpnext_runtime_translation(source, translation)

		self.assertEqual(
			self.catalog.get("Reverse {0} already available in draft status: {1}").string.format(
				self.catalog.get("Journal Entry").string, "ACC-JV-0001"
			),
			"已有草稿状态的冲销日记账凭证：ACC-JV-0001",
		)
		self.assertEqual(
			self.catalog.get("{0} view is currently unsupported in Custom Financial Report.").string.format(
				self.catalog.get("Margin").string
			),
			"自定义财务报表当前不支持“利润空间”视图。",
		)

		notification_path = (
			repo_root
			/ "erpnext/accounts/notification/notification_for_new_fiscal_year/notification_for_new_fiscal_year.json"
		)
		notification_message = json.loads(notification_path.read_text())["message"]
		self.assertIn('frappe.bold(_("Fiscal Year"))', notification_message)
		self.assertNotIn('frappe.bold("Fiscal Year")', notification_message)
		notification_subject = json.loads(notification_path.read_text())["subject"]
		self.assertEqual(notification_subject, '{{ _("New Fiscal Year - {0}").format(doc.name) }}')

	def test_core_business_report_gettext_messages_are_translated(self):
		erpnext_root = Path(__file__).parents[1]
		roots = (
			erpnext_root / "accounts/report",
			erpnext_root / "buying/report",
			erpnext_root / "projects/report",
			erpnext_root / "selling/report",
			erpnext_root / "stock/report",
		)
		message_pattern = re.compile(r'''__\(\s*["']([^"']+)["']''')
		missing = []

		for root in roots:
			for path in sorted(root.glob("**/*.js")):
				source = re.sub(r"/\*.*?\*/", "", path.read_text(), flags=re.DOTALL)
				source = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("//"))
				for message_id in message_pattern.findall(source):
					message = self.catalog.get(message_id)
					if not message or not message.string or "fuzzy" in message.flags or message.check():
						missing.append(f"{path.relative_to(erpnext_root)}:{message_id}")

		self.assertEqual(missing, [])

	def test_core_business_report_server_messages_are_translated(self):
		erpnext_root = Path(__file__).parents[1]
		roots = (
			erpnext_root / "accounts/report",
			erpnext_root / "buying/report",
			erpnext_root / "projects/report",
			erpnext_root / "selling/report",
			erpnext_root / "stock/report",
		)
		missing = []

		for root in roots:
			for path in sorted(root.glob("**/*.py")):
				tree = ast.parse(path.read_text())
				for node in ast.walk(tree):
					if not (
						isinstance(node, ast.Call)
						and isinstance(node.func, ast.Name)
						and node.func.id == "_"
						and node.args
						and isinstance(node.args[0], ast.Constant)
						and isinstance(node.args[0].value, str)
					):
						continue
					message_id = node.args[0].value
					message = self.catalog.get(message_id)
					if not message or not message.string or "fuzzy" in message.flags or message.check():
						missing.append(f"{path.relative_to(erpnext_root)}:{message_id}")

		self.assertEqual(missing, [])

	def test_security_and_audit_navigation_uses_reviewed_frappe_terms(self):
		translations = {
			"Roles & Permissions": "角色与权限",
			"Security Settings": "安全设置",
			"Simultaneous Sessions": "并发会话数",
			"Restrict IP": "限制IP",
			"API Access": "API 访问",
			"API Key": "API 密钥",
			"API Secret": "API 密钥",
			"Generate Keys": "生成密钥",
			"User Permission": "用户权限",
			"Apply To All Document Types": "应用于所有文档类型",
			"Applicable For": "适用于",
			"Hide Descendants": "隐藏下层节点",
			"Set Role For": "设置角色",
			"Allow Roles": "允许的角色",
			"Enable Prepared Report": "启用预生成报表",
			"Access Log": "访问记录",
			"Activity Log": "用户操作日志",
			"Reference Document": "源单据",
			"Log Data": "日志数据",
			"Show Report": "查看报表",
			"Show Document": "显示文档",
			"IP Address": "IP地址",
			"Impersonate": "用其它用户身份登录",
			"Version": "版本",
			"Document Name": "单据名称",
			"Navigation Buttons": "导航按钮",
			"Customize Quick Filters": "自定义快捷筛选条件",
			"Open Link": "打开链接",
			"Current Series": "当前编号",
		}

		for source, translation in translations.items():
			self._assert_frappe_translation(source, translation)

	def test_every_frappe_public_javascript_message_has_a_translation_owner(self):
		missing = []
		for message in self.frappe_runtime_catalog:
			if not message.id or not any(
				location.startswith("frappe/public/js/") for location, _line in message.locations
			):
				continue
			translated = self.merged_frappe_catalog.get(message.id, context=message.context)
			if not (
				translated
				and translated.string
				and "fuzzy" not in translated.flags
				and self._message_is_valid(translated)
			):
				missing.append(message.id)

		self.assertEqual(missing, [])

	def test_every_core_and_compliance_doctype_field_has_a_translation_owner(self):
		doctype_root = Path(__file__).parents[1]
		documents = {}
		for path in sorted(doctype_root.glob("**/doctype/*/*.json")):
			data = json.loads(path.read_text())
			if isinstance(data, dict) and data.get("name"):
				documents[data["name"]] = (path, data)

		root_doctypes = (
			CORE_BUSINESS_DOCTYPES
			| CORE_ACCOUNTING_MASTER_DOCTYPES
			| CORE_OPERATIONAL_MASTER_DOCTYPES
			| CHINA_COMPLIANCE_DOCTYPES
		)
		target_doctypes = self._doctype_closure(documents, root_doctypes)

		missing = []
		select_option_allowlist = {"GTIN-14"}
		for doctype in sorted(target_doctypes):
			path, data = documents[doctype]
			doctype_messages = [
				catalog.get(doctype) for catalog in (self.catalog, self.merged_frappe_catalog)
			]
			if not any(
				message and message.string and "fuzzy" not in message.flags and self._message_is_valid(message)
				for message in doctype_messages
			):
				missing.append(f"{path.relative_to(doctype_root)}:doctype:{doctype}")

			for field in data.get("fields", []):
				for key in ("label", "description"):
					source = field.get(key)
					if not isinstance(source, str) or not source.strip():
						continue
					messages = [
						catalog.get(source)
						for catalog in (self.catalog, self.merged_frappe_catalog)
					]
					if not any(
						message and message.string and "fuzzy" not in message.flags and self._message_is_valid(message)
						for message in messages
					):
						missing.append(f"{path.relative_to(doctype_root)}:{field.get('fieldname')}:{key}:{source.strip()}")

				if field.get("fieldtype") == "Select" and field.get("fieldname") != "naming_series":
					for source in field.get("options", "").splitlines():
						source = source.strip()
						if not source or source.isdecimal() or source in select_option_allowlist:
							continue
						messages = [
							catalog.get(source) for catalog in (self.catalog, self.merged_frappe_catalog)
						]
						if not any(
							message and message.string and "fuzzy" not in message.flags and self._message_is_valid(message)
							for message in messages
						):
							missing.append(
								f"{path.relative_to(doctype_root)}:{field.get('fieldname')}:option:{source}"
							)

		target_location_markers = {
			f"/doctype/{documents[doctype][0].parent.name}/" for doctype in target_doctypes
		}
		for message in self.catalog:
			if not message.id or isinstance(message.id, tuple):
				continue
			if message.id in select_option_allowlist:
				continue
			if not any(
				marker in filename
				for filename, _ in message.locations
				for marker in target_location_markers
			):
				continue
			if not message.string or "fuzzy" in message.flags or not self._message_is_valid(message):
				missing.append(f"catalog:{message.id}")

		self.assertEqual(missing, [])

	def test_stock_settings_uses_reviewed_chinese_terms(self):
		translations = {
			"Allow negative stock": "允许负库存",
			"Allow negative stock for Batch": "允许批次负库存",
			"Enable stock reservation": "启用库存预留",
			"Auto reserve Stock for Sales Order on Purchase": "采购入库时自动为销售订单预留库存",
			"Allow internal transfers at user-defined rate": "允许内部调拨使用用户指定单价",
			"Do not use Batch-wise Valuation": "不使用按批次计价",
			"Stock frozen up to": "库存冻结截止日期",
			"Role allowed to edit frozen stock": "允许编辑已冻结库存的角色",
			"Raise Material Request when stock reaches re-order level": "库存达到再订购水平时生成物料需求",
			"Action if Quality Inspection is rejected": "质量检验不合格时的处理方式",
			"Over Picking Allowance (%)": "超量拣货允许比例（%）",
			"Warehouse Defaults": "仓库默认设置",
			"Internal Transfer Rules": "内部调拨规则",
			"Quantity Tolerance": "数量容差",
			"Allow to edit stock UOM qty for Stock Entry": "允许在物料移动中编辑库存单位数量",
			"Auto create Serial and Batch Bundle for outward": "出库时自动创建序列号与批号",
			"If enabled, the item rate won't adjust to the valuation rate during internal transfers, but accounting will still use the valuation rate. This will allow the user to specify a different rate for printing or taxation purposes.": "启用后，内部调拨的物料单价不会调整为成本价，但会计处理仍使用成本价。用户可因打印或税务需要指定不同单价。",
			"If enabled, the system will allow negative stock entries for the batch. But, this may lead to incorrect valuation rates, so it is recommended to avoid using this option. The system will permit negative stock only when it is caused by backdated entries and will validate and block negative stock in all other cases.": "启用后，系统将允许该批次出现负库存。此设置可能导致成本价不准确，因此建议不要启用。系统仅在负库存由补录历史单据引起时允许过账，其他情况将校验并阻止。",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_fixed_asset_lifecycle_uses_reviewed_chinese_terms(self):
		translations = {
			"<b>Cannot create asset.</b><br><br>You're trying to create <b>{0} asset(s)</b> from {2} {3}.<br>However, only <b>{1} item(s)</b> were purchased and <b>{4} asset(s)</b> already exist against {5}.": "<b>无法创建资产。</b><br><br>您正在尝试创建 <b>{0} 项资产</b>，来源为 {2} {3}。<br>但仅采购了 <b>{1} 个物料</b>，并且已有 <b>{4} 项资产</b>关联到 {5}。",
			"Asset Type": "资产类型",
			"Existing Asset": "现有资产",
			"Composite Asset": "组合资产",
			"Composite Component": "组合资产组件",
			"Available for Use Date": "可使用日期",
			"Ownership": "权属信息",
			"Capitalize this asset before submitting.": "请在提交前将此资产资本化。",
			"Please capitalize this asset before submitting.": "请在提交前将此资产资本化。",
			"Row #{0}: Frequency of Depreciation must be greater than zero": "第 {0} 行：折旧频率必须大于零",
			"Row #{0}: Total Number of Depreciations must be greater than zero": "第 {0} 行：折旧总次数必须大于零",
			"Row {0}: Expected Value After Useful Life cannot be negative": "第 {0} 行：使用寿命结束后的预计价值不能为负数",
			"Row #{0}: Expense account {1} is not valid for Purchase Invoice {2}. Only expense accounts from non-stock items are allowed.": "第 {0} 行：费用科目 {1} 不适用于采购发票 {2}。仅允许使用非库存物料的费用科目。",
			"Sell Qty": "出售数量",
			"Sell quantity must be greater than zero": "出售数量必须大于零",
			"Sell quantity cannot exceed the asset quantity": "出售数量不能超过资产数量",
			"The sell quantity is less than the total asset quantity. The remaining quantity will be split into a new asset. This action cannot be undone. <br><br><b>Do you want to continue?</b>": "出售数量小于资产总数量，剩余数量将拆分为一项新资产。此操作无法撤销。<br><br><b>是否继续？</b>",
			"Transaction date can't be earlier than previous movement date": "业务日期不能早于上一次资产变动日期",
			"The following Purchase Invoices are not submitted:": "以下采购发票尚未提交：",
			"Row #{0}: Repair cost {1} exceeds available amount {2} for Purchase Invoice {3} and Account {4}": "第 {0} 行：维修费用 {1} 超过可用金额 {2}（采购发票 {3}，科目 {4}）",
			"Row {0}: The entire expense amount for account {1} in {2} has already been allocated.": "第 {0} 行：科目 {1} 在 {2} 中的费用金额已全部分配。",
			"{0} is in Draft. Submit it before creating the Asset.": "{0} 仍为草稿。请先提交，再创建资产。",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_asset_capitalization_and_maintenance_use_reviewed_chinese_terms(self):
		translations = {
			"Asset Capitalization": "资产资本化",
			"Asset Maintenance": "资产维护",
			"Asset Maintenance Log": "资产维护日志",
			"Asset Value Adjustment": "资产价值调整",
			"Asset capitalized after Asset Capitalization {0} was submitted": "提交资产资本化单 {0} 后，资产已完成资本化",
			"Asset restored after Asset Capitalization {0} was cancelled": "取消资产资本化单 {0} 后，资产已恢复",
			"Consumed Asset Total Value": "耗用资产总价值",
			"Consumed Stock Total Value": "耗用库存总价值",
			"Consumed Stock Items, Consumed Asset Items or Consumed Service Items is mandatory for Capitalization": "执行资本化时，必须填写耗用的库存物料、资产物料或服务物料",
			"Service Expense Total Amount": "服务费用总额",
			"Target Asset": "目标资产",
			"Target Incoming Rate": "目标入账单价",
			"Target Item Code": "目标物料编码",
			"Value Details": "价值明细",
			"Maintenance Log": "维护日志",
			"Maintenance Manager Name": "维护负责人姓名",
			"Maintenance Status": "维护状态",
			"Maintenance Status has to be Cancelled or Completed to Submit": "提交前，维护状态必须为已取消或已完成",
			"Maintenance Tasks": "维护任务",
			"Maintenance Team": "维护团队",
			"Maintenance Type": "维护类型",
			"Task Name": "任务名称",
			"Task Assignee Email": "任务负责人邮箱",
			"Start date should be less than end date for task {0}": "任务 {0} 的开始日期必须早于结束日期",
			"Please enter Item Code to get Batch Number": "请输入物料编码以获取批号",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_pos_shift_and_cash_control_use_reviewed_chinese_terms(self):
		translations = {
			"POS Profile": "POS 配置方案",
			"POS Configurations": "POS 配置",
			"POS Item Selector": "POS 物料选择",
			"POS Item Details": "POS 物料详情",
			"POS Opening Entry": "POS 开班登记",
			"POS Closing Entry": "POS 交班结算",
			"Opening & Closing": "POS 开班与交班",
			"Cashier": "收银员",
			"Opening Amount": "开班金额",
			"Opening Balance Details": "开班金额明细",
			"Expected Amount": "应有金额",
			"Closing Amount": "实际金额",
			"Account for Change Amount": "找零科目",
			"Please enter Account for Change Amount": "请填写找零科目",
			"POS Invoice": "POS 发票",
			"POS Invoice Merge Log": "POS 发票合并日志",
			"POS Transactions": "POS 交易",
			"At least one mode of payment is required for POS invoice.": "POS 发票必须至少设置一种付款方式。",
			"Payment methods are mandatory. Please add at least one payment method.": "必须设置付款方式，请至少添加一种付款方式。",
			"You can only select one mode of payment as default": "只能将一种付款方式设为默认",
			"POS Profile {0} cannot be disabled as there are ongoing POS sessions.": "POS 配置方案 {0} 仍有进行中的收银班次，无法停用。",
			"POS Profile - {0} is currently open. Please close the POS or cancel the existing POS Opening Entry before cancelling this POS Closing Entry.": "POS 配置方案 {0} 当前仍在开班。请先完成 POS 交班，或取消现有 POS 开班登记，再取消本次 POS 交班结算。",
			"POS Opening Entry cannot be cancelled as unconsolidated Invoices exists.": "仍有未合并的发票，无法取消 POS 开班登记。",
			"Selected POS Opening Entry should be open.": "所选 POS 开班登记必须处于开班状态。",
			"{0} is open. Close the POS or cancel the existing POS Opening Entry to create a new POS Opening Entry.": "{0} 仍在开班。请先完成 POS 交班，或取消现有 POS 开班登记，再创建新的 POS 开班登记。",
			"You need to cancel POS Closing Entry {} to be able to cancel this document.": "必须先取消 POS 交班结算 {}，才能取消此单据。",
			"Please select Customer first": "请先选择客户",
			"Insufficient Stock for Product Bundle Items": "套件物料库存不足",
			"Row #{0}: Item {1} has no stock in warehouse {2}.": "第 {0} 行：物料 {1} 在仓库 {2} 中没有库存。",
			"Row #{0}: Item {1} in warehouse {2}: Available {3}, Needed {4}.": "第 {0} 行：物料 {1} 在仓库 {2} 中可用 {3}，需要 {4}。",
			"Scheduler is inactive. Cannot enqueue job.": "调度器未启用，无法将任务加入队列。",
			"Serial / Batch Bundle Missing": "缺少序列号与批号",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_landed_cost_allocation_uses_reviewed_chinese_terms(self):
		translations = {
			"Landed Cost Voucher": "到岸成本凭证",
			"Landed Cost": "到岸成本",
			"Landed Cost Item": "到岸成本明细",
			"Applicable Charges": "分摊费用",
			"Distribute Charges Based On": "费用分摊依据",
			"Distribute Manually": "手动分摊",
			"Charges are updated in Purchase Receipt against each item": "费用将按物料更新到采购入库中",
			"Charges will be distributed proportionately based on item qty or amount, as per your selection": "费用将根据所选分摊依据，按物料数量或金额比例分摊。",
			"Item valuation rate is recalculated considering landed cost voucher amount": "物料成本价将基于到岸成本凭证金额重新计算",
			"Receipt Document": "入库单据",
			"Receipt Document Type": "入库单据类型",
			"Is Fixed Asset": "是否固定资产",
			"Incorrect Account": "科目不正确",
			"Incorrect Company": "公司不正确",
			"Incorrect Reference Document (Purchase Receipt Item)": "关联单据不正确（采购入库明细）",
			"Row {0}: Expense Account {1} is linked to company {2}. Please select an account belonging to company {3}.": "第 {0} 行：费用科目 {1} 关联到公司 {2}。请选择属于公司 {3} 的科目。",
			"Row {0}: {1} {2} is linked to company {3}. Please select a document belonging to company {4}.": "第 {0} 行：{1} {2} 关联到公司 {3}。请选择属于公司 {4} 的单据。",
			"Row {0}: {2} Item {1} does not exist in {2} {3}": "第 {0} 行：{2} 物料 {1} 不存在于 {2} {3} 中",
			"Stock Ledger Entries and GL Entries are reposted for the selected Purchase Receipts": "将为所选采购入库重新过账物料凭证和会计凭证",
			"Total Applicable Charges in Purchase Receipt Items table must be same as Total Taxes and Charges": "采购入库明细表中的适用费用合计必须等于税费合计",
			"Total Landed Cost (Company Currency)": "到岸成本合计（本币）",
			"Total Vendor Invoices Cost (Company Currency)": "供应商发票成本合计（本币）",
			"Total {0} for all items is zero, may be you should change 'Distribute Charges Based On'": "所有物料的 {0} 合计为零，请考虑更改“费用分摊依据”",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_supplier_quotation_workflow_uses_reviewed_chinese_terms(self):
		translations = {
			"Request for Quotation": "询价单",
			"Request for Quotation Item": "询价单明细",
			"Request for Quotation Supplier": "询价单供应商",
			"Supplier Quotation": "供应商报价单",
			"Supplier Quotation Item": "供应商报价单明细",
			"Supplier Quotation Comparison": "供应商比价",
			"Create Supplier Quotation": "创建供应商报价",
			"Quote Status": "报价状态",
			"Valid Till": "有效期至",
			"Valid till Date cannot be before Transaction Date": "有效期至不能早于业务日期",
			"Expected Delivery Date": "预计交货日期",
			"Possible Supplier": "候选供应商",
			"Select Possible Supplier": "选择候选供应商",
			"Get Suppliers By": "供应商筛选依据",
			"Supplier Part No": "供应商物料编码",
			"Supplier Part Number": "供应商物料编码",
			"Distributed Discount Amount": "分摊折扣金额",
			"Incoterm": "国际贸易术语",
			"Link to Material Requests": "关联物料需求",
			"Download PDF for Supplier": "下载供应商版 PDF",
			"Send Document Print": "附加单据 PDF",
			"Send Email": "发送邮件",
			"RFQs are not allowed for {0} due to a scorecard standing of {1}": "供应商 {0} 的评分卡等级为 {1}，不允许向其发出询价。",
			"{0} currently has a {1} Supplier Scorecard standing, and RFQs to this supplier should be issued with caution.": "{0}当前供应商评分等级为{1}，请谨慎向该供应商询价。",
			"Row {0}: For Supplier {1}, Email Address is Required to send an email": "行号{0}：供应商{1}必须填写邮箱地址以发送邮件",
			"Same supplier has been entered multiple times": "同一个供应商已多次输入",
			"The Access to Request for Quotation From Portal is Disabled. To Allow Access, Enable it in Portal Settings.": "门户询价申请功能已禁用。如需启用，请在门户设置中开启",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_quality_inspection_uses_reviewed_chinese_terms(self):
		translations = {
			"Quality Inspection": "质量检验单",
			"Quality Inspection Reading": "质量检验读数",
			"Quality Inspection Template": "质量检验模板",
			"Item Quality Inspection Parameter": "物料质量检验参数",
			"Inspection Type": "检验类型",
			"Inspected By": "检验人",
			"Verified By": "复核人",
			"Report Date": "检验日期",
			"Sample Size": "抽检数量",
			"Readings": "检验读数",
			"Reading Value": "检验读数值",
			"Reading 1": "检验读数 1",
			"Reading 10": "检验读数 10",
			"Manual Inspection": "人工检验",
			"Numeric Inspection": "数值检验",
			"Value Based Inspection": "按值检验",
			"Acceptance Criteria Formula": "验收标准公式",
			"Acceptance Criteria Value": "验收标准值",
			"Formula Based Criteria": "公式判定",
			"Applied on each reading.": "逐个检验读数应用。",
			"Invalid Reading": "检验读数无效",
			"Row #{0}: Reading {1} {2} is not a valid number in the {3} number format. Use {4} as the decimal separator.": "第 {0} 行：检验读数 {1} {2} 不符合 {3} 数字格式。请使用 {4} 作为小数分隔符。",
			"Row #{0}: {1} is not a valid reading field. Please refer to the field description.": "第 {0} 行：{1} 不是有效的检验读数字段，请参阅字段说明。",
			"Status set to rejected as there are one or more rejected readings.": "存在一项或多项不合格检验读数，质量检验单状态已设为不合格。",
			"Set the status manually.": "手动设置检验状态。",
			"'Inspection Required before Delivery' has disabled for the item {0}, no need to create the QI": "物料 {0} 未启用“交付前必须质量检验”，无需创建质量检验单",
			"'Inspection Required before Purchase' has disabled for the item {0}, no need to create the QI": "物料 {0} 未启用“采购前必须质量检验”，无需创建质量检验单",
			(
				"Simple Python formula applied on Reading fields.<br> Numeric eg. 1: <b>reading_1 &gt; 0.2 and reading_1 &lt; 0.5</b><br>\n"
				"Numeric eg. 2: <b>mean &gt; 3.5</b> (mean of populated fields)<br>\n"
				'Value based eg.:  <b>reading_value in ("A", "B", "C")</b>'
			): (
				"在检验读数字段上应用简单 Python 公式。<br>数值示例 1：<b>reading_1 &gt; 0.2 and reading_1 &lt; 0.5</b><br>\n"
				"数值示例 2：<b>mean &gt; 3.5</b>（已填写读数字段的平均值）<br>\n"
				'按值判定示例：<b>reading_value in ("A", "B", "C")</b>'
			),
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_stock_reconciliation_uses_reviewed_chinese_terms(self):
		translations = {
			"Stock Reconciliation": "库存盘点调整",
			"Stock Reconciliation Item": "库存盘点调整明细",
			"Before reconciliation": "盘点调整前",
			"Current Qty": "账面数量",
			"Current Amount": "账面金额",
			"Current Valuation Rate": "账面成本价",
			"Current Serial / Batch Bundle": "账面序列号与批号组合",
			"Quantity Difference": "数量差异",
			"Amount Difference": "金额差异",
			"Allow Zero Valuation Rate": "允许成本价为零",
			"Negative Quantity is not allowed": "库存数量不能为负数",
			"Negative Valuation Rate is not allowed": "成本价不可以为负数",
			"Please enter Batch No": "请输入批号",
			"Please enter Serial No": "请输入序列号",
			"Please specify either Quantity or Valuation Rate or both": "请填写实盘数量、成本价，或同时填写两者",
			"Reconcile All Serial Nos / Batches": "盘点全部序列号与批号",
			"Serial / Batch Bundle": "序列号与批号组合",
			"Add Serial / Batch No": "添加序列号与批号",
			"Row # {0}: Please add Serial and Batch Bundle for Item {1}": "第 {0} 行：请为物料 {1} 添加序列号与批号",
			"Row #{0}: Item {1} is not a Serialized/Batched Item. It cannot have a Serial No/Batch No against it.": "第 {0} 行：物料 {1} 未启用序列号或批号管理，不能为其设置序列号或批号。",
			"Same item and warehouse combination already entered.": "已存在相同的物料与仓库组合。",
			"No stock ledger entries were created. Please set the quantity or valuation rate for the items properly and try again.": "未生成物料凭证。请正确设置物料的实盘数量或成本价后重试。",
			"Difference Account must be a Asset/Liability type account, since this Stock Reconciliation is an Opening Entry": "此库存盘点调整属于开账凭证，因此差异科目必须为资产或负债类科目",
			"Row #{0}: You cannot use the inventory dimension '{1}' in Stock Reconciliation to modify the quantity or valuation rate. Stock reconciliation with inventory dimensions is intended solely for performing opening entries.": "第 {0} 行：库存盘点调整不能使用库存维度“{1}”修改数量或成本价。包含库存维度的盘点调整仅用于录入期初库存。",
			"This tool helps you to update or fix the quantity and valuation of stock in the system. It is typically used to synchronise the system values and what actually exists in your warehouses.": "此工具用于根据仓库实盘结果更新系统中的库存数量和成本价，使账面库存与实际库存保持一致。",
			"Valuation Rate required for Item {0} at row {1}": "物料 {0} 在第 {1} 行必须填写成本价",
			"Valuation rate for customer provided items has been set to zero.": "客户提供物料的成本价已设为零。",
			"The stock has been reserved for the following Items and Warehouses, un-reserve the same to {0} the Stock Reconciliation: <br /><br /> {1}": "以下物料与仓库的库存已被预留。请先取消预留，再{0}库存盘点调整：<br /><br />{1}",
			"{0} units are reserved for Item {1} in Warehouse {2}, please un-reserve the same to {3} the Stock Reconciliation.": "已预留 {0} 个单位的物料 {1}（仓库 {2}）。请先取消预留，再{3}库存盘点调整。",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_serial_batch_and_expiry_tracking_uses_reviewed_chinese_terms(self):
		translations = {
			"Serial No": "序列号",
			"Batch": "批号",
			"Batch No": "批号",
			"Serial and Batch Bundle": "序列号与批号组合",
			"Serial and Batch Entry": "序列号与批号明细",
			"Serial and Batch Nos": "序列号与批号",
			"Serial and Batch Bundle created": "已创建序列号与批号组合",
			"Serial and Batch Bundle updated": "已更新序列号与批号组合",
			"Serial and Batch No for Item Disabled": "物料未启用序列号与批号",
			"Inward": "入库",
			"Outward": "出库",
			"Type of Transaction": "出入库类型",
			"Batch Expiry Date": "批号到期日",
			"Expiry Date": "到期日",
			"Shelf Life in Days": "保质期（天）",
			"Parent Batch": "上级批号",
			"Use Batch-wise Valuation": "按批号计算成本价",
			"No stock available for this batch.": "此批号没有可用库存。",
			"If enabled, the system will allow negative stock entries for this batch, overriding the 'Allow negative stock for Batch' setting in Stock Settings. This may lead to incorrect valuation rates, so it is recommended to avoid using this option.": "启用后，系统将允许此批号出现负库存，并覆盖库存设置中的“允许批次负库存”。这可能导致成本价不准确，因此建议不要启用。",
			"At Row {0}: In Serial and Batch Bundle {1} must have docstatus as 1 and not 0": "第 {0} 行：序列号与批号组合 {1} 必须为已提交状态，不能为草稿状态",
			"Serial and Batch Bundle {0} is submitted and its entries cannot be modified.": "序列号与批号组合 {0} 已提交，其明细不能修改。",
			"Serial Nos {0} are already Delivered. You cannot use them again in Manufacture / Repack entry.": "序列号 {0} 已交付，不能再次用于生产或重新包装单据。",
			"Item Code cannot be changed for Serial No.": "序列号对应的物料编码不能更改。",
			"Warehouse cannot be changed for Serial No.": "序列号所在仓库不能直接更改。",
			"View Ledger": "查看库存台账",
			"View Ledgers": "查看库存台账",
			"AMC Expiry Date": "年度维保合同到期日",
			"Under AMC": "在年度维保合同期内",
			"Out of AMC": "已超出年度维保合同期限",
			"Warranty / AMC Details": "保修与年度维保合同信息",
			"{0} is not a CSV file.": "{0} 不是 CSV 文件。",
			"You cannot outward following {0} as either they are Delivered, Inactive or located in a different warehouse.": "以下 {0} 无法出库，因为它们已交付、已停用或位于其他仓库。",
			"You can't process the serial number {0} as it has already been used in the SABB {1}. {2} if you want to inward same serial number multiple times then enabled 'Allow existing Serial No to be Manufactured/Received again' in the {3}": "无法处理序列号 {0}，因为它已用于序列号与批号组合 {1}。{2} 如需多次入库同一序列号，请在 {3} 中启用“允许再次生产或接收现有序列号”。",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_project_timesheet_and_activity_cost_uses_reviewed_chinese_terms(self):
		translations = {
			"Activity Summary": "活动汇总",
			"Timesheet": "工时单",
			"Timesheet Detail": "工时单明细",
			"Timesheets": "工时单",
			"Activity Type": "活动类型",
			"Activity Cost": "活动成本",
			"Activity Cost per Employee": "员工活动成本",
			"Types of activities for Time Logs": "工时记录的活动类型",
			"Activity Cost exists for Employee {0} against Activity Type - {1}": "员工 {0} 已存在活动类型 {1} 的活动成本",
			"Default Activity Cost exists for Activity Type - {0}": "活动类型 {0} 已存在默认活动成本",
			"Default Billing Rate": "默认计费单价",
			"Default Costing Rate": "默认成本单价",
			"Billing Details": "计费信息",
			"Billing Hours": "计费工时",
			"Billing Rate": "计费单价",
			"Costing Rate": "成本单价",
			"Costing Amount": "成本金额",
			"Total Billable Hours": "可计费工时合计",
			"Total Billable Amount": "可计费金额合计",
			"Total Billed Hours": "已开票工时合计",
			"Total Billed Amount": "已开票金额合计",
			"Total Costing Amount": "成本金额合计",
			"Total Working Hours": "工作工时合计",
			"Base Total Billable Amount": "可计费金额合计（本币）",
			"Base Total Billed Amount": "已开票金额合计（本币）",
			"Base Total Costing Amount": "成本金额合计（本币）",
			"% Amount Billed": "已开票金额比例（%）",
			"Hrs": "工时（小时）",
			"Resume Timer": "继续计时",
			"Time Sheet": "工时单",
			"Time Sheet List": "工时单清单",
			"Timesheet Billing Summary": "工时单计费汇总",
			"Create Timesheet": "创建工时单",
			"Add Timesheets": "添加工时单",
			"Daily Timesheet Summary": "每日工时单汇总",
			"Fetch Timesheet in Sales Invoice": "允许在销售发票中获取工时单",
			"Enabling the check box will fetch timesheet on select of a Project in Sales Invoice": "勾选此复选框将在销售发票中选择项目时获取工时单",
			"Include Timesheets in Draft Status": "包含草稿状态的工时单",
			"Hide timesheets": "隐藏工时单",
			"Sales Invoice Timesheet": "销售发票工时单",
			"Timesheet {0} cannot be invoiced in its current state": "工时单 {0} 当前状态无法开票",
			"Total Billable Amount (via Timesheet)": "可计费金额合计（通过工时单）",
			"Total Costing Amount (via Timesheet)": "成本金额合计（通过工时单）",
			"To Time cannot be before from date": "结束时间不能早于开始时间",
			"Invoice can't be made for zero billing hour": "计费工时为零，无法创建发票",
			"Invoice already created for all billing hours": "所有可开票工时均已开票",
			"Row {0}: Activity Type is mandatory.": "第 {0} 行：必须填写活动类型。",
			"Row {0}: From Time and To Time is mandatory.": "第 {0} 行：必须填写开始时间和结束时间。",
			"Row {0}: From Time and To Time of {1} is overlapping with {2}": "第 {0} 行：{1} 的起止时间与 {2} 重叠",
			"Row {0}: Hours value must be greater than zero.": "第 {0} 行：工时必须大于零。",
			"Row {0}: Project must be same as the one set in the Timesheet: {1}.": "第 {0} 行：项目必须与工时单中设置的项目 {1} 一致。",
			"Warning - Row {0}: Billing Hours are more than Actual Hours": "警告：第 {0} 行的计费工时超过实际工时",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

		self._assert_translation("Billing Amount", "开票金额")
		self._assert_translation("Billing Amount", "计费金额", context="Timesheet Detail")
		self._assert_translation(
			"Billing Amount", "计费金额", context="Timesheet Billing Summary"
		)

	def test_operational_email_templates_use_reviewed_chinese_terms(self):
		self._assert_translation("Please take necessary action", "请及时处理")

	def test_project_management_reports_use_reviewed_chinese_terms(self):
		translations = {
			"Project Summary": "项目汇总",
			"Total Tasks": "任务总数",
			"Tasks Completed": "已完成任务数",
			"Tasks Overdue": "逾期任务数",
			"Completion": "完成率（%）",
			"Average Completion": "平均完成率",
			"Completed Tasks": "已完成任务",
			"Overdue Tasks": "逾期任务",
			"Daily Timesheet Summary": "每日工时单汇总",
			"From Datetime": "开始时间",
			"To Datetime": "结束时间",
			"Project wise Stock Tracking": "项目库存流转跟踪",
			"Project Id": "项目编号",
			"Cost of Purchased Items": "采购物料成本",
			"Cost of Issued Items": "发出物料成本",
			"Delivered Item Net Amount": "交付物料销售净额",
			"Estimated Cost": "预估成本",
			"Project Start Date": "项目开始日期",
			"Completion Date": "完成日期",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

		repo_root = Path(__file__).parents[2]
		report_path = (
			repo_root
			/ "erpnext/projects/report/project_wise_stock_tracking/project_wise_stock_tracking.json"
		)
		report = json.loads(report_path.read_text())
		self.assertEqual(report["report_name"], "Project wise Stock Tracking")

		report_source = (
			repo_root
			/ "erpnext/projects/report/project_wise_stock_tracking/project_wise_stock_tracking.py"
		).read_text()
		self.assertIn('_("Estimated Cost") + ":Currency:120"', report_source)
		self.assertNotIn('_("Project Value") + ":Currency:120"', report_source)

	def test_project_task_journey_has_no_known_empty_chinese_messages(self):
		translations = {
			"Create Tasks": "创建任务",
			"Parent Task {0} is not a Template Task": "父任务 {0} 不是模板任务",
			"Parent Task {0} must be a Group Task": "父任务 {0} 必须为任务组",
			"Progress % for a task cannot be more than 100.": "任务进度不能超过 100%。",
			"You are not permitted to create a Task for Project {0}": "您没有权限为项目 {0} 创建任务",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_stock_reposting_uses_reviewed_chinese_terms(self):
		translations = {
			"Current Index": "已处理项数",
			"Auto Reposting of Incorrect Valuation": "自动修复成本价错误",
			"Auto Repost Incorrect Valuation Entries (Weekly)": "每周自动重新过账成本价错误记录",
			"Enable Parallel Reposting": "启用并行重新过账",
			"Enable Separate Reposting for GL": "对会计总账单独重新过账",
			"Recalculate Valuation Rate": "重新计算成本价",
			"Repost Only Accounting Ledgers": "仅重新过账会计凭证",
			"Stock Ledgers won’t be reposted.": "物料凭证不会重新过账。",
			"Reposting Item and Warehouse": "正在重新过账物料与仓库",
			"Reposting Vouchers Progress": "凭证重新过账进度",
			"Incorrect Stock Asset Account in {0}": "{0} 中的库存资产科目不正确",
			"Posting date is required": "必须填写过账日期",
			"Only works for Purchase Receipt, Purchase Invoice and Stock Entry": "仅适用于采购入库、采购发票和物料移动",
			"Restart Failed Entries": "重新启动失败记录",
			"No account set": "未设置科目",
			"If enabled, a weekly scheduler scans the Stock Ledger Variance for item-warehouses with incorrect valuation in the current financial year and auto-creates Item & Warehouse based reposts to fix them.": "启用后，每周调度任务将扫描当前会计年度的物料凭证差异报表，找出成本价错误的物料与仓库组合，并自动创建重新过账任务进行修复。",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_accounting_reposting_uses_reviewed_chinese_terms(self):
		translations = {
			"Partially Reposted": "部分重新过账",
			"Add atleast one voucher to repost.": "至少添加一张需要重新过账的凭证。",
			"Add vouchers to generate preview.": "请添加凭证以生成预览。",
			"Cannot repost more than {0} vouchers at once. Split them into multiple documents.": "一次不能重新过账超过 {0} 张凭证。请拆分为多份单据处理。",
			"Duplicate vouchers found. Remove the duplicate vouchers to continue to repost.": "发现重复凭证。请删除重复凭证后继续重新过账。",
			"The following vouchers are not submitted: {0}": "以下凭证尚未提交：{0}",
			"Reposting can be started only for submitted document.": "只能对已提交的单据启动重新过账。",
			"Reposting cannot be started when status is {0}.": "状态为 {0} 时无法启动重新过账。",
			"Reposting is still in progress in background.": "重新过账仍在后台进行。",
			"Reposting {0} {1}": "正在重新过账 {0} {1}",
			"Scheduler is inactive. Reposting will only run once background jobs are processed.": "调度器未启用。只有在后台作业开始处理后，重新过账才会运行。",
			"{0} {1} not allowed to be reposted. You can enable it by adding it '{2}' table in {3}.": "不允许对 {0} {1} 重新过账。可将该单据类型添加到“{2}”表格（位于 {3}）以启用。",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_budget_controls_use_reviewed_chinese_terms(self):
		translations = {
			"Account is mandatory": "必须填写科目",
			"Account {0} does not belong to company {1}": "科目 {0} 不属于公司 {1}",
			"Fiscal Year {0} is not available for Company {1}.": "会计年度 {0} 不适用于公司 {1}。",
			"Another Budget record '{0}' already exists against {1} '{2}' and account '{3}' with overlapping fiscal years.": "已存在另一条预算记录“{0}”，其针对 {1}“{2}”和科目“{3}”的会计年度范围与当前记录重叠。",
			"Budget cannot be assigned against {0}, as its Root Type is not of Income or Expense": "无法为 {0} 分配预算，因为其根类型不是收入或费用",
			"Are you sure you want to revise this budget? The current budget will be cancelled and a new draft will be created.": "确定要修订此预算吗？当前预算将被取消，并创建一份新草稿。",
			"New revised budget created successfully": "已成功创建修订后的新预算",
			"Revision cancelled": "已取消修订",
			"Spending for Account {0} ({1}) between {2} and {3} has already exceeded the new allocated budget. Spent: {4}, Budget: {5}": "科目 {0}（{1}）在 {2} 至 {3} 期间的支出已超过新分配的预算。已支出：{4}，预算：{5}",
			"Total distributed amount {0} must be equal to Budget Amount {1}": "分配总额 {0} 必须等于预算金额 {1}",
			"Total distribution percent must equal 100 (currently {0})": "分配比例合计必须等于 100（当前为 {0}）",
			"{0} Budget for Account {1} against {2} {3} is {4}. It is already exceeded by {5}.": "{0}预算中，科目 {1} 针对 {2} {3} 的预算为 {4}，已超支 {5}。",
			"{0} Budget for Account {1} against {2} {3} is {4}. It will be exceeded by {5}.": "{0}预算中，科目 {1} 针对 {2} {3} 的预算为 {4}，本次操作将超支 {5}。",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_bank_statement_import_backend_uses_reviewed_chinese_terms(self):
		translations = {
			"Already Imported": "已导入",
			"This statement has already been imported.": "此对账单已导入。",
			"Detected Date Format": "识别出的日期格式",
			"Detected Amount Format": "识别出的金额格式",
			"Detected Header Index": "检测到的表头行号",
			"Detected Transaction Starting Index": "检测到的交易起始行号",
			"Detected Transaction Ending Index": "检测到的交易结束行号",
			"Amount column has \"CR\"/\"DR\" values": "金额列使用“CR”/“DR”标记",
			"Amount column has positive/negative values": "金额列使用正数/负数",
			"Transaction type column has \"Deposit\"/\"Withdrawal\" values": "交易类型列使用“Deposit”/“Withdrawal”标记",
			"Bank Statement Import Log Column Map": "银行对账单导入日志列映射",
			"PDF Tables": "PDF 表格",
			"No Tables Detected": "未检测到表格",
			"Password Required": "需要密码",
			"This PDF is password protected. Please set the correct statement password on the Bank Account and try again.": "此 PDF 受密码保护。请在银行账户中设置正确的对账单密码后重试。",
			"Bank Transaction Rule Accounts": "银行交易匹配规则科目",
			"Bank Transaction Rule Description Conditions": "银行交易匹配规则描述条件",
			"Description Rules": "描述匹配规则",
			"Regex": "正则表达式",
			"Party IBAN": "往来单位 IBAN",
			"Party account is required to create a payment entry.": "创建收付款单必须填写往来单位科目。",
			"Party type is required to create a payment entry.": "创建收付款单必须填写往来类型。",
			"You do not have permission to import bank transactions": "您没有导入银行交易的权限",
			"You do not have permission to import and submit bank transactions": "您没有导入并提交银行交易的权限",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)
			self._assert_erpnext_runtime_translation(source, translation)

	def test_transaction_deletion_uses_reviewed_safety_terms(self):
		translations = {
			"IMPORTANT: Create a backup before proceeding!": "重要：继续前务必创建备份！",
			"Warning: This action cannot be undone!": "警告：此操作无法撤销！",
			"What will be deleted:": "将删除以下内容：",
			"ALL records will be deleted (entire DocType cleared)": "将删除全部记录（清空整个单据类型）",
			"DocTypes To Delete": "待删除单据类型",
			"DocTypes that will NOT be deleted.": "不会删除的单据类型。",
			"Company Field": "公司字段",
			"Company link field name used for filtering (optional - leave empty to delete all records)": "用于按公司筛选的链接字段名（可选；留空将删除全部记录）",
			"Cannot delete protected core DocType: {0}": "无法删除受保护的核心单据类型：{0}",
			"Cannot delete virtual DocType: {0}. Virtual DocTypes do not have database tables.": "无法删除虚拟单据类型：{0}。虚拟单据类型没有数据库表。",
			"Cannot add child table {0} to deletion list. Child tables are automatically deleted with their parent DocTypes.": "无法将子表 {0} 添加到删除清单。子表会随父单据类型自动删除。",
			"Child tables that will also be deleted": "将一并删除的子表",
			"Cannot start deletion. Another deletion {0} is already queued/running. Please wait for it to complete.": "无法开始删除。另一个删除任务 {0} 已排队或正在运行，请等待其完成。",
			"Transaction Deletion Record {0} is currently deleting {1}. Cannot save documents until deletion completes.": "业务交易删除记录 {0} 正在删除 {1}。删除完成前无法保存单据。",
			"Deletion will start automatically after submission.": "提交后将自动开始删除。",
			"No DocTypes in To Delete list. Please generate or import the list before submitting.": "待删除清单中没有单据类型。请在提交前生成或导入清单。",
			"Invalid CSV format. Expected column: doctype_name": "CSV 格式无效，必须包含 doctype_name 列",
			"Only CSV files are allowed": "仅允许使用 CSV 文件",
			"File does not belong to this Transaction Deletion Record": "该文件不属于当前业务交易删除记录",
			"Field '{0}' is not a valid Company link field for DocType {1}": "字段“{0}”不是单据类型 {1} 的有效公司链接字段",
			"Multiple company fields available: {0}. Please select manually.": "可用的公司字段有多个：{0}。请手动选择。",
			"{0}: Protected DocType": "{0}：受保护的单据类型",
			"{0}: Virtual DocType (no database table)": "{0}：虚拟单据类型（无数据库表）",
			"{0}: Child table (auto-deleted with parent)": "{0}：子表（随父单据自动删除）",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_material_planning_and_picking_use_reviewed_chinese_terms(self):
		translations = {
			"Auto Created (Reorder)": "自动创建（再订购）",
			"Projected On Hand": "预计在手库存",
			"If the reorder check is set at the Group warehouse level, the available quantity becomes the sum of the projected quantities of all its child warehouses.": "若在仓库组层级设置再订购检查，可用数量将按其所有子仓库的预计数量汇总计算。",
			"A separate Purchase Order is created for each Supplier.": "每个供应商将分别创建一张采购订单。",
			"Item rates have been updated based on the selected Buying Price List {0}": "已根据所选采购价格表 {0} 更新物料单价",
			"Item {0} cannot be ordered more than once": "物料 {0} 不能重复下单",
			"Select Supplier for Items": "为物料选择供应商",
			"Select a Supplier for Item {0}": "请为物料 {0} 选择供应商",
			"Select at least one Item": "请至少选择一个物料",
			"Set Supplier for All Items": "为所有物料设置供应商",
			"{0} was set to today for items whose requested date has passed": "对请求日期已过期的物料，已将 {0} 设为今天",
			"Partially Transferred": "部分已调拨",
			"Transferred Qty (in Stock UOM)": "已调拨数量（库存单位）",
			"% of materials delivered against this Pick List": "本拣货单的物料交付百分比",
			"All picked items have already been transferred against this Pick List": "此拣货单中的所有已拣物料均已调拨",
			"Missing Warehouse": "缺少仓库",
			"Row {0}: Warehouse is required": "第 {0} 行：必须填写仓库",
			"Row {0}: Warehouse {1} is linked to company {2}. Please select a warehouse belonging to company {3}.": "第 {0} 行：仓库 {1} 关联的公司为 {2}。请选择属于公司 {3} 的仓库。",
			"Quantity for Item {0} must be greater than zero and cannot exceed {1}": "物料 {0} 的数量必须大于零且不能超过 {1}",
			"{0} units of Item {1} is not available in any of the warehouses. Other Pick Lists exist for this item.": "任何仓库中均无法提供 {0} 个单位的物料 {1}，且该物料还存在其他拣货单。",
			"Cannot declare as Lost because an active Quotation exists.": "存在有效报价单，无法将此商机标记为未成交。",
			"Row #{0}: Quantity must be greater than 0 for Item {1}": "第 {0} 行：物料 {1} 的数量必须大于 0",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_manufacturing_execution_uses_reviewed_chinese_terms(self):
		translations = {
			"Production Item Info": "生产物料信息",
			"Additional Costs (as per BOM)": "额外费用（按物料清单）",
			"Work Order Additional Item": "生产工单附加物料",
			"Allow Editing of Items and Quantities in Work Order": "允许编辑生产工单中的物料和数量",
			"If enabled, the system will allow users to edit the raw materials and their quantities in the Work Order. The system will not reset the quantities as per the BOM, if the user has changed them.": "启用后，用户可编辑生产工单中的原材料及其数量。用户修改后，系统不会再按物料清单重置这些数量。",
			"Set Operating Cost / Secondary Items From Sub-assemblies": "从半成品设置工费成本 / 副产品",
			"Secondary Items": "副产品",
			"Secondary Items (as per BOM)": "副产品（按物料清单）",
			"Secondary Items (as per Manufacture Entries)": "副产品（按生产入库单）",
			"Job Card Secondary Item": "生产任务单副产品",
			"BOM Secondary Item Reference": "物料清单副产品引用",
			"Source Manufacture Entry": "来源生产入库单",
			"Serial / Batch": "序列号 / 批号",
			"Job Card On Hold": "生产任务单已暂停",
			"Cancelled Job Card cannot be processed.": "已取消的生产任务单无法处理。",
			"Submitted Job Card cannot be processed.": "已提交的生产任务单无法继续处理。",
			"Cannot submit Job Card {0} while it is On Hold. Please resume and complete the job before submission.": "生产任务单 {0} 处于暂停状态时不能提交。请恢复并完成作业后再提交。",
			"Process loss quantity cannot be negative.": "制程损耗数量不能为负数。",
			"Quality Inspection is required for the item {0} before completing the job card {1}": "物料 {0} 必须完成质量检验，才能完成生产任务单 {1}",
			"Quality Inspection {0} is not submitted for the item: {1}": "质检单 {0} 尚未针对物料 {1} 提交",
			"Quality Inspection {0} is rejected for the item: {1}": "质检单 {0} 针对物料 {1} 的检验未通过",
			"The completed quantity {0} of an operation {1} cannot be greater than the completed quantity {2} of a previous operation {3}.": "完成数量 {0}（工序 {1}）不能大于完成数量 {2}（上一道工序 {3}）。",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_bom_configuration_uses_reviewed_chinese_terms(self):
		translations = {
			"BOM Configuration": "物料清单配置",
			"Components": "组件",
			"Consume Components": "组件消耗",
			"The final item that will be produced using this BOM.": "使用此物料清单最终生产的物料。",
			"Quantity (Output Qty)": "数量（产出数量）",
			"How many units of the final product this BOM makes.": "此物料清单可生产的最终产品数量。",
			"Unit Of Measure": "计量单位",
			"Cost Allocation": "成本分摊",
			"% Cost Allocation": "成本分摊比例（%）",
			"Cost Allocation %": "成本分摊比例（%）",
			"Cost Allocation / Process Loss": "成本分摊 / 制程损耗",
			"Cost allocation between finished goods and secondary items should equal 100%": "产成品和副产品之间的成本分摊比例合计必须等于 100%",
			"Secondary Items Cost": "副产品成本",
			"Secondary Items Cost (Company Currency)": "副产品成本（本币）",
			"Is Phantom BOM": "虚拟物料清单",
			"Is Phantom Item": "虚拟物料",
			"Phantom Item": "虚拟物料",
			"Non-phantom BOM cannot be created for non-stock item {0}.": "不能为非库存物料 {0} 创建非虚拟物料清单。",
			"Phantom BOM cannot be created for stock item {0}.": "不能为库存物料 {0} 创建虚拟物料清单。",
			"Users can make manufacture entry against Job Cards": "用户可根据生产任务单创建生产入库单",
			"Controls how raw materials are consumed during the ‘Manufacture’ stock entry.": "控制在“生产入库”物料移动中如何消耗原材料。",
			"If you want to run operations in parallel, keep the same sequence ID for them.": "如需并行执行多道工序，请为它们设置相同的顺序编号。",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_doctype_inventory_follows_nested_child_tables(self):
		documents = {
			"Root": (None, {"fields": [{"fieldtype": "Table", "options": "Child"}]}),
			"Child": (None, {"fields": [{"fieldtype": "Table", "options": "Grandchild"}]}),
			"Grandchild": (None, {"fields": []}),
		}

		self.assertEqual(self._doctype_closure(documents, {"Root"}), {"Root", "Child", "Grandchild"})

	def test_china_compliance_controls_use_reviewed_terms(self):
		translations = {
			"Clearance date changed from {0} to {1} via Bank Clearance Tool": "已通过银行清账工具将清账日期从 {0} 更改为 {1}",
			"Stock Closing Entry In Progress": "库存结转分录处理中",
			"When there are multiple finished goods ({0}) in a Repack stock entry, the basic rate for all finished goods must be set manually. To set rate manually, enable the checkbox 'Set Basic Rate Manually' in the respective finished good row.": "重新包装库存单中存在多个成品（{0}）时，必须手动设置所有成品的单价。请在对应成品行中启用“手动设置成本”。",
			"Process Period Closing Voucher Detail": "期末结账凭证处理明细",
			"Role allowed to bypass period restrictions.": "允许绕过会计期间限制的角色。",
			"Accounting entries are frozen up to this date. Only users with the specified role can create or modify entries before this date.": "截至该日期的会计分录均已冻结；只有拥有指定角色的用户才能创建或修改该日期之前的分录。",
			"Roles Allowed to Set and Edit Frozen Account Entries": "允许设置和编辑冻结会计分录的角色",
			"Determine Address Tax Category from": "税类判定所依据的地址",
			"Role Allowed to over bill ": "允许超额开票的角色",
			"Role Allowed to Bypass Over Billing Restriction": "允许绕过逾期超额开票限制的角色",
			"Use legacy controller for Period Closing Voucher": "期末结账凭证使用旧版控制器",
			"PCV Job Timeout (seconds)": "期末结账凭证任务超时（秒）",
			"Automatically run rules on unreconciled transactions": "对未对账交易自动运行规则",
			"Action if same rate is not maintained throughout internal transaction": "内部交易未保持相同单价时的处理方式",
			"Maintain same rate throughout internal Transaction": "内部交易全程保持相同单价",
			"Fetch valuation rate for internal Transaction": "内部交易获取成本价",
			"Check if this tax is not applicable to items (distinct from 0% rate)": "勾选表示此税种不适用于该物料（不同于 0% 税率）",
			"PCV": "期末结账凭证（PCV）",
			"Running": "运行中",
			"Tax withheld only for amount exceeding cumulative threshold": "仅对超过累计起征额的部分代扣税款",
			"When checked, only cumulative threshold will be applied": "勾选后，仅应用累计起征额",
			"When checked, only transaction threshold will be applied for transaction individually": "勾选后，仅对每笔交易单独应用单笔起征额",
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
			"Timesheet {0} cannot be invoiced in its current state": "工时单 {0} 当前状态无法开票",
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
			"Inward Order": "受托加工订单",
			"Item-wise sales Register": "物料销售台账",
			"Items To Be Received": "待收货委外成品",
			"Manufactured Items Value": "完工物料价值",
			"Material Planning": "物料计划",
			"Materials To Be Transferred": "待调拨委外原材料",
			"Outward Order": "委外发料订单",
			"Quality Inspections": "质检单",
			"Reconciliation Statement": "银行对账单",
			"Subcontracting Inward Order Count": "受托加工订单数量",
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
			"Auto User Creation Error": "自动创建用户失败",
			"Company Account is mandatory": "必须填写总账科目",
			"Company or Personal Email is mandatory when 'Create User Automatically' is enabled": "启用“自动创建用户”时，必须填写公司邮箱或个人邮箱",
			"Email is required to create a user": "创建用户必须填写邮箱",
			"Email is required to create a user.": "创建用户必须填写邮箱。",
			"Employee is required": "必须填写员工",
			"Employee {0} already has a linked user": "员工 {0} 已关联用户",
			"Employee {0} not found": "未找到员工 {0}",
			"Import Employees": "导入员工",
			"Included fee is bigger than the withdrawal itself.": "已计入手续费不能大于支出金额。",
			"Interest on Fixed Deposits": "定期存款利息",
			"Missing Parameter": "缺少参数",
			"Only one of Deposit or Withdrawal should be non-zero when applying an Excluded Fee.": "应用未计入手续费时，存入金额和支出金额只能有一项非零。",
			"Optional. Used with Financial Report Template": "可选。用于财务报表模板。",
			"The Excluded Fee is bigger than the Deposit it is deducted from.": "未计入手续费不能大于其扣减的存入金额。",
			"The account type of {0} cannot be changed from {1} because stock ledger entries exist against it.": "{0} 的科目类型不能从 {1} 更改，因为该科目已有库存总账记录。",
			"Variant {0} and its template {1} cannot both be added to the same Pricing Rule": "变体物料 {0} 及其模板 {1} 不能同时添加到同一条定价规则中",
			"Extended Bank Statement": "银行流水扩展信息",
			"Included Fee": "已计入手续费",
			"Excluded Fee": "未计入手续费",
			"On save, the Excluded Fee will be converted to an Included Fee.": "保存时，未计入手续费将转换为已计入手续费。",
			"Create User Automatically": "自动创建用户",
			"Creates a User account for this employee using the Preferred, Company, or Personal email.": "使用员工的首选、公司或个人邮箱为其创建用户账户。",
			"Transaction": "交易",
			"Weight": "权重",
			"Disable": "禁用",
			"Used with Financial Report Template": "用于财务报表模板",
			"Statement PDF Password": "对账单 PDF 密码",
			"Password used to open password-protected PDF statements for this account. Stored encrypted.": "用于打开该账户受密码保护的 PDF 对账单；密码将加密保存。",
			"If checked, journal entries made using bank reconciliation will be of type \"Credit Card Entry\"": "勾选后，通过银行对账创建的日记账分录类型将为“信用卡分录”。",
			"Template Name": "模板名称",
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

	def test_buying_and_selling_settings_use_reviewed_chinese_terms(self):
		translations = {
			"Action if same rate is not maintained": "未保持相同单价时的处理方式",
			"Action if same rate is not maintained throughout sales cycle": "销售全流程未保持相同单价时的处理方式",
			"Allow Sales Order creation for expired Quotation": "允许从已过期报价单创建销售订单",
			"Allow editing Price List rate in transactions": "允许在交易单据中修改价目表单价",
			"Allow multiple Sales Orders against a customer's Purchase Order": "允许同一客户采购订单对应多张销售订单",
			"Backflush raw materials of subcontract based on": "委外原材料倒冲依据",
			"Bill for rejected quantity in Purchase Invoice": "采购发票包含拒收数量",
			"Blanket Orders": "框架订单",
			"Disable last purchase rate": "禁用最近采购单价",
			"Enable discount accounting for selling": "启用销售折扣核算",
			"Is Delivery Note required to create Sales Invoice?": "创建销售发票前是否必须有送货单？",
			"Is Purchase Order required for Purchase Invoice & Receipt creation?": "创建采购发票和采购入库单前是否必须有采购订单？",
			"Maintain same rate throughout sales cycle": "销售全流程保持相同单价",
			"Maintain same rate throughout the purchase  cycle": "采购全流程保持相同单价",
			"Over Order Allowance (%)": "超订容差（%）",
			"Validate selling price for Item against purchase or valuation rate": "根据采购单价或估值单价校验物料销售单价",
			"Zero-Quantity Line Items": "零数量明细行",
		}

		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def test_banking_frontend_visible_copy_uses_the_translation_catalog(self):
		translations = {
			"Loading...": "正在加载……",
			"Date/Transaction Date/Value Date": "日期/交易日期/记账日期",
			"Withdrawal/Deposit": "支出/收入",
			"Description/Particulars/Remarks/Narration/Detail": "摘要/用途/备注/附言/明细",
			"Reference/Ref/Transaction ID/Cheque/Check": "参考号/交易编号/支票号",
			"The following documents will be cancelled:": "以下单据将被取消：",
			"Get Unpaid Invoices": "获取未结发票",
			"Select Invoices": "选择发票",
			"Unpaid invoices from {0} for {1}.": "{0} 的未结发票，待分配金额为 {1}。",
			"Invoices": "发票",
			"Other Charges / Deductions": "其他费用/扣减",
			"Clear Filters": "清除筛选条件",
			"or": "或",
			"For more information, open the Bank Reconciliation Statement tab below.": "如需查看更多信息，请打开下方的“银行对账单”页签。",
			"More": "更多",
			"Banking": "银行",
			"Beta": "测试版",
			"This screen is not supported on mobile devices.": "该功能暂不支持移动端操作。",
			"Go to Desktop": "返回工作台",
			"Match and Reconcile": "匹配并核销",
			"Bank Reconciliation Statement": "银行对账单",
			"Bank Transactions": "银行流水",
			"Bank Clearance Summary": "银行清账汇总表",
			"Incorrectly Cleared Entries": "清账日期异常分录",
			"No bank accounts found": "未找到银行账户",
			"You have not added any bank accounts to your company.": "当前公司尚未添加银行账户。",
			"Configure Bank Accounts": "配置银行账户",
			"Select {0}": "选择 {0}",
			"GL Account": "总账科目",
			"Last Synced Transaction": "最近同步流水",
			"Select a bank account to reconcile": "请选择要核销的银行账户",
			"Unreconciled Transactions": "待核销流水",
			"Match or Create": "匹配或新建单据",
			"Search transactions": "搜索银行流水",
			"Filter by amount": "按金额筛选",
			"Debits": "支出",
			"Credits": "收入",
			"No transactions found for the given filters.": "未找到符合筛选条件的流水。",
			"No unreconciled transactions found": "没有待核销流水",
			"Try adjusting your search or filter criteria.": "请调整搜索内容或筛选条件。",
			"Import your bank statement to get started.": "请先导入银行对账单。",
			"Import Bank Statement": "导入银行对账单",
			"result": "条结果",
			"results": "条结果",
			"Ref": "参考号",
			"Matched by rule": "已按规则匹配",
			"Unallocated": "未分配",
			"No results found.": "未找到匹配结果。",
			"Invoice No": "发票编号",
			"Bank GL Account": "银行总账科目",
			"e.g.": "例如",
		}
		for source, translation in translations.items():
			self._assert_translation(source, translation)

	def _assert_translation(self, source, translation, context=None):
		with self.subTest(source=source, context=context):
			message = self.catalog.get(source, context=context)
			self.assertIsNotNone(message)
			self.assertNotIn("fuzzy", message.flags)
			self.assertEqual(message.string, translation)
			self.assertTrue(self._message_is_valid(message), [str(error) for error in message.check()])
			self.assertEqual(
				self._format_fields(source),
				self._format_fields(translation),
			)

	def _assert_erpnext_runtime_translation(self, source, translation):
		with self.subTest(runtime_source=source):
			message = self.merged_erpnext_catalog.get(source)
			self.assertIsNotNone(message)
			self.assertNotIn("fuzzy", message.flags)
			self.assertEqual(message.string, translation)
			self.assertTrue(self._message_is_valid(message), [str(error) for error in message.check()])

	def _assert_frappe_translation(self, source, translation):
		with self.subTest(source=source):
			message = self.merged_frappe_catalog.get(source)
			self.assertIsNotNone(message)
			self.assertNotIn("fuzzy", message.flags)
			self.assertEqual(message.string, translation)
			self.assertTrue(self._message_is_valid(message), [str(error) for error in message.check()])

	@staticmethod
	def _doctype_closure(documents, roots):
		targets = set()
		pending = list(roots)
		while pending:
			doctype = pending.pop()
			if doctype in targets:
				continue
			targets.add(doctype)
			pending.extend(
				field["options"]
				for field in documents[doctype][1].get("fields", [])
				if field.get("fieldtype") in {"Table", "Table MultiSelect"}
				and field.get("options") in documents
			)
		return targets

	@staticmethod
	def _format_fields(value):
		return [field for _, field, _, _ in Formatter().parse(value) if field]

	@staticmethod
	def _message_is_valid(message):
		return message.id in BABEL_LITERAL_PERCENT_MESSAGES or not message.check()

	@classmethod
	def _is_usable_translation(cls, message, source):
		if not message or "fuzzy" in message.flags or not cls._message_is_valid(message):
			return False
		translations = message.string if isinstance(message.string, (list, tuple)) else [message.string]
		if not translations or not all(translations):
			return False
		if source in ERPNext_IDENTITY_TRANSLATION_ALLOWLIST:
			return all(translation == source for translation in translations)
		if source in ERPNext_APPROVED_NON_CJK_TRANSLATIONS:
			return translations == [ERPNext_APPROVED_NON_CJK_TRANSLATIONS[source]]
		return all(re.search(r"[\u3400-\u9fff]", translation) for translation in translations)
