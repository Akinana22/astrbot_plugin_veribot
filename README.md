# VeriBot

> [English Documentation](https://github.com/Akinana22/astrbot_plugin_veribot/blob/main/README.en.md)

跨平台注册邀请码分发 bot，支持 Discord 和 QQ。

## 配置

在 AstrBot WebUI 插件管理页面配置。

### 数据库配置

支持四种数据库类型，选择 `db_type` 后填写对应连接信息即可：

| `db_type` | 对应数据库 | 默认端口 | `db_name` 说明 |
|-----------|-----------|----------|---------------|
| `postgresql` | PostgreSQL | 5432 | 数据库名 |
| `mysql` | MySQL | 3306 | 数据库名 |
| `mariadb` | MariaDB | 3306 | 数据库名 |
| `sqlite` | SQLite | — | 文件路径，如 `data/veribot.db` |

#### 连接配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `db_type` | 数据库类型 | `postgresql` |
| `db_host` | 主机地址（SQLite 可忽略） | `localhost` |
| `db_port` | 端口（`0` = 使用驱动默认端口） | `0` |
| `db_name` | 数据库名称 / SQLite 文件路径 | (空) |
| `db_user` | 用户名（SQLite 可忽略） | (空) |
| `db_password` | 密码（SQLite 可忽略） | (空) |

#### 表名 / 列名（高级）

以下字段允许自定义数据存储位置。默认全部指向同一张表 `platform_bindings`，无需修改即可使用。

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `platform_table` | 平台字段所在表 | `platform_bindings` |
| `platform_column` | 平台字段列名 | `platform` |
| `qq_uid_table` | QQ UID 所在表 | `platform_bindings` |
| `qq_uid_column` | QQ UID 列名 | `platform_user_id` |
| `qq_code_table` | QQ 邀请码所在表 | `platform_bindings` |
| `qq_code_column` | QQ 邀请码列名 | `register_code_hash` |
| `discord_uid_table` | Discord UID 所在表 | `platform_bindings` |
| `discord_uid_column` | Discord UID 列名 | `platform_user_id` |
| `discord_code_table` | Discord 邀请码所在表 | `platform_bindings` |
| `discord_code_column` | Discord 邀请码列名 | `register_code_hash` |
| `is_used_table` | 状态字段所在表 | `platform_bindings` |
| `is_used_column` | 状态字段列名（`false`=未使用 / `true`=已使用） | `is_used` |

#### 功能配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `auxiliary_password` | 手动模式辅助密码，每行一个 | (空) |
| `auto_refresh` | 启用自动刷新密码 | `false` |
| `refresh_interval` | 刷新间隔（分钟，5-30） | `5` |
| `password_count` | 每轮密码数量（1-10） | `6` |

### 推荐（最简）配置

对于大多数用户，只需设置：

1. `db_type` — 选择数据库类型
2. `db_host` / `db_port` / `db_name` / `db_user` / `db_password` — 填写连接信息（SQLite 只需 `db_name` 填文件路径）
3. `auxiliary_password` — 至少填写一行辅助密码

其余保持默认值即可。

## 使用方式

### Discord

> **注意**：由于 Discord 斜杠指令需通过插件在平台适配器启动后动态注册，请按以下顺序操作。
>
> 1. 先安装配置好插件，**再**启动 Discord 平台适配器
> 2. 启动后等待 AstrBot 日志中出现 `[VeriBot] sign-in 追加完成`（完成后可能会有几秒延迟），稍等片刻即可投入生产
> 3. 如需重启插件，请**先关闭** Discord 平台适配器，重启插件后再重新启动适配器

在服务器中使用斜杠指令 `/sign-in`，bot 计算 SHA256 注册邀请码并通过临时消息（ephemeral，仅用户自己可见）回复。

**工作流：**

1. 用户在 Discord 服务器中使用 `/sign-in` 指令
2. Bot 获取 Discord 用户 UID
3. 查询数据库确认是否初次 sign-in
4. 初次 sign-in：计算 `SHA256(uid + 辅助密码)` 生成邀请码，写入数据库（`platform=discord, is_used=false`），ephemeral 回复邀请码
5. 非初次且 `is_used=false`：ephemeral 回复已有邀请码
6. 非初次且 `is_used=true`：不回复（已注册完成）

### QQ

> **注意：** QQ bot 需要设置为群管理员，否则群临时会话可能发送失败。

在群聊中发送 `/注册`，bot 随机选取一个辅助密码，计算注册邀请码并通过群临时会话私聊发送。

**工作流：**

1. 用户在 QQ 群聊中发送 `/注册` 指令
2. Bot 获取 QQ 用户 ID
3. 查询数据库确认是否初次注册
4. 初次注册：计算 `SHA256(uid + 辅助密码)` 生成邀请码，写入数据库（`platform=qq, is_used=false`），群临时会话发送邀请码
5. 非初次且 `is_used=false`：重新发送已有邀请码
6. 非初次且 `is_used=true`：回复"已成功注册"

### 密码模式

- **手动模式**：关闭自动刷新，在配置中手动填写密码（每行一个，使用时随机选取）
- **自动模式**：开启后按间隔自动生成随机密码池，使用时随机选取

## 指令

| 指令 | 平台 | 说明 |
|------|------|------|
| `/sign-in` | Discord | 获取注册邀请码（ephemeral 临时消息） |
| `/注册` | QQ | 获取注册邀请码（群临时会话） |
| `/sqltest` | 通用 | 测试数据库连接 |
