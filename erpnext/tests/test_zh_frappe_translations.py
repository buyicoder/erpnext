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
			"Sign In": "登录",
			"Welcome! Please sign in to continue.": "欢迎！请登录后继续。",
			"Forgot password?": "忘记密码？",
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

	def test_account_access_journey_uses_reviewed_chinese(self):
		expected = {
			"A new account has been created for you at {0}.": "已在 {0} 为你创建新账户。",
			"Back to sign in": "返回登录",
			"Click below to accept your invitation and get started.": "点击下方按钮接受邀请并开始使用。",
			"Click the button below to complete your registration and set a new password.": "点击下方按钮完成注册并设置新密码。",
			"Click the button below to sign in to your account. This link will expire in {0} minutes.": "点击下方按钮登录账户。此链接将在 {0} 分钟后失效。",
			"Complete your registration": "完成注册",
			"Didn't receive the link?": "没有收到链接？",
			"Full name is required.": "必须填写姓名。",
			"Good": "较强",
			"Great!": "很强！",
			"If you didn't request this link, you can ignore this email. Someone may have entered your email address by mistake.": "如果你没有请求此链接，可以忽略这封邮件；可能有人误填了你的电子邮箱地址。",
			"Invalid Email.": "电子邮箱格式无效。",
			"Invalid credentials, try again.": "登录信息无效，请重试。",
			"Invitation cancelled": "邀请已取消",
			"Invitation expired": "邀请已过期",
			"Let's setup your account.": "开始设置你的账户。",
			"Log In to {0}": "登录 {0}",
			"Log in to {0}": "登录 {0}",
			"Or copy and paste this link:": "或复制并粘贴此链接：",
			"Please check your email.": "请查收电子邮件。",
			"Please enter a valid email.": "请输入有效的电子邮箱地址。",
			"Please enter your email, we'll send you password reset link": "请输入电子邮箱地址，我们将向你发送密码重置链接",
			"Poor!": "较弱！",
			"Resend": "重新发送",
			"Send Link": "发送链接",
			"Sign Up": "注册",
			"Too many requests. Please try again later.": "请求过于频繁，请稍后重试。",
			"Use minimum of 8 characters(case sensitive) with at least one number or special character.": "请至少使用 8 个区分大小写的字符，并包含至少一个数字或特殊字符。",
			"Use strong passwords.": "请使用高强度密码。",
			"You've been invited": "你收到了一份邀请",
			"Your login ID is:": "你的登录账号是：",
			"Your password has expired. Please set a new password.": "你的密码已过期，请设置新密码。",
		}
		for source, translation in expected.items():
			with self.subTest(source=source):
				message = self.catalog.get(source)
				self.assertIsNotNone(message)
				self.assertNotIn("fuzzy", message.flags)
				self.assertEqual(message.string, translation)

	def test_system_settings_use_reviewed_chinese(self):
		expected = {
			"0 - too guessable: risky password.\n<br>\n1 - very guessable: protection from throttled online attacks. \n<br>\n2 - somewhat guessable: protection from unthrottled online attacks.\n<br>\n3 - safely unguessable: moderate protection from offline slow-hash scenario.\n<br>\n4 - very unguessable: strong protection from offline slow-hash scenario.": "0 - 极易猜中：密码风险很高。\n<br>\n1 - 很容易猜中：只能抵御受限速的在线攻击。\n<br>\n2 - 较容易猜中：可以抵御未限速的在线攻击。\n<br>\n3 - 难以猜中：可以适度抵御离线慢速哈希破解。\n<br>\n4 - 极难猜中：可以有效抵御离线慢速哈希破解。",
			"Adds a clear (×) button to Link fields, allowing users to quickly remove the selected value.": "为链接字段添加清除（×）按钮，便于用户快速移除已选值。",
			"Allow Clearing Link Fields": "允许清除链接字段",
			"Allowed Doctypes for Guest Uploads": "访客可上传文件的单据类型",
			"Disable Product Suggestion": "禁用产品推荐",
			"If enabled, only System Managers can upload public files. Other users can't see the checkbox <i>Is Private</i> in the upload dialog.": "启用后，仅系统管理员可以上传公开文件；其他用户在上传对话框中看不到“<i>设为私有</i>”复选框。",
			"Max Zip Extract Size (MB)": "ZIP 最大解压大小（MB）",
			"Maximum total size a ZIP archive is allowed to expand to when extracted.": "ZIP 压缩包解压后允许达到的最大总大小。",
			"OTP SMS Template": "一次性验证码短信模板",
			"OTP SMS Template must contain <code>{0}</code> placeholder to insert the OTP.": "一次性验证码短信模板必须包含 <code>{0}</code> 占位符以插入验证码。",
			"OTP placeholder should be defined as <code>{{ otp }}</code> ": "一次性验证码占位符应定义为 <code>{{ otp }}</code>。",
			"Only allow System Managers to upload public files": "仅允许系统管理员上传公开文件",
			"Provide a list of allowed Doctypes for file uploads. Each line should contain one allowed Doctype. If unset, uploads to all doctypes are allowed. Example: <br>User<br>Item<br>Quotation": "请提供允许上传文件的单据类型列表，每行填写一个单据类型。留空时允许向所有单据类型上传。示例：<br>用户<br>物料<br>报价单",
			"Snapshot Reports": "快照报表",
			"Sync In Batches": "分批同步",
			"Sync Timeout (Seconds)": "同步超时时间（秒）",
		}
		for source, translation in expected.items():
			with self.subTest(source=source):
				message = self.catalog.get(source)
				self.assertIsNotNone(message)
				self.assertNotIn("fuzzy", message.flags)
				self.assertEqual(message.string, translation)
