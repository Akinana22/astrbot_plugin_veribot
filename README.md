# VeriBot

> [English Documentation](https://github.com/Akinana22/qqAuthCode/blob/main/README.en.md)

跨平台注册邀请码分发 bot，支持 Discord 和 QQ。

## 配置

在 AstrBot WebUI 插件管理页面配置：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `db_host` | 数据库主机地址 | localhost |
| `db_port` | 数据库端口 | 5432 |
| `db_name` | 数据库名称 | (空) |
| `db_user` | 数据库用户名 | (空) |
| `db_password` | 数据库密码 | (空) |
| `auxiliary_password` | 手动模式辅助密码，每行一个 | (空) |
| `auto_refresh` | 启用自动刷新密码 | false |
| `refresh_interval` | 刷新间隔（分钟，5-30） | 5 |
| `password_count` | 每轮密码数量（1-10） | 6 |

## 使用方式

### Discord

在服务器中使用斜杠指令 `/sign-in`，bot 计算 SHA256 注册邀请码并通过临时消息（ephemeral，仅用户自己可见）回复。

**工作流：**

1. 用户在 Discord 服务器中使用 `/sign-in` 指令
2. Bot 获取 Discord 用户 UID
3. 查询数据库 `platform_bindings` 确认是否初次 sign-in
4. 初次 sign-in：计算 `SHA256(uid + 辅助密码)` 生成邀请码，写入数据库（`platform=discord, is_used=0`），ephemeral 回复邀请码
5. 非初次且 `is_used=0`：ephemeral 回复已有邀请码
6. 非初次且 `is_used=1`：不回复（已注册完成）

### QQ

> QQ bot 需要设置为群管理员，否则群临时会话可能发送失败。

在群聊中发送 `/注册`，bot 随机选取一个辅助密码，计算注册邀请码并通过群临时会话私聊发送。

**工作流：**

1. 用户在 QQ 群聊中发送 `/注册` 指令
2. Bot 获取 QQ 用户 ID
3. 查询数据库 `platform_bindings` 确认是否初次注册
4. 初次注册：计算 `SHA256(uid + 辅助密码)` 生成邀请码，写入数据库（`platform=qq, is_used=0`），群临时会话发送邀请码
5. 非初次且 `is_used=0`：重新发送已有邀请码
6. 非初次且 `is_used=1`：回复"已成功注册"

### 密码模式

- **手动模式**：关闭自动刷新，在配置中手动填写密码（每行一个，使用时随机选取）
- **自动模式**：开启后按间隔自动生成随机密码池，使用时随机选取

## 指令

| 指令 | 平台 | 说明 |
|------|------|------|
| `/sign-in` | Discord | 获取注册邀请码（ephemeral 临时消息） |
| `/注册` | QQ | 获取注册邀请码（群临时会话） |
| `/sqltest` | 通用 | 测试数据库连接 |
