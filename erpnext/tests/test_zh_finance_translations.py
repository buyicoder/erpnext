import ast
import json
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
	"Customer",
	"Delivery Note",
	"Item",
	"Journal Entry",
	"Payment Entry",
	"Project",
	"Purchase Invoice",
	"Purchase Order",
	"Purchase Receipt",
	"Sales Invoice",
	"Sales Order",
	"Stock Entry",
	"Supplier",
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
	"Bank",
	"Bank Clearance",
	"Bank Statement Import",
	"Bank Transaction",
	"Branch",
	"Brand",
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
	"Shipping Rule",
	"Task Type",
	"Territory",
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
	"% of materials billed against this Sales Order",
	"% of materials delivered against this Sales Order",
	"Check if this tax is not applicable to items (distinct from 0% rate)",
	"In this case, the amount will be calculated as 25% of the transaction amount. If the transaction amount is 200, then this will be calculated as 200 * 0.25 = 50.",
	"{0}% of total invoice value will be given as discount.",
}


class TestZhFinanceTranslations(TestCase):
	maxDiff = None

	@classmethod
	def setUpClass(cls):
		po_path = Path(__file__).parents[1] / "locale" / "zh.po"
		cls.catalog = read_po(BytesIO(po_path.read_bytes()), locale="zh")
		repo_root = Path(__file__).parents[2]
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
				repo_root / ".build/frappe-v16.24.4-zh.po",
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

	def test_asset_and_manufacturing_onboarding_has_no_untranslated_visible_copy(self):
		erpnext_root = Path(__file__).parents[1]
		roots = (
			erpnext_root / "assets/module_onboarding",
			erpnext_root / "assets/onboarding_step",
			erpnext_root / "manufacturing/module_onboarding",
			erpnext_root / "manufacturing/onboarding_step",
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
		}

		for source, translation in translations.items():
			self._assert_frappe_translation(source, translation)

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

	def _assert_translation(self, source, translation):
		with self.subTest(source=source):
			message = self.catalog.get(source)
			self.assertIsNotNone(message)
			self.assertNotIn("fuzzy", message.flags)
			self.assertEqual(message.string, translation)
			self.assertTrue(self._message_is_valid(message), [str(error) for error in message.check()])
			self.assertEqual(
				self._format_fields(source),
				self._format_fields(translation),
			)

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
