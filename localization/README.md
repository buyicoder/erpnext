# ERPNext 中国化维护

## 历史人民币大写金额

新建或重新保存的人民币单据会自动生成中文财务大写金额。历史单据可通过维护函数重新计算；它只更新派生的金额大写字段，不改交易金额、币种、状态或 `modified` 时间。

先在站点容器中执行默认的只读盘点：

```bash
bench --site frontend execute erpnext.setup.china_money.rebuild_cny_amount_in_words
```

可先限制扫描数量或单据类型核对结果：

```bash
bench --site frontend execute erpnext.setup.china_money.rebuild_cny_amount_in_words \
  --kwargs '{"doctypes":["Sales Invoice","Purchase Invoice","Payment Entry"],"limit":100}'
```

确认数据库备份和只读报告后，显式应用：

```bash
bench --site frontend execute erpnext.setup.china_money.rebuild_cny_amount_in_words \
  --kwargs '{"dry_run":False}'
```

结果包含扫描单据数、实际变化单据数、变化字段数、各单据类型统计和最多 100 条样本。重复执行是幂等的；第二次只读盘点应显示 `documents_changed: 0`。
