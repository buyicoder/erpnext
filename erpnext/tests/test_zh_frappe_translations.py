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

	def test_permission_manager_help_uses_reviewed_chinese(self):
		expected = {
			"Allows printing or PDF download of documents.": "允许打印单据或将单据下载为 PDF。",
			"Allows sharing document access with other users.": "允许与其他用户共享单据访问权限。",
			"Allows the user to access reports related to the document.": "允许用户访问与该单据相关的报表。",
			"Allows the user to create new documents.": "允许用户新建单据。",
			"Allows the user to delete documents.": "允许用户删除单据。",
			"Allows the user to edit existing records they have access to.": "允许用户编辑其有权访问的现有记录。",
			"Allows the user to email from the document.": "允许用户从单据发送电子邮件。",
			"Allows the user to export data from the Report view.": "允许用户从报表视图导出数据。",
			"Allows the user to search and see records.": "允许用户搜索并查看记录。",
			"Allows the user to use Data Import tool to create / update records.": "允许用户使用数据导入工具新建或更新记录。",
			"Allows the user to view the document.": "允许用户查看单据。",
			"Allows users to enable the mask property for any field of the respective doctype.": "允许用户为相应单据类型的任意字段启用掩码属性。",
			"If the user enables the mask property for the phone number field, the value will be displayed in a masked format (e.g., 811XXXXXXX).": "如果用户为电话号码字段启用掩码属性，该值将以脱敏格式显示（例如 811XXXXXXX）。",
			"If the user has access to Employee and Report is enabled, they can view Employee-based reports.": "如果用户有权访问员工且已启用报表权限，则可以查看基于员工的报表。",
			"Meaning of Different Permission Types": "不同权限类型的含义",
			"No user has the role <strong>{0}</strong>": "没有用户拥有角色 <strong>{0}</strong>",
			"The email button is enabled for the user in the document.": "用户可以使用单据中的电子邮件按钮。",
			"The print button is enabled for the user in the document.": "用户可以使用单据中的打印按钮。",
			"The user can create a new Item but cannot edit existing items.": "用户可以新建物料，但不能编辑现有物料。",
			"The user can delete Draft / Cancelled documents.": "用户可以删除草稿或已取消的单据。",
			"The user can export report data.": "用户可以导出报表数据。",
			"The user can import new records or update existing data for the document.": "用户可以为该单据类型导入新记录或更新现有数据。",
			"The user can select a Customer in Sales Order but cannot open the Customer master.": "用户可以在销售订单中选择客户，但不能打开客户主数据。",
			"The user can share document access with another user.": "用户可以与其他用户共享单据访问权限。",
			"The user can update a customer or any other fields in an existing Sales Order but cannot create a new Sales Order.": "用户可以更新现有销售订单中的客户或其他字段，但不能新建销售订单。",
			"The user can view Sales Invoices but cannot modify any field values in them.": "用户可以查看销售发票，但不能修改其中任何字段的值。",
			"View all {0} users": "查看全部 {0} 位用户",
			"{0} with the role <strong>{1}</strong>": "{0} 位用户拥有角色 <strong>{1}</strong>",
		}
		for source, translation in expected.items():
			with self.subTest(source=source):
				message = self.catalog.get(source)
				self.assertIsNotNone(message)
				self.assertNotIn("fuzzy", message.flags)
				self.assertEqual(message.string, translation)

	def test_email_account_and_queue_use_reviewed_chinese(self):
		expected = {
			"Add Reply-To header": "添加 Reply-To 邮件头",
			"Add X-Original-From header": "添加 X-Original-From 邮件头",
			"Addresses added here will be used as the Reply-To header for outgoing emails sent from this account.": "此处添加的地址将用作该账户外发邮件的 Reply-To 邮件头。",
			"Automatic sending of emails is disabled via site config.": "站点配置已禁用自动发送邮件。",
			"DELAY": "延迟",
			"Delivery Status Notification Type": "送达状态通知类型",
			"Email size {0:.2f} MB exceeds the maximum allowed size of {1:.2f} MB": "邮件大小 {0:.2f} MB 超过允许的最大值 {1:.2f} MB",
			"FAILURE": "失败",
			"Failed to retrieve the list of IMAP folders from the server. Please ensure the mailbox is accessible and the account has permission to list folders.": "无法从服务器获取 IMAP 文件夹列表。请确认邮箱可访问，且该账户有权列出文件夹。",
			"IMAP Folder Not Found": "未找到 IMAP 文件夹",
			"IMAP Folder Validation Failed": "IMAP 文件夹验证失败",
			"IMAP Folder name cannot be empty.": "IMAP 文件夹名称不能为空。",
			"NEVER": "从不",
			"No IMAP folders were found on the server. Please verify the email account settings and ensure the mailbox contains folders.": "服务器上未找到 IMAP 文件夹。请检查邮件账户设置，并确认邮箱中存在文件夹。",
			"Outgoing": "发件",
			"Raw HTML emails are rendered as complete Jinja templates. Otherwise, emails are wrapped in the standard.html email template, which inserts brand_logo, header and footer.": "原始 HTML 邮件将作为完整的 Jinja 模板渲染；否则邮件会套用 standard.html 模板，并插入 brand_logo、页眉和页脚。",
			"Redact Message After Send": "发送后清除邮件正文",
			"Replace the message body with a placeholder once the email has been sent, so that sensitive content like password reset links is not retained in the queue.": "邮件发送后用占位内容替换正文，避免密码重置链接等敏感内容保留在队列中。",
			"Reply To email is required": "必须填写回复地址电子邮箱",
			"Reply-To Addresses": "回复地址",
			"SUCCESS": "成功",
			"SUCCESS,FAILURE": "成功、失败",
			"SUCCESS,FAILURE,DELAY": "成功、失败、延迟",
			"Select which delivery events should trigger a delivery status notification (DSN) from the SMTP server.": "选择哪些送达事件应触发 SMTP 服务器的送达状态通知（DSN）。",
			"Send As Raw HTML": "以原始 HTML 发送",
			"The configured SMTP server does not support DSN (Delivery Status Notification).": "配置的 SMTP 服务器不支持 DSN（送达状态通知）。",
			"The following configured IMAP folder(s) were not found or are not accessible on the server:<br><ul>{0}</ul>Please verify the folder names exactly as they appear on the server and ensure the account has access to them.": "服务器上找不到或无法访问以下已配置的 IMAP 文件夹：<br><ul>{0}</ul>请核对文件夹名称与服务器上的显示完全一致，并确认该账户有权访问。",
		}
		for source, translation in expected.items():
			with self.subTest(source=source):
				message = self.catalog.get(source)
				self.assertIsNotNone(message)
				self.assertNotIn("fuzzy", message.flags)
				self.assertEqual(message.string, translation)

	def test_notification_configuration_uses_reviewed_chinese(self):
		expected = {
			'<p><strong>{{ __("Condition Examples") }}:</strong></p>\n<pre><code class="language-python">doc.status=="Open"<br>doc.due_date==nowdate()<br>doc.total &gt; 40000\n</code></pre>\n': '<p><strong>{{ __("Condition Examples") }}：</strong></p>\n<pre><code class="language-python">doc.status=="Open"<br>doc.due_date==nowdate()<br>doc.total &gt; 40000\n</code></pre>\n',
			'<p><strong>{{ __("Condition Examples") }}:</strong></p>\n<pre>doc.status=="Open"<br>doc.due_date==nowdate()<br>doc.total &gt; 40000\n</pre>': '<p><strong>{{ __("Condition Examples") }}：</strong></p>\n<pre>doc.status=="Open"<br>doc.due_date==nowdate()<br>doc.total &gt; 40000\n</pre>',
			"Category for the in-app notification. Used for filtering and per-user email preferences.": "应用内通知的分类，用于筛选和设置每位用户的邮件偏好。",
			"From Attach Field": "来自附件字段",
			"From Field": "来自字段",
			"Headline of the in-app notification. Falls back to Subject if left blank. Supports Jinja.": "应用内通知的标题；留空时使用主题。支持 Jinja。",
			"Notification Message": "通知内容",
			"Notification Title": "通知标题",
			"Notification Type": "通知类型",
			"Optional body of the in-app notification. Supports Jinja.": "应用内通知的可选正文。支持 Jinja。",
			"Please specify the field from which to attach files": "请指定用于获取附件的字段",
			"You are not allowed to delete a standard Notification. You can disable it instead.": "您无权删除标准通知，可以将其禁用。",
		}
		for source, translation in expected.items():
			with self.subTest(source=source):
				message = self.catalog.get(source)
				self.assertIsNotNone(message)
				self.assertNotIn("fuzzy", message.flags)
				self.assertEqual(message.string, translation)

	def test_form_timeline_uses_reviewed_chinese(self):
		expected = {
			"You created this document": "你创建了此单据",
			"added {0} row(s) to {1}": "在 {1} 中新增了 {0} 行",
			"cancelled this document": "取消了此单据",
			"changed {0}": "修改了 {0}",
			"cleared {0}": "清空了 {0}",
			"removed {0} row(s) from {1}": "从 {1} 中移除了 {0} 行",
			"set {0} to": "将 {0} 设置为",
			"set {0} to {1} in row #{2}": "将第 {2} 行的 {0} 设置为 {1}",
			"submitted this document": "提交了此单据",
			"updated {0}": "更新了 {0}",
			"{0} created this document": "{0} 创建了此单据",
			"{0} liked": "{0} 点赞了",
		}
		for source, translation in expected.items():
			with self.subTest(source=source):
				message = self.catalog.get(source)
				self.assertIsNotNone(message)
				self.assertNotIn("fuzzy", message.flags)
				self.assertEqual(message.string, translation)

	def test_security_txt_configuration_uses_reviewed_chinese(self):
		expected = {
			"Date after which this security.txt should be considered stale. Expires timestamp is converted to UTC.": "超过此日期后，security.txt 将视为失效。过期时间会转换为 UTC。",
			"Days Remaining": "剩余天数",
			"Defaults to `en`": "默认值为 `en`",
			"Expiration date must be in the future": "过期日期必须晚于当前时间",
			"Expires": "有效期至",
			"Guidelines and policies on vulnerability reporting. Defaults to `https://frappe.io/security`": "漏洞报告指南与安全策略。默认值为 `https://frappe.io/security`",
			"Please update your security settings from desk.": "请前往管理后台更新安全设置。",
			"Policy": "安全策略",
			"Preferred Language": "首选语言",
			"Public Policy URL must start with https://": "公开安全策略网址必须以 https:// 开头",
			"Security.txt": "Security.txt",
			"Security.txt will be served only under HTTPS.": "Security.txt 仅通过 HTTPS 提供。",
			"Security.txt will expire soon!": "Security.txt 即将过期！",
			"Site": "站点",
			"URL contact must start with https://": "联系网址必须以 https:// 开头",
			"Website, email or phone where vulnerabilities can be reported. Defaults to `https://security.frappe.io`": "用于报告漏洞的网站、电子邮箱或电话。默认值为 `https://security.frappe.io`",
		}
		for source, translation in expected.items():
			with self.subTest(source=source):
				message = self.catalog.get(source)
				self.assertIsNotNone(message)
				self.assertNotIn("fuzzy", message.flags)
				self.assertEqual(message.string, translation)

	def test_notification_type_preferences_use_reviewed_chinese(self):
		expected = {
			"Email everyone for <b>{0}</b> notifications? This adds it to every user's email preferences. Users can still opt out individually afterwards.": "是否为所有用户启用 <b>{0}</b> 通知邮件？此操作会将其添加到每位用户的邮件偏好中，用户之后仍可自行关闭。",
			"Enable Email Notifications for All Users": "为所有用户启用邮件通知",
			"Enable the notification type before emailing it to users.": "请先启用该通知类型，再为用户开启邮件通知。",
			"Enabling email for {0} across all users in the background.": "正在后台为所有用户启用 {0} 邮件通知。",
			"Type Name": "类型名称",
			"{0} does not exist": "{0} 不存在",
			"{0} is a built-in Notification Type and cannot be deleted. Disable it instead.": "{0} 是内置通知类型，无法删除；请将其禁用。",
			"{0} never sends email, so it cannot be enabled for users.": "{0} 从不发送邮件，因此无法为用户启用。",
		}
		for source, translation in expected.items():
			with self.subTest(source=source):
				message = self.catalog.get(source)
				self.assertIsNotNone(message)
				self.assertNotIn("fuzzy", message.flags)
				self.assertEqual(message.string, translation)

	def test_global_search_settings_use_reviewed_chinese(self):
		expected = {
			"Cannot configure Core DocTypes for Global Search.": "无法为全局搜索配置核心单据类型。",
			"Configure search fields": "配置搜索字段",
			"Document Name (ID)": "单据名称（ID）",
			"Document Type is required": "必须选择单据类型",
			"Please select Document Type first.": "请先选择单据类型。",
			"Search fields updated.": "搜索字段已更新。",
			"Updating search index": "正在更新搜索索引",
		}
		for source, translation in expected.items():
			with self.subTest(source=source):
				message = self.catalog.get(source)
				self.assertIsNotNone(message)
				self.assertNotIn("fuzzy", message.flags)
				self.assertEqual(message.string, translation)

	def test_communication_email_actions_use_reviewed_chinese(self):
		expected = {
			"Are you sure you want to relink this communication?": "确定要重新关联此沟通记录吗？",
			"Email undo window is over. Cannot undo email.": "邮件撤回时限已过，无法撤回。",
			"Failed to delete communication": "删除沟通记录失败",
			"Fw: {0}": "转发：{0}",
			"It is too late to undo this email. It is already being sent.": "现在撤回已太晚，邮件已经开始发送。",
			"Raw HTML can be used only with Email Templates having 'Use HTML' checked. Proceeding with plain text email.": "仅当邮件模板勾选“使用 HTML”时才能使用原始 HTML。将改用纯文本邮件。",
			"You are not authorized to undo this email": "您无权撤回此邮件",
		}
		for source, translation in expected.items():
			with self.subTest(source=source):
				message = self.catalog.get(source)
				self.assertIsNotNone(message)
				self.assertNotIn("fuzzy", message.flags)
				self.assertEqual(message.string, translation)
