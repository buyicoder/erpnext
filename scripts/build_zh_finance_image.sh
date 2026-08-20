#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(git -C "$script_dir/.." rev-parse --show-toplevel)"
source "$script_dir/frappe_zh_baseline.conf"
image="${1:-buyicoder/erpnext-cn:v16.32.3-zh-finance}"
if [[ -n "$(git -C "$repo_root" status --porcelain --untracked-files=all)" ]]; then
	printf '%s\n' "Refusing to build from a dirty worktree; commit the release inputs first." >&2
	exit 1
fi
source_commit="$(git -C "$repo_root" rev-parse HEAD)"

"$repo_root/scripts/fetch_frappe_zh_baseline.sh"

docker build \
	--pull=false \
	--file "$repo_root/docker/zh-finance/Containerfile" \
	--build-arg "SOURCE_COMMIT=$source_commit" \
	--tag "$image" \
	"$repo_root"

docker run --rm --entrypoint sh \
	--env "FRAPPE_RUNTIME_VERSION=$FRAPPE_RUNTIME_VERSION" \
	--mount "type=bind,src=$repo_root/erpnext/tests/test_subcontracting_order_i18n.py,dst=/tmp/test_subcontracting_order_i18n.py,readonly" \
	--mount "type=bind,src=$repo_root/erpnext/tests/test_maintenance_schedule_i18n.py,dst=/tmp/test_maintenance_schedule_i18n.py,readonly" \
	--mount "type=bind,src=$repo_root/erpnext/tests/test_inventory_dimension_i18n.py,dst=/tmp/test_inventory_dimension_i18n.py,readonly" \
	--mount "type=bind,src=$repo_root/erpnext/tests/test_stock_entry_i18n.py,dst=/tmp/test_stock_entry_i18n.py,readonly" \
	--mount "type=bind,src=$repo_root/erpnext/tests/test_serial_batch_bundle_i18n.py,dst=/tmp/test_serial_batch_bundle_i18n.py,readonly" \
	--mount "type=bind,src=$repo_root/erpnext/tests/test_item_price_i18n.py,dst=/tmp/test_item_price_i18n.py,readonly" \
	--mount "type=bind,src=$repo_root/erpnext/tests/test_purchase_receipt_i18n.py,dst=/tmp/test_purchase_receipt_i18n.py,readonly" \
	--mount "type=bind,src=$repo_root/erpnext/tests/test_repost_item_valuation_i18n.py,dst=/tmp/test_repost_item_valuation_i18n.py,readonly" \
	--mount "type=bind,src=$repo_root/erpnext/tests/test_promotional_scheme_i18n.py,dst=/tmp/test_promotional_scheme_i18n.py,readonly" \
	--mount "type=bind,src=$repo_root/erpnext/tests/test_taxes_and_totals_i18n.py,dst=/tmp/test_taxes_and_totals_i18n.py,readonly" \
	--mount "type=bind,src=$repo_root/erpnext/tests/test_process_statement_i18n.py,dst=/tmp/test_process_statement_i18n.py,readonly" \
	--mount "type=bind,src=$repo_root/erpnext/tests/test_currency_exchange_settings_i18n.py,dst=/tmp/test_currency_exchange_settings_i18n.py,readonly" \
	--mount "type=bind,src=$repo_root/erpnext/tests/test_selling_controller_i18n.py,dst=/tmp/test_selling_controller_i18n.py,readonly" \
	--mount "type=bind,src=$repo_root/erpnext/tests/test_buying_controller_i18n.py,dst=/tmp/test_buying_controller_i18n.py,readonly" \
	--mount "type=bind,src=$repo_root/erpnext/tests/test_repost_accounting_ledger_i18n.py,dst=/tmp/test_repost_accounting_ledger_i18n.py,readonly" \
	--mount "type=bind,src=$repo_root/erpnext/tests/test_tax_report_labels_i18n.py,dst=/tmp/test_tax_report_labels_i18n.py,readonly" \
	"$image" -s <<'VERIFY_SCRIPT'
	set -eu
	/home/frappe/frappe-bench/env/bin/python - <<'PY'
import ast
import json
import os
import re
import sys
from gettext import GNUTranslations
from pathlib import Path

sys.path.insert(0, "/home/frappe/frappe-bench/apps/frappe")
import frappe

expected_frappe_version = os.environ["FRAPPE_RUNTIME_VERSION"]
if frappe.__version__ != expected_frappe_version:
	raise SystemExit(
		f"Frappe runtime/catalog version mismatch: runtime={frappe.__version__}, "
		f"catalog={expected_frappe_version}"
	)
print(f"Verified Frappe runtime/catalog version {expected_frappe_version}")

asset_root = Path("/home/frappe/frappe-bench/assets")
manifest = json.loads((asset_root / "assets.json").read_text())
missing = [path for path in manifest.values() if isinstance(path, str) and path.startswith("/assets/") and not (asset_root / path.removeprefix("/assets/")).is_file()]
if missing:
	raise SystemExit("Asset manifest references missing files: " + ", ".join(missing))
print(f"Verified {len(manifest)} asset manifest entries")

form_sidebar_source = Path(
	"/home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/form/templates/form_sidebar.html"
).read_text()
translated_single_title = "frm.meta.issingle ? __(frappe.utils.html2text(title)) : frappe.utils.html2text(title)"
if translated_single_title not in form_sidebar_source:
	raise SystemExit("Single DocType sidebar titles are not translated in the final image")
print("Verified translated Single DocType sidebar titles")

sidebar_item_source = Path(
	"/home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/ui/sidebar/sidebar_item.html"
).read_text()
translated_standard_sidebar_label = "item.standard ? __(item.label) : item.label"
if sidebar_item_source.count(translated_standard_sidebar_label) != 3:
	raise SystemExit("Standard workspace sidebar labels are not translated in the final image")
print("Verified translated standard workspace sidebar labels")

