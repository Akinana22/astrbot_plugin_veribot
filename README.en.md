# VeriBot

> [中文文档](https://github.com/Akinana22/astrbot_plugin_veribot/blob/main/README.md)

A cross-platform registration invite code bot for AstrBot, supporting Discord and QQ.

## Configuration

Configure via the AstrBot WebUI plugin management page.

### Database Configuration

Four database types are supported. Select `db_type` and fill in the corresponding connection info:

| `db_type` | Database | Default Port | `db_name` Usage |
|-----------|----------|-------------|-----------------|
| `postgresql` | PostgreSQL | 5432 | Database name |
| `mysql` | MySQL | 3306 | Database name |
| `mariadb` | MariaDB | 3306 | Database name |
| `sqlite` | SQLite | — | File path, e.g. `data/veribot.db` |

#### Connection Settings

| Option | Description | Default |
|--------|-------------|---------|
| `db_type` | Database type | `postgresql` |
| `db_host` | Host address (ignored for SQLite) | `localhost` |
| `db_port` | Port (`0` = driver default) | `0` |
| `db_name` | Database name / SQLite file path | (empty) |
| `db_user` | Username (ignored for SQLite) | (empty) |
| `db_password` | Password (ignored for SQLite) | (empty) |

#### Table / Column Names (Advanced)

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

#### Feature Settings

| Option | Description | Default |
|--------|-------------|---------|
| `auxiliary_password` | Manual mode passwords, one per line | (empty) |
| `auto_refresh` | Enable automatic password refresh | `false` |
| `refresh_interval` | Refresh interval (minutes, 5-30) | `5` |
| `password_count` | Passwords per refresh round (1-10) | `6` |

### Quick-Start (Recommended)

For most users, only the following are needed:

1. `db_type` — select your database type
2. `db_host` / `db_port` / `db_name` / `db_user` / `db_password` — fill in connection info (for SQLite, only `db_name` as file path)
3. `auxiliary_password` — enter at least one password

Leave all other fields at their defaults.

## Usage

### Discord

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

### QQ

> **Note:** The QQ bot must be a group admin, otherwise group temp sessions may fail to send.

Send `/注册` in a group chat. The bot randomly picks an auxiliary password, computes the invite code, and sends it via a group temp session.

**Workflow:**

1. User sends `/注册` in a QQ group chat
2. Bot retrieves the user's QQ ID
3. Queries the database to check if it is a first-time registration
4. First-time: computes `SHA256(uid + auxiliary password)`, writes to DB (`platform=qq, is_used=false`), sends the invite code via group temp session
5. Existing with `is_used=false`: resends the existing invite code
6. Existing with `is_used=true`: replies "Already registered"

### Password Modes

- **Manual**: Disable auto-refresh and enter passwords manually (one per line, randomly selected each time).
- **Auto**: Enable auto-refresh to periodically generate a random password pool, randomly selected each time.

## Commands

| Command | Platform | Description |
|---------|----------|-------------|
| `/sign-in` | Discord | Get registration invite code (ephemeral message) |
| `/注册` | QQ | Get registration invite code (group temp session) |
| `/sqltest` | All | Test database connection |
