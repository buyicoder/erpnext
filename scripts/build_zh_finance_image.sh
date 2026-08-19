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

docker run --rm --entrypoint sh "$image" -lc '
	set -eu
	FRAPPE_RUNTIME_VERSION="'"$FRAPPE_RUNTIME_VERSION"'" /home/frappe/frappe-bench/env/bin/python - <<"PY"
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

expected_translations = {
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
	"Stock Reservation Entries created": "已创建库存预留单",
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
print(f"Verified {len(expected_translations)} compiled ERPNext translations")

expected_frappe_translations = {
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
	/home/frappe/frappe-bench/env/bin/python /tmp/validate_frappe_runtime_i18n.py \
		--frappe-app /home/frappe/frappe-bench/apps/frappe \
		--catalog /home/frappe/frappe-bench/apps/frappe/frappe/locale/zh.po
	grep -F "this.print_format_control.get_value()" /home/frappe/frappe-bench/apps/frappe/frappe/printing/page/print/print.js >/dev/null
	test -s /home/frappe/frappe-bench/assets/locale/zh/LC_MESSAGES/erpnext.mo
	grep -F "{{ _(\"Banking\") }}" /home/frappe/frappe-bench/apps/erpnext/erpnext/www/banking.html >/dev/null
'

printf '%s\n' "Built $image from $source_commit"