demo_root = Path("/home/frappe/frappe-bench/apps/erpnext/erpnext/setup/demo_data")
demo_items = json.loads((demo_root / "item.json").read_text())
demo_customers = json.loads((demo_root / "customer.json").read_text())
demo_suppliers = json.loads((demo_root / "supplier.json").read_text())
demo_item_groups = json.loads((demo_root / "item_group.json").read_text())
demo_customer_groups = json.loads((demo_root / "customer_group.json").read_text())
demo_supplier_groups = json.loads((demo_root / "supplier_group.json").read_text())
demo_sales_orders = json.loads((demo_root / "sales_order.json").read_text())
demo_purchase_orders = json.loads((demo_root / "purchase_order.json").read_text())
if demo_items[0]["item_name"] != "T恤" or demo_items[-1]["item_name"] != "相机":
	raise SystemExit("Bundled item demo data is not localized")
if {row["customer_name"] for row in demo_customers} != {
	"格兰特塑料有限公司",
	"西景软件有限公司",
	"帕尔默制造有限公司",
}:
	raise SystemExit("Bundled customer demo data is not localized")
item_codes = {row["item_code"] for row in demo_items}
customer_names = {row["customer_name"] for row in demo_customers}
supplier_names = {row["supplier_name"] for row in demo_suppliers}
item_groups = {row["item_group_name"] for row in demo_item_groups}
customer_groups = {row["customer_group_name"] for row in demo_customer_groups}
supplier_groups = {row["supplier_group_name"] for row in demo_supplier_groups}
if not all(row["item_group"] in item_groups for row in demo_items):
	raise SystemExit("Bundled item demo groups are inconsistent")
if not all(row["customer_group"] in customer_groups for row in demo_customers):
	raise SystemExit("Bundled customer demo groups are inconsistent")
if not all(row["supplier_group"] in supplier_groups for row in demo_suppliers):
	raise SystemExit("Bundled supplier demo groups are inconsistent")
if not all(order["customer"] in customer_names for order in demo_sales_orders):
	raise SystemExit("Bundled sales-order demo customers are inconsistent")
if not all(order["supplier"] in supplier_names for order in demo_purchase_orders):
	raise SystemExit("Bundled purchase-order demo suppliers are inconsistent")
if not all(
	row["item_code"] in item_codes
	for order in demo_sales_orders + demo_purchase_orders
	for row in order["items"]
):
	raise SystemExit("Bundled transaction demo items are inconsistent")
print("Verified bundled Chinese demo data")

