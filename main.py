import hashlib
import asyncio
import secrets
import random

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger, AstrBotConfig

from . import db


class QQAuthCode(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.db_pool = None
        self._passwords = []
        asyncio.create_task(self._init_db())
        if config.get("auto_refresh", False):
            asyncio.create_task(self._password_refresher())

    async def _init_db(self):
        try:
            self.db_pool = await db.init_pool(
                host=self.config.get("db_host", "localhost"),
                port=self.config.get("db_port", 5432),
                database=self.config.get("db_name", "qqauthcode"),
                user=self.config.get("db_user", "postgres"),
                password=self.config.get("db_password", ""),
            )
            logger.info("QQAuthCode PostgreSQL 连接池初始化成功")
        except Exception as e:
            logger.error(f"QQAuthCode PostgreSQL 连接失败: {e}")

    async def _password_refresher(self):
        await self._refresh_passwords()
        while True:
            interval = max(5, min(30, self.config.get("refresh_interval", 5))) * 60
            await asyncio.sleep(interval)
            await self._refresh_passwords()

    async def _refresh_passwords(self):
        count = max(1, min(10, self.config.get("password_count", 6)))
        self._passwords = [secrets.token_hex(8) for _ in range(count)]
        logger.info(f"已刷新 {count} 个辅助密码")

    def _get_password(self):
        if self.config.get("auto_refresh", False):
            return random.choice(self._passwords)
        lines = [line.strip() for line in self.config.get("auxiliary_password", "").splitlines() if line.strip()]
        if not lines:
            return ""
        return random.choice(lines)

    @filter.command("注册")
    async def register(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        group_id = event.message_obj.group_id

        if not group_id:
            yield event.plain_result("请在群聊中使用此指令")
            return

        if self.db_pool is None:
            yield event.plain_result("数据库未连接，请联系管理员")
            return

        try:
            binding = await db.get_binding(self.db_pool, "qq", str(user_id))

            if binding is None:
                aux_pwd = self._get_password()
                if not aux_pwd:
                    logger.error("辅助密码未设置，无法生成验证码")
                    yield event.plain_result("辅助密码未设置，请联系管理员")
                    return

                raw_str = f"{user_id}{aux_pwd}"
                hash_code = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

                await db.save_auth_code(self.db_pool, "qq", str(user_id), hash_code)
                logger.info(f"验证码已生成并存储 QQ={user_id}")

                code = hash_code[:12]
                await self._send_group_temp_msg(event, user_id, group_id, f"您的注册验证码为：{code}")
                yield event.plain_result("验证码已私聊发送，请查收")

            elif not binding["is_used"]:
                code = binding["register_code_hash"][:12]
                await self._send_group_temp_msg(event, user_id, group_id, f"您的注册验证码为：{code}")
                yield event.plain_result("验证码已重新私聊发送，请查收")

            else:
                yield event.plain_result("该 QQ 号已成功注册")

        except Exception as e:
            logger.error(f"处理注册失败 QQ={user_id}: {e}")
            yield event.plain_result("处理失败，请稍后重试")

    async def _send_group_temp_msg(self, event: AstrMessageEvent, user_id: str, group_id: str, message: str):
        try:
            client = event.bot
            await client.api.call_action(
                "send_private_msg",
                user_id=user_id,
                group_id=group_id,
                message=message,
            )
            logger.info(f"已发送群临时会话 QQ={user_id}")
        except Exception as e:
            logger.error(f"发送群临时会话失败 QQ={user_id}: {e}")

    @filter.command("sqltest")
    async def sqltest(self, event: AstrMessageEvent):
        if self.db_pool is None:
            yield event.plain_result("数据库未连接")
            return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.fetchrow("SELECT 1")
                yield event.plain_result("数据库连接正常")
        except Exception as e:
            logger.error(f"数据库测试失败: {e}")
            yield event.plain_result(f"数据库连接失败: {e}")

    async def terminate(self):
        if self.db_pool:
            await self.db_pool.close()
            logger.info("QQAuthCode PostgreSQL 连接池已关闭")
