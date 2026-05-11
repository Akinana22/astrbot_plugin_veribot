# qqAuthCode

群聊中发送 `/注册` 指令，bot 通过群临时会话返回 SHA256 注册验证码。

## 安装

1. 将插件目录放入 AstrBot 的 `data/plugins/` 下
2. 安装依赖：`pip install -r requirements.txt`
3. 重启 AstrBot 或在 WebUI 插件管理中重载插件

## 配置

在 AstrBot WebUI 插件管理页面配置：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `db_host` | PostgreSQL 主机地址 | localhost |
| `db_port` | PostgreSQL 端口 | 5432 |
| `db_name` | 数据库名称 | qqauthcode |
| `db_user` | 数据库用户名 | postgres |
| `db_password` | 数据库密码 | (空) |
| `auxiliary_password` | 手动模式辅助密码，每行一个 | (空) |
| `auto_refresh` | 启用自动刷新密码 | false |
| `refresh_interval` | 刷新间隔（分钟，5-30） | 5 |
| `password_count` | 每轮密码数量（1-10） | 6 |

## 使用方式

> QQ bot 需要设置为群管理员，否则群临时会话可能发送失败。

1. QQ 用户在群聊中发送 `/注册`
2. Bot 随机选取一个辅助密码，计算验证码
3. 通过群临时会话私聊发送给用户

### 密码模式

- **手动模式**：关闭自动刷新，在配置中手动填写密码（每行一个，注册时随机选取）
- **自动模式**：开启后按间隔自动生成随机密码池，注册时随机选取

## 指令

| 指令 | 说明 |
|------|------|
| `/注册` | 获取注册验证码 |
| `/sqltest` | 测试数据库连接 |