expected_translations = {
	"My own business": "我的企业",
	"A company I work for": "我所在的公司",
	"A client I'm consulting for": "我服务的客户",
	"Retail": "零售",
	"Wholesale / Distribution": "批发 / 分销",
	"E-commerce": "电子商务",
	"Services / Consulting": "服务 / 咨询",
	"Construction / Real Estate": "建筑 / 房地产",
	"Technology / Software": "科技 / 软件",
	"Healthcare": "医疗健康",
	"Food & Beverage": "餐饮",
	"Other": "其他",
	"Excel / Spreadsheets": "Excel / 电子表格",
	"Nothing yet - starting fresh": "尚未使用，准备从零开始",
	"Standard": "标准",
	"Standard with Numbers": "标准（带编号）",
	"Zero Balance Journal: {0}": "零余额日记账凭证：{0}",
	"Revaluation Journal: {0}": "汇率重估日记账凭证：{0}",
	"Row #{0}: Item Code is Mandatory": "第 {0} 行：必须填写物料号",
	"Stock Entry Type {0} cannot be set as standard": "移动类型 {0} 不能设为标准类型",
	"Starting a background job to create {0} {1}": "正在后台创建 {0} 个{1}",
	"New issue created: {0}": "已创建新问题：{0}",
	"Create Visit": "创建维护巡修",
	"ERPNext Certification": "ERPNext 认证",
	"Certification price is 20,000 INR / 300 USD.": "认证费用为 20,000 印度卢比或 300 美元。",
	"You must first sign up and login to apply for certification.": "申请认证前，请先注册并登录。",
	"Sign Up": "注册",
	"Certification History": "认证记录",
	"Certification ID": "认证编号",
	"Your certification has expired. Click on the button below to start a new certification.": "您的认证已过期。请点击下方按钮开始新的认证。",
	"Your certification is due to expire soon. Click on the button below to start a new certification.": "您的认证即将到期。请点击下方按钮开始新的认证。",
	"Not In Stock": "库存不足",
	"{0} star": "{0} 星",
	"{0} percent of reviews have a {1}-star rating": "{0}% 的评价为 {1} 星",
	"No open tasks": "暂无未完成任务",
	"No completed tasks": "暂无已完成任务",
	"No open issues": "暂无未解决问题",
	"No completed issues": "暂无已解决问题",
	"Raw Materials": "原材料",
	"Invoicing": "开票管理",
	"Payments": "付款",
	"Financial Reports": "财务报表",
	"Accounts Setup": "会计设置",
	"Taxes": "税",
	"Banking": "银行",
	"Budget": "预算",
	"Share Management": "股份管理",
	"Subscription": "订阅",
	"Cannot apply TDS against multiple parties in one entry": "单笔分录不能对多个往来方应用税款扣缴",
	"TDS / withholding tax category applied when paying this supplier": "向该供应商付款时适用的代扣代缴税款类别",
	"TDS/TCS is calculated at the rate defined here on every payment from this customer.": "收到该客户每笔付款时，均按此处定义的税率计算代收代缴税款。",
	"Tax Withholding": "税款扣缴",
	"Adjustment based on Purchase Invoice rate": "根据采购发票单价调整",
	"Base Amount": "本币金额",
	"Base Rate": "本币单价",
	"If enabled, the system will use the moving average valuation method to calculate the valuation rate for the batched items and will not consider the individual batch-wise incoming rate.": "启用后，系统将按移动平均法计算批次物料成本价，不再按各批次入库单价分别计算。",
	"This table is used to set details about the 'Item', 'Qty', 'Basic Rate', etc.": "用于设置“物料”“数量”“单价”等明细。",
	"(I) Valuation Rate": "(I) 成本价",
	"(J) Valuation Rate as per FIFO": "(J) 先进先出成本价",
	"Cannot deduct when category is for 'Valuation' or 'Valuation and Total'": "费用类别为“计入成本”或“计入成本及总计”时不能抵扣。",
	"Enable this to block transactions where the selling price is less than the purchase or valuation rate": "启用后，销售单价低于采购单价或成本价时将阻止交易",
	"If checked, the entire amount (e.g. Freight) is allocated to the valuation of stock & asset items only. If unchecked, the amount is distributed across all items and the portion belonging to non-stock items is not added to valuation.": "勾选后，全部金额（如运费）仅计入库存物料和资产物料成本；不勾选时，金额分摊至全部物料，非库存物料对应金额不计入成本。",
	"Opening Stock entry created with zero valuation rate: {0}": "已创建成本价为零的期初库存物料移动：{0}",
	"Row #{idx}: Item rate has been updated as per valuation rate since its an internal stock transfer.": "第 {idx} 行：这是内部库存调拨，物料单价已按成本价更新。",
	"Row {0}: Item rate has been updated as per valuation rate since its an internal stock transfer": "第 {0} 行：这是内部库存调拨，物料单价已按成本价更新。",
	"Set valuation rate for rejected Materials": "为拒收物料设置成本价",
	"Used to create an opening Stock Entry with the Valuation Rate when the item is saved": "保存物料时，使用成本价创建期初库存物料移动。",
	"Validate selling price for Item against purchase or valuation rate": "根据采购单价或成本价校验物料销售单价",
	"Valuation": "计入成本",
	"Valuation (I - K)": "成本价（I-K）",
	"Valuation Field Type": "成本价字段类型",
	"Valuation and Total": "计入成本及总计",
	"Valuation rate for the item as per Sales Invoice (Only for Internal Transfers)": "按销售发票确定物料成本价（仅用于内部调拨）",
	"Valuation type charges can not be marked as Inclusive": "计入成本类费用不能标记为价内税",
	"Valuation type charges can not marked as Inclusive": "计入成本类费用不能标记为价内税",
	"Accounting Dimensions ": "辅助核算 ",
	"Enable Accounting Dimensions": "启用辅助核算",
	"Enable cost center, projects and other custom accounting dimensions": "启用成本中心、项目及其他自定义辅助核算",
	"Invalid Accounting Dimension": "无效的辅助核算",
	"Mandatory Accounting Dimension": "必填辅助核算",
	"Not allowed to create accounting dimension for {0}": "不允许为 {0} 创建辅助核算",
	"Offsetting for Accounting Dimension": "辅助核算抵销",
	"Please create a new Accounting Dimension if required.": "如有需要，请新建辅助核算。",
	"Please set Accounting Dimension {} in {}": "请在 {} 中设置辅助核算 {}",
	"Select Accounting Dimension.": "请选择辅助核算。",
	"{0} is a mandatory Accounting Dimension. <br>Please set a value for {0} in Accounting Dimensions section.": "{0} 是必填辅助核算。<br>请在辅助核算区域设置 {0} 的值。",
	"{0} is not a valid Accounting Dimension.": "{0} 不是有效的辅助核算。",
	"Bank Account No": "银行账号",
	"Exchange Gain/Loss amount has been booked through {0}": "已通过日记账凭证 {0} 登记汇兑损益金额",
	"Not allowed to update stock transactions older than {0}": "不能更新早于 {0} 的库存交易",
	"Row {0}: {1} account already applied for Accounting Dimension {2}": "第 {0} 行：科目 {1} 已用于辅助核算 {2}",
	"Row {0}: {1} {2} cannot be same as {3} (Party Account) {4}": "第 {0} 行：{1} {2} 不能与 {3}（往来科目）{4} 相同",
	"Serial No Ledger": "序列号台账",
	"Setting Events to {0}, since the Employee attached to the below Sales Persons does not have a User ID{1}": "已将事件设为 {0}，因为以下业务员关联的员工没有用户账号{1}",
	"Stock transactions that are older than the mentioned days cannot be modified.": "早于所设天数的库存交易不能修改。",
	"Accounts Settings": "会计设置",
	"Please submit Purchase Order {0} before proceeding.": "请先提交采购订单 {0}，再继续操作。",
	"Cannot create more Subcontracting Orders against the Purchase Order {0}.": "无法再基于采购订单 {0} 创建委外订单。",
	"Reserve Warehouse must be different from Supplier Warehouse for Supplied Item {0}.": "委外原材料 {0} 的预留仓库必须与委外仓不同。",
	"Selected {0} does not contain the Item Code {1}": "所选{0}中不包含物料号 {1}",
	"Purchase Receipt": "采购入库",
	"Purchase Invoice": "采购发票",
	"The field {0} is required for the reposting": "库存重算必须填写“{0}”",
	"Item Code": "物料号",
	"Warehouse": "仓库",
	"Posting Date": "记账日期",
	"Posting Time": "记账时间",
	"Statement PDF Password": "对账单 PDF 密码",
	"Create User Automatically": "自动创建用户",
	"Included fee is bigger than the withdrawal itself.": "已计入手续费不能大于支出金额。",
	"Matching Rules": "匹配规则",
	"No bank statements imported yet": "尚未导入银行对账单",
	"Record Payment": "记录收付款",
	"A new fiscal year has been automatically created.": "已自动创建新会计年度。",
	"No <strong>Account Data</strong> row found": "未找到<strong>科目数据</strong>行。",
	"Reverse {0} already available in draft status: {1}": "已有草稿状态的冲销{0}：{1}",
	"Appointment Booking Portal Settings": "预约门户设置",
	"Email Campaign Send Error": "邮件营销活动发送错误",
	"Verification Token": "验证令牌",
	"Invalid Discount Amount": "折扣金额无效",
	"Reserved Batch Conflict": "预留批次冲突",
	"Unit Price": "单价",
	"Stock Frozen": "库存已冻结",
	"Duplicate Serial Number Error": "序列号重复错误",
	"Reserved Inventory": "已预留库存",
	"Quality Inspection Not Configured": "质量检验单未配置",
	"Select Company Address": "选择公司地址",
	"Total Advance Paid": "预付款合计",
	"Invite Users": "邀请用户",
	"Use Posting Datetime for Naming Documents": "使用记账日期时间生成单据编号",
	"Creating demo data": "正在创建演示数据",
	"BOM Stock Analysis": "物料清单库存分析",
	"Subcontracting Setup": "委外设置",
	"Subcontracting Inward Order": "受托加工订单",
	"Subcontracting Delivery": "受托加工交付",
	"Subcontracted Purchase Order": "委外采购订单",
	"Subcontract BOM": "委外物料清单",
	"Stock Reservation Entries created": "已创建库存预留单",
	"Serial and Batch Bundle {0} should have voucher type as {1}": "序列号与批号组合 {0} 的单据类型必须为“{1}”",
	"Maintenance Schedule": "维护巡修计划",
	"The user cannot change the value of field {0} because stock transactions exist against dimension {1}.": "该库存辅助核算已有库存交易，不能修改字段 {0}（库存辅助核算：{1}）。",
	"Deleted custom fields related to dimension {0}": "已删除与库存辅助核算 {0} 相关的自定义字段",
	"Reference document {0} cannot be a child table.": "引用单据 {0} 不能是子表。",
	"Reference document {0} cannot be used as an Inventory Dimension.": "引用单据 {0} 不能用作库存辅助核算。",
	"Dimension Name": "辅助核算名称",
	"Sales Invoice Item": "销售发票明细",
	"Row #{0}: The Job Card Item reference is missing. Create the Stock Entry from the Job Card; rows added manually cannot be linked to a Job Card Item.": "第 {0} 行：缺少生产任务单明细引用。请从生产任务单创建物料移动；手工添加的明细无法关联生产任务单明细。",
	"The transaction type of Serial and Batch Bundle {0} is {1}, but based on Actual Qty {2} for Item {3} in {4} {5}, it should be {6}.": "序列号与批号组合 {0} 的交易类型为{1}，但根据单据 {4} {5} 中物料 {3} 的实际数量 {2}，交易类型应为{6}。",
	"Total Qty {0} of Serial and Batch Bundle {1} does not equal Actual Qty {2} in {3} {4}.": "序列号与批号组合 {1} 的总数量 {0} 与单据 {3} {4} 中的实际数量 {2} 不一致。",
	"Inward": "入库",
	"Outward": "出库",
	"Stock Entry": "物料移动",
	"Incorrect Type of Transaction": "交易类型错误",
	"Delivery Note": "销售出库",
	"Sales Invoice": "销售发票",
	"Set Serial No Series for Item {0}, or create the Serial and Batch Bundle manually.": "请为物料 {0} 设置序列号模板，或手工创建序列号与批号组合。",
	"Serial and Batch Bundle {0} does not match one or more of: Item {1}, Warehouse {2}, and {3} {4}.": "序列号与批号组合 {0} 与以下一项或多项不匹配：物料 {1}、仓库 {2}、单据 {3} {4}。",
	"This Item does not use batch or serial numbers.": "此物料未启用批号或序列号管理。",
	"To select serial numbers automatically, set Serial No Series for this Item.": "如需自动选择序列号，请为此物料设置序列号模板。",
	"To select batches automatically, set Batch Number Series for this Item.": "如需自动选择批号，请为此物料设置批号模板。",
	"To select serial numbers or batches automatically for outbound stock, enable {0} in {1}.": "如需在出库时自动选择序列号或批号，请在{1}中启用“{0}”。",
	"Auto create Serial and Batch Bundle for outward": "出库时自动创建序列号与批号",
	"Stock Settings": "库存设置",
	"Serial and Batch Bundle is not set for Item {0} in Warehouse {1}. {2}": "物料 {0} 在仓库 {1} 中未设置序列号与批号组合。{2}",
	"Price List {0} does not exist or is disabled.": "价格表 {0} 不存在或已停用。",
	"Item Price cannot be created for template Item {0}.": "不能为模板物料 {0} 创建物料价格。",
	"Row #{0}: Select a valid Quality Inspection with Reference Type {1} and Reference Name {2}.": "第 {0} 行：请选择关联类型为 {1}、源单据为 {2} 的有效质量检验单。",
	"Row #{0}: Select a valid Quality Inspection with Item Code {1}.": "第 {0} 行：请选择物料号为 {1} 的有效质量检验单。",
	"Due to period closing, item valuation cannot be reposted on or before {0}.": "会计期间已结账，不能对 {0} 或更早日期的物料成本价进行追溯调整。",
	"Due to Stock Closing Entry {0}, item valuation cannot be reposted on or before {1}.": "因存在库存结转分录 {0}，不能对 {1} 或更早日期的物料成本价进行追溯调整。",
	"Duplicate Stock Closing Entry": "重复的库存结转分录",
	"Generate Stock Closing Entry": "生成库存结转分录",
	"Field {0} is required.": "必须填写字段“{0}”。",
	"Customer": "客户",
	"Customer Group": "客户组",
	"Territory": "区域",
	"Sales Partner": "业务伙伴",
	"Campaign": "营销活动",
	"Supplier": "供应商",
	"Supplier Group": "供应商组",
	"Row {0} (Difference: {1})": "第 {0} 行（差额：{1}）",
	"Item Wise Tax Details do not match with Taxes and Charges at the following rows:": "以下行的物料税费明细与税费不一致：",
	"<p>The following {0} records do not belong to Company {1}:</p>": "<p>以下{0}记录不属于公司 {1}：</p>",
	"Statement Of Accounts for {{ customer.customer_name }}": "{{ customer.customer_name }} 往来对账单",
	"Hello {{ customer.customer_name }},<br>Please find attached your Statement Of Accounts from {{ doc.from_date }} to {{ doc.to_date }}.": "{{ customer.customer_name }}，您好：<br>附件为 {{ doc.from_date }} 至 {{ doc.to_date }} 的往来对账单，请查收。",
	"Hello {{ customer.customer_name }},<br>Please find attached your Statement Of Accounts until {{ doc.posting_date }}.": "{{ customer.customer_name }}，您好：<br>附件为截至 {{ doc.posting_date }} 的往来对账单，请查收。",
	"Exchange rate service call failed: {0}": "汇率服务调用失败：{0}",
	"Invalid result key. Response: {0}": "汇率服务返回结果中不存在配置的结果键。响应内容：{0}",
	"The exchange rate service did not return a numeric exchange rate.": "汇率服务未返回有效的数值汇率。",
	"Target Warehouse is set for some items but the customer is not an internal customer.": "部分物料设置了目标仓库，但客户不是内部客户。",
	"This {0} will be treated as a material transfer.": "此{0}将按物料调拨处理。",
	"Sales Order": "销售订单",
	"Repost Accounting Ledger": "会计凭证重新过账",
	"Repost Accounting Ledger Items": "会计凭证重新过账明细",
	"Repost Accounting Ledger Settings": "会计凭证重新过账设置",
	"Repost Allowed Types": "允许重新过账的单据类型",
	"Unable to Repost Accounting Ledger": "无法重新过账会计凭证",
	"Generating Preview": "正在生成预览…",
	"Accounting Ledger Repost Preview": "会计凭证重新过账预览",
	"Review the accounting entries before reposting.": "请在重新过账前核对会计凭证明细。",
	"The following document types cannot be reposted:<ul>{0}</ul>Add them to {1} in {2} to enable reposting.": "以下单据类型不能重新过账：<ul>{0}</ul>如需启用，请将这些单据类型添加到“{1}”表格（位于{2}）。",
	"The following documents have deferred revenue or expense enabled and cannot be reposted:<ul>{0}</ul>": "以下单据已启用递延收入或递延费用，不能重新过账：<ul>{0}</ul>",
	"Allowed DocTypes": "允许的单据类型",
	"Cost Center": "成本中心",
	"Project": "项目",
	"Customer Name": "客户名称",
	"Customer Type": "客户类型",
	"Supplier Name": "供应商名称",
	"Supplier Type": "供应商类型",
	"Party": "往来单位",
	"Party Name": "往来单位名称",
	"Party Type": "往来类型",
	"Invalid Accounts": "无效科目",
	"Stock Reposting Ongoing": "库存重新过账进行中",
	"Stock Closing Entry Failed": "库存结转分录处理失败",
	"Assigning Material Request {0} to Item {1} (row {2})": "正在将物料需求 {0} 分配给物料 {1}（第 {2} 行）",
	"Opening invoice creation failed": "开账发票创建失败",
	"Bank entry creation failed": "银行交易流水创建失败",
	"Subscription failed": "订阅处理失败",
	"Ledger merge failed": "科目合并失败",
	"Bank Statement Import failed": "银行对账单导入失败",
	"Unable to create material request": "无法创建物料需求",
	"Unable to repost item valuation": "无法执行物料成本价追溯调整",
	"Dimension Disabled": "辅助核算已禁用",
	"Dimension Enabled": "辅助核算已启用",
	"Creating reposting entries will change Stock In Hand and Stock Expenses in the Trial Balance, and the Balance Value in the Stock Balance report.": "创建重新过账记录将更改试算平衡表中的存货和存货费用，并同时更改库存余额报表中的余额。",
	"Are you sure you want to create the selected reposting entries?": "确定要创建所选的重新过账记录吗？",
	"Reason for hold: {0}": "暂停原因：{0}",
	"Row {0}: The field {1} is mandatory for internal transfer": "第 {0} 行：内部调拨必须填写字段 {1}",
	"You cannot change {0} because transactions exist against Promotional Scheme {1}. Disable this Promotional Scheme and create a new one for a different {0}.": "无法更改{0}，因为促销方案 {1} 已存在交易。请禁用此促销方案，并为其他{0}新建促销方案。",
	"Batch No {0} was not supplied against {1} {2}": "批号 {0} 未随 {1} {2} 提供",
	"Serial Nos {0} were not supplied against {1} {2}": "序列号 {0} 未随 {1} {2} 提供",
	"Item {0} is a template; please select one of its variants": "物料 {0} 是模板，请选择其具体规格物料",
	"Target {0}": "目标{0}",
	"Source {0}": "来源{0}",
	"Row {0}: {1} {2} must be submitted": "第 {0} 行：必须先提交{1} {2}",
	"Transaction not allowed against stopped Work Order {0}": "生产工单 {0} 已停止，不允许操作",
	"{0} {1} must be submitted": "{0} {1}必须提交",
	"Send Email": "发送邮件",
	"Company Logo": "公司标志",
	"Redeem Loyalty Points": "兑换积分",
	"Add Payment Method": "添加付款方式",
	"{0} percent off": "优惠 {0}%",
	"Search the docs (Press ? to focus)": "搜索文档（按 ? 键聚焦）",
	"Toggle navigation": "切换导航",
	"Quick Search": "快速搜索",
	"Clear Search": "清除搜索",
	"Search results for": "搜索结果",
	"Generic Empty State": "暂无内容",
	"Search {0}": "搜索{0}",
	"Email Campaign Failed.": "邮件营销活动发送失败。",
	"Failed to authenticate API key": "YouTube API 密钥认证失败",
	"Failed to authenticate the API key. Please check the error logs.": "API 密钥认证失败，请查看错误日志。",
	"Successful": "成功",
	"Partially successful": "部分成功",
	"Unable to update YouTube statistics": "无法更新 YouTube 统计数据",
	"All Accounts": "所有科目",
	"All Locations": "所有地点",
	"All Companies": "所有公司",
	"All Departments": "所有部门",
	"All Quality Procedures": "所有质量程序",
	"All Tasks": "所有任务",
	"BOM": "物料清单",
	"Cost Centers": "成本中心",
	"Warehouses": "仓库",
}
with (asset_root / "locale/zh/LC_MESSAGES/erpnext.mo").open("rb") as mo_file:
	translations = GNUTranslations(mo_file)
