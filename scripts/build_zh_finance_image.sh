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
	--file "$repo_root/docker/zh-finance/Containerfile" \
	--build-arg "SOURCE_COMMIT=$source_commit" \
	--tag "$image" \
	"$repo_root"

docker run --rm --entrypoint sh \
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
	"$image" -lc '
	set -eu
	FRAPPE_RUNTIME_VERSION="'"$FRAPPE_RUNTIME_VERSION"'" /home/frappe/frappe-bench/env/bin/python - <<"PY"
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
	"Error": "错误",
	"Current Series": "当前编号",
	"Create Saved Filter": "创建已保存筛选",
	"No rows selected": "未选择任何行",
}
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
'

printf '%s\n' "Built $image from $source_commit"
