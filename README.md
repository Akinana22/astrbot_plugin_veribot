# VeriBot

[中文](#中文) | [English](#english)

---

## 中文

跨平台注册邀请码分发 bot，支持 Discord 和 QQ。

### 配置

在 AstrBot WebUI 插件管理页面配置。

#### 数据库配置

支持四种数据库类型，选择 `db_type` 后填写对应连接信息即可：

| `db_type` | 对应数据库 | 默认端口 | `db_name` 说明 |
|-----------|-----------|----------|---------------|
| `postgresql` | PostgreSQL | 5432 | 数据库名 |
| `mysql` | MySQL | 3306 | 数据库名 |
| `mariadb` | MariaDB | 3306 | 数据库名 |
| `sqlite` | SQLite | — | 文件路径，如 `data/veribot.db` |

##### 连接配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `db_type` | 数据库类型 | `postgresql` |
| `db_host` | 主机地址（SQLite 可忽略） | `localhost` |
| `db_port` | 端口（`0` = 使用驱动默认端口） | `0` |
| `db_name` | 数据库名称 / SQLite 文件路径 | (空) |
| `db_user` | 用户名（SQLite 可忽略） | (空) |
| `db_password` | 密码（SQLite 可忽略） | (空) |

##### 表名 / 列名（高级）

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

##### 功能配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `auxiliary_password` | 手动模式辅助密码，每行一个 | (空) |
| `auto_refresh` | 启用自动刷新密码 | `false` |
| `refresh_interval` | 刷新间隔（分钟，5-30） | `5` |
| `password_count` | 每轮密码数量（1-10） | `6` |

#### 推荐（最简）配置

对于大多数用户，只需设置：

1. `db_type` — 选择数据库类型
2. `db_host` / `db_port` / `db_name` / `db_user` / `db_password` — 填写连接信息（SQLite 只需 `db_name` 填文件路径）
3. `auxiliary_password` — 至少填写一行辅助密码

其余保持默认值即可。

### 使用方式

#### Discord

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

#### QQ

> **注意：** QQ bot 需要设置为群管理员，否则群临时会话可能发送失败。

在群聊中发送 `/注册`，bot 随机选取一个辅助密码，计算注册邀请码并通过群临时会话私聊发送。

**工作流：**

1. 用户在 QQ 群聊中发送 `/注册` 指令
2. Bot 获取 QQ 用户 ID
3. 查询数据库确认是否初次注册
4. 初次注册：计算 `SHA256(uid + 辅助密码)` 生成邀请码，写入数据库（`platform=qq, is_used=false`），群临时会话发送邀请码
5. 非初次且 `is_used=false`：重新发送已有邀请码
6. 非初次且 `is_used=true`：回复"已成功注册"

#### 密码模式

- **手动模式**：关闭自动刷新，在配置中手动填写密码（每行一个，使用时随机选取）
- **自动模式**：开启后按间隔自动生成随机密码池，使用时随机选取

### 指令

| 指令 | 平台 | 说明 |
|------|------|------|
| `/sign-in` | Discord | 获取注册邀请码（ephemeral 临时消息） |
| `/注册` | QQ | 获取注册邀请码（群临时会话） |
| `/sqltest` | 通用 | 测试数据库连接 |

---

## English

A cross-platform registration invite code bot for AstrBot, supporting Discord and QQ.

### Configuration

Configure via the AstrBot WebUI plugin management page.

#### Database Configuration

Four database types are supported. Select `db_type` and fill in the corresponding connection info:

| `db_type` | Database | Default Port | `db_name` Usage |
|-----------|----------|-------------|-----------------|
| `postgresql` | PostgreSQL | 5432 | Database name |
| `mysql` | MySQL | 3306 | Database name |
| `mariadb` | MariaDB | 3306 | Database name |
| `sqlite` | SQLite | — | File path, e.g. `data/veribot.db` |

##### Connection Settings

| Option | Description | Default |
|--------|-------------|---------|
| `db_type` | Database type | `postgresql` |
| `db_host` | Host address (ignored for SQLite) | `localhost` |
| `db_port` | Port (`0` = driver default) | `0` |
| `db_name` | Database name / SQLite file path | (empty) |
| `db_user` | Username (ignored for SQLite) | (empty) |
| `db_password` | Password (ignored for SQLite) | (empty) |

##### Table / Column Names (Advanced)

The following fields allow customizing where data is stored. All default to the single table `platform_bindings` — no changes needed for standard use.

| Option | Description | Default |
|--------|-------------|---------|
| `platform_table` | Platform field table | `platform_bindings` |
| `platform_column` | Platform field column | `platform` |
| `qq_uid_table` | QQ UID table | `platform_bindings` |
| `qq_uid_column` | QQ UID column | `platform_user_id` |
| `qq_code_table` | QQ invite code table | `platform_bindings` |
| `qq_code_column` | QQ invite code column | `register_code_hash` |
| `discord_uid_table` | Discord UID table | `platform_bindings` |
| `discord_uid_column` | Discord UID column | `platform_user_id` |
| `discord_code_table` | Discord invite code table | `platform_bindings` |
| `discord_code_column` | Discord invite code column | `register_code_hash` |
| `is_used_table` | Status field table | `platform_bindings` |
| `is_used_column` | Status field column (`false`=unused / `true`=used) | `is_used` |

##### Feature Settings

| Option | Description | Default |
|--------|-------------|---------|
| `auxiliary_password` | Manual mode passwords, one per line | (empty) |
| `auto_refresh` | Enable automatic password refresh | `false` |
| `refresh_interval` | Refresh interval (minutes, 5-30) | `5` |
| `password_count` | Passwords per refresh round (1-10) | `6` |

#### Quick-Start (Recommended)

For most users, only the following are needed:

1. `db_type` — select your database type
2. `db_host` / `db_port` / `db_name` / `db_user` / `db_password` — fill in connection info (for SQLite, only `db_name` as file path)
3. `auxiliary_password` — enter at least one password

Leave all other fields at their defaults.

### Usage

#### Discord

> **Note**: Due to how Discord slash commands are dynamically registered after the adapter starts, follow this order:
>
> 1. Install and configure the plugin **before** starting the Discord adapter
> 2. After starting, wait for the log `[VeriBot] sign-in 追加完成` (there may be a few seconds delay), then the command is ready
> 3. To restart the plugin: **stop** the Discord adapter first, restart the plugin, then restart the adapter

Use the slash command `/sign-in` in a server. The bot computes a SHA256 registration invite code and replies with an ephemeral message (visible only to the user).

**Workflow:**

1. User sends `/sign-in` in a Discord server
2. Bot retrieves the user's Discord UID
3. Queries the database to check if it is a first-time sign-in
4. First-time: computes `SHA256(uid + auxiliary password)`, writes to DB (`platform=discord, is_used=false`), replies with the invite code via ephemeral message
5. Existing with `is_used=false`: replies with the existing invite code via ephemeral message
6. Existing with `is_used=true`: no reply (registration already completed)

#### QQ

> **Note:** The QQ bot must be a group admin, otherwise group temp sessions may fail to send.

Send `/注册` in a group chat. The bot randomly picks an auxiliary password, computes the invite code, and sends it via a group temp session.

**Workflow:**

1. User sends `/注册` in a QQ group chat
2. Bot retrieves the user's QQ ID
3. Queries the database to check if it is a first-time registration
4. First-time: computes `SHA256(uid + auxiliary password)`, writes to DB (`platform=qq, is_used=false`), sends the invite code via group temp session
5. Existing with `is_used=false`: resends the existing invite code
6. Existing with `is_used=true`: replies "Already registered"

#### Password Modes

- **Manual**: Disable auto-refresh and enter passwords manually (one per line, randomly selected each time).
- **Auto**: Enable auto-refresh to periodically generate a random password pool, randomly selected each time.

### Commands

| Command | Platform | Description |
|---------|----------|-------------|
| `/sign-in` | Discord | Get registration invite code (ephemeral message) |
| `/注册` | QQ | Get registration invite code (group temp session) |
| `/sqltest` | All | Test database connection |