mismatches = {
	source: (translations.gettext(source), expected)
	for source, expected in expected_translations.items()
	if translations.gettext(source) != expected
}
if mismatches:
	raise SystemExit(f"Compiled ERPNext translations do not match: {mismatches}")
stock_transfer_title = translations.pgettext("Stock Transfer", "Internal Transfer")
if stock_transfer_title != "内部调拨":
	raise SystemExit(
		"Compiled ERPNext contextual translation does not match: "
		f"{stock_transfer_title!r} != '内部调拨'"
	)
print(f"Verified {len(expected_translations)} compiled ERPNext translations")

runtime_source_contracts = {
	"accounts/doctype/exchange_rate_revaluation/exchange_rate_revaluation.py": (
		"_(\"Zero Balance Journal: {0}\").format(",
		"_(\"Revaluation Journal: {0}\").format(",
	),
	"stock/doctype/pick_list/pick_list.py": (
		"_(\"Row #{0}: Item Code is Mandatory\").format(item.idx)",
	),
	"stock/doctype/stock_entry_type/stock_entry_type.py": (
		"_(\"Stock Entry Type {0} cannot be set as standard\").format(self.name)",
	),
	"public/js/bulk_transaction_processing.js": (
		"__(\"Starting a background job to create {0} {1}\", [",
	),
	"support/doctype/issue/issue.js": (
		"__(\"New issue created: {0}\", [",
		"frappe.utils.get_form_link(\"Issue\", r.message, true)",
	),
	"assets/doctype/asset/asset.js": ("primary_action_label: __(\"Submit\"),",),
	"maintenance/doctype/maintenance_schedule/maintenance_schedule.js": (
		"primary_action_label: __(\"Create Visit\"),",
	),
	"public/js/controllers/buying.js": (
		"__(\"Assigning Material Request {0} to Item {1} (row {2})\", [",
		"frappe.msgprint(__(\"Splitting {0} units of {1}\", [qty, d.item_code]));",
		"primary_action_label: __(\"Get Items\"),",
	),
	"public/js/sms_manager.js": ("title: __(\"Send SMS\"),",),
	"public/js/payment/payments.js": ("title: __(\"Payment\"),",),
	"stock/page/warehouse_capacity_summary/warehouse_capacity_summary.js": (
		"page.set_secondary_action(__(\"Refresh\"),",
	),
	"templates/pages/rfq.html": ("{{ _(\"View\") }}",),
	"templates/includes/transaction_row.html": ("{{ _(\"View\") }}",),
	"templates/includes/projects/project_timesheets.html": ("{{ _(\"View\") }}",),
	"templates/includes/projects/project_row.html": ("{{ _(\"View\") }}",),
	"www/payment_setup_certification.html": (
		"{{ _(\"ERPNext Certification\") }}",
		"{{ _(\"Continue\") }}",
		"{{ _(\"Certification History\") }}",
		"{{ _(\"Certification ID\") }}",
	),
	"templates/form_grid/item_grid.html": (
		"title = __(\"Warehouse\")",
		"var title = __(\"In Stock\")",
		"var title = __(\"Not In Stock\")",
	),
	"templates/includes/macros.html": (
		"{{ _(\"{0} star\").format(loop.index) }}",
		"{{ _(\"{0} percent of reviews have a {1}-star rating\").format(percent, loop.index) }}",
	),
	"templates/pages/projects.js": (
		"\"open:task\": __(\"No open tasks\")",
		"\"completed:task\": __(\"No completed tasks\")",
		"\"open:issue\": __(\"No open issues\")",
		"\"completed:issue\": __(\"No completed issues\")",
		"} else {",
	),
	"manufacturing/doctype/workstation/workstation.js": (
		"title: __(\"Raw Materials\"),",
	),
}
erpnext_root = Path("/home/frappe/frappe-bench/apps/erpnext/erpnext")
for relative_path, contracts in runtime_source_contracts.items():
	source = (erpnext_root / relative_path).read_text()
	missing = [contract for contract in contracts if contract not in source]
	if missing:
		raise SystemExit(f"Runtime translation source is stale in {relative_path}: {missing}")
