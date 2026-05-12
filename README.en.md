# VeriBot

> [中文文档](https://github.com/Akinana22/qqAuthCode/blob/main/README.md)

A cross-platform registration invite code bot for AstrBot, supporting Discord and QQ.

## Configuration

Configure via the AstrBot WebUI plugin management page:

| Option | Description | Default |
|--------|-------------|---------|
| `db_host` | Database host | localhost |
| `db_port` | Database port | 5432 |
| `db_name` | Database name | (empty) |
| `db_user` | Database user | (empty) |
| `db_password` | Database password | (empty) |
| `auxiliary_password` | Manual mode passwords, one per line | (empty) |
| `auto_refresh` | Enable automatic password refresh | false |
| `refresh_interval` | Refresh interval (minutes, 5-30) | 5 |
| `password_count` | Passwords per refresh round (1-10) | 6 |

## Usage

### Discord

Use the slash command `/sign-in` in a server. The bot computes a SHA256 registration invite code and replies with an ephemeral message (visible only to the user).

**Workflow:**

1. User sends `/sign-in` in a Discord server
2. Bot retrieves the user's Discord UID
3. Queries the `platform_bindings` table to check if it is a first-time sign-in
4. First-time: computes `SHA256(uid + auxiliary password)`, writes to DB (`platform=discord, is_used=0`), replies with the invite code via ephemeral message
5. Existing with `is_used=0`: replies with the existing invite code via ephemeral message
6. Existing with `is_used=1`: no reply (registration already completed)

### QQ

> The QQ bot must be a group admin, otherwise group temp sessions may fail to send.

Send `/注册` in a group chat. The bot randomly picks an auxiliary password, computes the invite code, and sends it via a group temp session.

**Workflow:**

1. User sends `/注册` in a QQ group chat
2. Bot retrieves the user's QQ ID
3. Queries the `platform_bindings` table to check if it is a first-time registration
4. First-time: computes `SHA256(uid + auxiliary password)`, writes to DB (`platform=qq, is_used=0`), sends the invite code via group temp session
5. Existing with `is_used=0`: resends the existing invite code
6. Existing with `is_used=1`: replies "Already registered"

### Password Modes

- **Manual**: Disable auto-refresh and enter passwords manually (one per line, randomly selected each time).
- **Auto**: Enable auto-refresh to periodically generate a random password pool, randomly selected each time.

## Commands

| Command | Platform | Description |
|---------|----------|-------------|
| `/sign-in` | Discord | Get registration invite code (ephemeral message) |
| `/注册` | QQ | Get registration invite code (group temp session) |
| `/sqltest` | All | Test database connection |
