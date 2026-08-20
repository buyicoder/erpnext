# ERPNext 中国化维护

## 本地部署前备份

`scripts/deploy_local_zh_finance.sh` 会在重建容器和执行 `migrate` 之前强制备份现有站点。备份包含数据库、公开文件、私有文件和站点配置，同时保留在 Docker `sites` 卷和本机目录：

```text
.backups/pre-deploy/<site>/<UTC timestamp>/
```

本机备份文件权限为 `600`。部署前会验证 SQL gzip、两个 tar 归档和 JSON 配置；任何文件缺失、为空或损坏都会中止部署。

只生成和验证备份，不重建容器、不迁移数据库：

```bash
BACKUP_ONLY=1 ./scripts/deploy_local_zh_finance.sh
```

恢复时，先将选定时间戳目录复制到 backend 容器的临时目录，再使用 Frappe 原生恢复命令：

```bash
docker cp .backups/pre-deploy/frontend/<timestamp>/. erpnext-cn-backend-1:/tmp/erpnext-restore/
docker exec -it erpnext-cn-backend-1 bash -lc \
  'database="$(find /tmp/erpnext-restore -name "*-database*.sql.gz" -print -quit)"; \
  public_files="$(find /tmp/erpnext-restore -name "*-files*.tgz" ! -name "*-private-files*.tgz" -print -quit)"; \
  private_files="$(find /tmp/erpnext-restore -name "*-private-files*.tgz" -print -quit)"; \
  cd /home/frappe/frappe-bench && bench --site frontend restore "$database" \
  --with-public-files "$public_files" --with-private-files "$private_files"'
```

恢复是高风险操作；执行前应停止该站点的写入，并核对时间戳和站点名称。不要把 `site_config_backup.json` 提交到 Git，其中可能包含数据库密码和加密密钥。

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