print(f"Verified {len(runtime_source_contracts)} runtime translation source overlays")

repost_preview_source = Path(
	"/home/frappe/frappe-bench/apps/erpnext/erpnext/accounts/doctype/"
	"repost_accounting_ledger/repost_accounting_ledger.js"
).read_text()
for contract in (
	"title: __(\"Accounting Ledger Repost Preview\"),",
	"const preview_note = frappe.utils.escape_html(",
	"__(\"Review the accounting entries before reposting.\")",
	"let content = `<p class=\"text-muted\">${preview_note}</p>${r.message}`;",
):
	if contract not in repost_preview_source:
		raise SystemExit(f"Repost Accounting Ledger preview localization missing: {contract}")

stock_ledger_source = Path(
	"/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/stock_ledger_entry/stock_ledger_entry.py"
).read_text()
required_stock_templates = {
	"_(\"Item {0} not found\").format(self.item_code)",
	"_(\"Stock cannot exist for Item {0} since it has variants\").format(self.item_code)",
	"_(\"Serial No and Batch No are not allowed for Item {0}\").format(self.item_code)",
}
missing_stock_templates = {template for template in required_stock_templates if template not in stock_ledger_source}
if missing_stock_templates or "frappe.throw(_(message)" in stock_ledger_source:
	raise SystemExit(
		f"Stock Ledger Entry translation source is stale: missing={sorted(missing_stock_templates)}"
	)
print("Verified Stock Ledger Entry translation source")

stock_reposting_source = Path(
	"/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/stock_ledger.py"
).read_text()

stock_reposting_tree = ast.parse(stock_reposting_source)
validate_item_warehouse = next(
	node
	for node in ast.walk(stock_reposting_tree)
	if isinstance(node, ast.FunctionDef) and node.name == "validate_item_warehouse"
)
throw_calls = [
	node
	for node in ast.walk(validate_item_warehouse)
	if isinstance(node, ast.Call)
	and isinstance(node.func, ast.Attribute)
	and node.func.attr == "throw"
]
field_label_assignments = [
	node
	for node in ast.walk(validate_item_warehouse)
	if isinstance(node, ast.Assign)
	and any(isinstance(target, ast.Name) and target.id == "field_label" for target in node.targets)
]
if len(throw_calls) != 1 or len(field_label_assignments) != 1:
	raise SystemExit("Stock reposting translation source is stale")
throw_call = throw_calls[0]
formatted_message = throw_call.args[0]
field_label_value = field_label_assignments[0].value
valid_reposting_template = (
	isinstance(formatted_message, ast.Call)
	and isinstance(formatted_message.func, ast.Attribute)
	and formatted_message.func.attr == "format"
	and isinstance(formatted_message.func.value, ast.Call)
	and isinstance(formatted_message.func.value.func, ast.Name)
	and formatted_message.func.value.func.id == "_"
	and isinstance(formatted_message.func.value.args[0], ast.Constant)
	and formatted_message.func.value.args[0].value == "The field {0} is required for the reposting"
	and len(formatted_message.args) == 1
	and isinstance(formatted_message.args[0], ast.Name)
	and formatted_message.args[0].id == "field_label"
	and isinstance(field_label_value, ast.Call)
	and isinstance(field_label_value.func, ast.Name)
	and field_label_value.func.id == "_"
	and len(field_label_value.args) == 1
	and isinstance(field_label_value.args[0], ast.Call)
	and isinstance(field_label_value.args[0].func, ast.Attribute)
	and isinstance(field_label_value.args[0].func.value, ast.Name)
	and field_label_value.args[0].func.value.id == "frappe"
	and field_label_value.args[0].func.attr == "unscrub"
	and len(field_label_value.args[0].args) == 1
	and isinstance(field_label_value.args[0].args[0], ast.Name)
	and field_label_value.args[0].args[0].id == "field"
)
if not valid_reposting_template:
	raise SystemExit("Stock reposting translation source is stale")
print("Verified stock reposting translation source")

asset_source = Path(
	"/home/frappe/frappe-bench/apps/erpnext/erpnext/assets/doctype/asset/asset.py"
).read_text()
asset_tree = ast.parse(asset_source)
purchase_doc_function = next(
	node
	for node in asset_tree.body
	if isinstance(node, ast.FunctionDef) and node.name == "get_values_from_purchase_doc"
)
asset_throw_calls = [
	node
	for node in ast.walk(purchase_doc_function)
	if isinstance(node, ast.Call)
	and isinstance(node.func, ast.Attribute)
	and node.func.attr == "throw"
]
if len(asset_throw_calls) != 1:
	raise SystemExit("Asset purchase document translation source is stale")
asset_message = asset_throw_calls[0].args[0]
valid_asset_template = (
	isinstance(asset_message, ast.Call)
	and isinstance(asset_message.func, ast.Attribute)
	and asset_message.func.attr == "format"
	and isinstance(asset_message.func.value, ast.Call)
	and isinstance(asset_message.func.value.func, ast.Name)
	and asset_message.func.value.func.id == "_"
	and isinstance(asset_message.func.value.args[0], ast.Constant)
	and asset_message.func.value.args[0].value == "Selected {0} does not contain the Item Code {1}"
	and len(asset_message.args) == 2
	and isinstance(asset_message.args[0], ast.Call)
	and isinstance(asset_message.args[0].func, ast.Name)
	and asset_message.args[0].func.id == "_"
	and isinstance(asset_message.args[0].args[0], ast.Name)
	and asset_message.args[0].args[0].id == "doctype"
	and isinstance(asset_message.args[1], ast.Name)
	and asset_message.args[1].id == "item_code"
)
if not valid_asset_template:
	raise SystemExit("Asset purchase document translation source is stale")
print("Verified asset purchase document translation source")

expected_frappe_translations = {
	"Login": "登录",
	"Refresh": "刷新",
	"View": "查看",
	"Continue": "继续",
	"Error": "错误",
	"Failed": "失败",
	"Current Series": "当前编号",
	"Create Saved Filter": "创建已保存筛选",
	"No rows selected": "未选择任何行",
	"Sign In": "登录",
	"Welcome! Please sign in to continue.": "欢迎！请登录后继续。",
	"Forgot password?": "忘记密码？",
}
login_source = Path("/home/frappe/frappe-bench/apps/frappe/frappe/www/login.py").read_text()
if login_source.count('context["title"] = _("Login")') != 1:
	raise SystemExit("Frappe login page title translation source is stale")
if 'context["title"] = "Login"' in login_source:
	raise SystemExit("Frappe login page still contains the raw English title")
print("Verified Frappe login page title translation source")
setup_wizard_source = Path(
	"/home/frappe/frappe-bench/apps/frappe/frappe/desk/page/setup_wizard/setup_wizard.js"
).read_text()
if setup_wizard_source.count('default: "中文",') != 1:
	raise SystemExit("Frappe setup wizard Chinese language default is stale")
if 'default: "English",' in setup_wizard_source:
	raise SystemExit("Frappe setup wizard still defaults to English")
date_control_source = Path(
	"/home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/form/controls/date.js"
).read_text()
expected_date_language = (
	'let lang = document.documentElement.lang || frappe.boot.user?.language || "en";'
)
if date_control_source.count(expected_date_language) != 1:
	raise SystemExit("Frappe date picker does not fall back to the Chinese system language")
if 'let lang = "en";\n\t\tfrappe.boot.user && (lang = frappe.boot.user.language);' in date_control_source:
	raise SystemExit("Frappe date picker still defaults setup sessions to English")
print("Verified Frappe setup wizard Chinese language default")
with (asset_root / "locale/zh/LC_MESSAGES/frappe.mo").open("rb") as mo_file:
	frappe_translations = GNUTranslations(mo_file)
frappe_mismatches = {
	source: (frappe_translations.gettext(source), expected)
	for source, expected in expected_frappe_translations.items()
	if frappe_translations.gettext(source) != expected
}
if frappe_mismatches:
	raise SystemExit(f"Compiled Frappe translations do not match: {frappe_mismatches}")
print(f"Verified {len(expected_frappe_translations)} compiled Frappe translations")

banking_html = Path("/home/frappe/frappe-bench/apps/erpnext/erpnext/www/banking.html").read_text()
asset_paths = re.findall(r"(?:src|href)=\"(/assets/erpnext/banking/[^\"]+)\"", banking_html)
if not asset_paths:
	raise SystemExit("Banking HTML has no built asset references")
missing_banking_assets = [path for path in asset_paths if not (Path("/home/frappe/frappe-bench") / path.removeprefix("/")).is_file()]
if missing_banking_assets:
	raise SystemExit("Banking HTML references missing assets: " + ", ".join(missing_banking_assets))
entry_paths = [path for path in asset_paths if re.search(r"/index-[^/]+\.js$", path)]
if len(entry_paths) != 1:
	raise SystemExit(f"Expected one Banking entry bundle, found: {entry_paths}")
entry_file = Path("/home/frappe/frappe-bench/assets") / entry_paths[0].removeprefix("/assets/")
if "_translations_loaded" not in entry_file.read_text():
	raise SystemExit(f"Banking entry bundle lacks translation readiness contract: {entry_paths[0]}")
print(f"Verified {len(asset_paths)} Banking HTML asset references")
PY
	cd /home/frappe/frappe-bench
	PYTHONPATH=apps/erpnext:apps/frappe env/bin/python -m unittest discover -s /tmp -p "test_subcontracting_order_i18n.py"
	printf "%s\n" "Verified subcontracting order translation behavior"
	PYTHONPATH=apps/erpnext:apps/frappe env/bin/python -m unittest discover -s /tmp -p "test_maintenance_schedule_i18n.py"
	printf "%s\n" "Verified maintenance schedule translation behavior"
	PYTHONPATH=apps/erpnext:apps/frappe env/bin/python -m unittest discover -s /tmp -p "test_inventory_dimension_i18n.py"
	printf "%s\n" "Verified inventory dimension translation behavior"
	PYTHONPATH=apps/erpnext:apps/frappe env/bin/python -m unittest discover -s /tmp -p "test_stock_entry_i18n.py"
	printf "%s\n" "Verified stock entry translation behavior"
	PYTHONPATH=apps/erpnext:apps/frappe env/bin/python -m unittest discover -s /tmp -p "test_serial_batch_bundle_i18n.py"
	printf "%s\n" "Verified serial and batch bundle translation behavior"
	PYTHONPATH=apps/erpnext:apps/frappe env/bin/python -m unittest discover -s /tmp -p "test_item_price_i18n.py"
	printf "%s\n" "Verified item price translation behavior"
	PYTHONPATH=apps/erpnext:apps/frappe env/bin/python -m unittest discover -s /tmp -p "test_purchase_receipt_i18n.py"
	printf "%s\n" "Verified purchase receipt translation behavior"
	PYTHONPATH=apps/erpnext:apps/frappe env/bin/python -m unittest discover -s /tmp -p "test_repost_item_valuation_i18n.py"
	printf "%s\n" "Verified repost item valuation translation behavior"
	PYTHONPATH=apps/erpnext:apps/frappe env/bin/python -m unittest discover -s /tmp -p "test_promotional_scheme_i18n.py"
	printf "%s\n" "Verified promotional scheme translation behavior"
	PYTHONPATH=apps/erpnext:apps/frappe env/bin/python -m unittest discover -s /tmp -p "test_taxes_and_totals_i18n.py"
	printf "%s\n" "Verified taxes and totals translation behavior"
	PYTHONPATH=apps/erpnext:apps/frappe env/bin/python -m unittest discover -s /tmp -p "test_process_statement_i18n.py"
	printf "%s\n" "Verified process statement translation behavior"
	PYTHONPATH=apps/erpnext:apps/frappe env/bin/python -m unittest discover -s /tmp -p "test_currency_exchange_settings_i18n.py"
	printf "%s\n" "Verified currency exchange settings translation behavior"
	PYTHONPATH=apps/erpnext:apps/frappe env/bin/python -m unittest discover -s /tmp -p "test_selling_controller_i18n.py"
	printf "%s\n" "Verified selling controller translation behavior"
	PYTHONPATH=apps/erpnext:apps/frappe env/bin/python -m unittest discover -s /tmp -p "test_buying_controller_i18n.py"
	printf "%s\n" "Verified buying controller translation behavior"
	PYTHONPATH=apps/erpnext:apps/frappe env/bin/python -m unittest discover -s /tmp -p "test_repost_accounting_ledger_i18n.py"
	printf "%s\n" "Verified accounting ledger repost translation behavior"
	PYTHONPATH=apps/erpnext:apps/frappe env/bin/python -m unittest discover -s /tmp -p "test_tax_report_labels_i18n.py"
	printf "%s\n" "Verified tax report label translation behavior"
	/home/frappe/frappe-bench/env/bin/python /tmp/validate_frappe_runtime_i18n.py \
		--frappe-app /home/frappe/frappe-bench/apps/frappe \
		--catalog /home/frappe/frappe-bench/apps/frappe/frappe/locale/zh.po
	grep -F "this.print_format_control.get_value()" /home/frappe/frappe-bench/apps/frappe/frappe/printing/page/print/print.js >/dev/null
	test -s /home/frappe/frappe-bench/assets/locale/zh/LC_MESSAGES/erpnext.mo
	grep -F "{{ _(\"Banking\") }}" /home/frappe/frappe-bench/apps/erpnext/erpnext/www/banking.html >/dev/null
VERIFY_SCRIPT

printf '%s\n' "Built $image from $source_commit"
