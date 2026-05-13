import hashlib
import asyncio
import secrets
import random
import traceback
import aiohttp
from sqlalchemy import text

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger, AstrBotConfig

from . import db


class VeriBot(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.db_engine = None
        self._db_type = config.get("db_type", "postgresql")
        self._passwords = []
        self._discord_signin_setup = False
        asyncio.create_task(self._init_db())
        if config.get("auto_refresh", False):
            asyncio.create_task(self._password_refresher())

    async def _init_db(self):
        try:
            self.db_engine = await db.init_engine(
                self._db_type,
                self.config.get("db_host", "localhost"),
                self.config.get("db_port", 0),
                self.config.get("db_name", ""),
                self.config.get("db_user", ""),
                self.config.get("db_password", ""),
            )
            unique_tables = {
                self.config.get("platform_table", "platform_bindings"),
                self.config.get("qq_uid_table", "platform_bindings"),
                self.config.get("qq_code_table", "platform_bindings"),
                self.config.get("discord_uid_table", "platform_bindings"),
                self.config.get("discord_code_table", "platform_bindings"),
                self.config.get("is_used_table", "platform_bindings"),
            }
            plat_col = self.config.get("platform_column", "platform")
            uid_col = self.config.get("qq_uid_column", "platform_user_id")
            code_col = self.config.get("qq_code_column", "register_code_hash")
            used_col = self.config.get("is_used_column", "is_used")
            for table in unique_tables:
                await db.ensure_tables(self.db_engine, self._db_type, table, plat_col, uid_col, code_col, used_col)
            logger.info(f"VeriBot {self._db_type} 数据库初始化成功")
        except Exception as e:
            logger.error(f"VeriBot 数据库连接失败: {e}")

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
    @filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP)
    async def register(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        group_id = event.message_obj.group_id

        if not group_id:
            yield event.plain_result("请在群聊中使用此指令")
            return

        if self.db_engine is None:
            yield event.plain_result("数据库未连接，请联系管理员")
            return

        try:
            binding = await db.get_binding(
                self.db_engine, self._db_type,
                self.config.get("qq_uid_table", "platform_bindings"),
                self.config.get("qq_uid_column", "platform_user_id"),
                self.config.get("qq_code_column", "register_code_hash"),
                self.config.get("is_used_column", "is_used"),
                self.config.get("platform_column", "platform"),
                "qq", str(user_id),
            )

            if binding is None:
                aux_pwd = self._get_password()
                if not aux_pwd:
                    logger.error("辅助密码未设置，无法生成注册邀请码")
                    yield event.plain_result("辅助密码未设置，请联系管理员")
                    return

                raw_str = f"{user_id}{aux_pwd}"
                hash_code = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

                await db.save_auth_code(
                    self.db_engine, self._db_type,
                    self.config.get("qq_code_table", "platform_bindings"),
                    self.config.get("qq_uid_column", "platform_user_id"),
                    self.config.get("qq_code_column", "register_code_hash"),
                    self.config.get("is_used_column", "is_used"),
                    self.config.get("platform_column", "platform"),
                    "qq", str(user_id), hash_code,
                )
                logger.info(f"注册邀请码已生成并存储 QQ={user_id}")

                code = hash_code[:12]
                await self._send_group_temp_msg(event, user_id, group_id, f"您的注册邀请码为：{code}")
                yield event.plain_result("注册邀请码已私聊发送，请查收")

            elif not binding[self.config.get("is_used_column", "is_used")]:
                code = binding[self.config.get("qq_code_column", "register_code_hash")][:12]
                await self._send_group_temp_msg(event, user_id, group_id, f"您的注册邀请码为：{code}")
                yield event.plain_result("注册邀请码已重新私聊发送，请查收")

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
        logger.info(f"[VeriBot] sqltest 触发, platform={event.get_platform_name()}")
        if self.db_engine is None:
            logger.warning("[VeriBot] sqltest: db_engine is None, 尝试初始化...")
            try:
                await self._init_db()
                if self.db_engine is None:
                    yield event.plain_result("数据库未连接，请稍后重试")
                    return
            except Exception as e:
                logger.error(f"[VeriBot] sqltest: 初始化失败: {e}")
                yield event.plain_result("数据库未连接，请联系管理员")
                return
        try:
            async with self.db_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("[VeriBot] sqltest: SELECT 1 成功")
            yield event.plain_result("数据库连接正常")
            logger.info("[VeriBot] sqltest: 结果已 yield")
        except Exception as e:
            logger.error(f"[VeriBot] sqltest 失败: {e}\n{traceback.format_exc()}")
            yield event.plain_result(f"数据库连接失败: {e}")

    @filter.on_platform_loaded()
    async def _on_platform_ready(self):
        for plat in self.context.platform_manager.platform_insts:
            if plat.meta().name == "discord" and not self._discord_signin_setup:
                self._discord_signin_setup = True
                logger.info(f"[VeriBot] 检测到 Discord 平台, id={plat.meta().id}")
                asyncio.create_task(self._setup_discord_signin(plat))
            elif plat.meta().name == "discord" and self._discord_signin_setup:
                logger.info(f"[VeriBot] Discord 平台 {plat.meta().id} sign-in 已注册，跳过")

    async def _setup_discord_signin(self, platform):
        import discord as _discord

        logger.info("[VeriBot] 开始设置 Discord sign-in 指令")

        for i in range(60):
            if hasattr(platform, 'client') and platform.client is not None:
                logger.info("[VeriBot] Discord client 已出现，等待 on_ready 完成...")
                break
            if i == 0:
                logger.info("[VeriBot] 等待 Discord client 初始化...")
            await asyncio.sleep(1)
        else:
            logger.error("[VeriBot] Discord client 超时未就绪，放弃注册 sign-in 指令")
            return

        client = platform.client

        try:
            await client.wait_until_ready()
            logger.info("[VeriBot] wait_until_ready 完成，等待适配器 on_ready 回调执行...")
            await asyncio.sleep(5)
            logger.info("[VeriBot] 开始注册 sign-in 指令")
        except Exception as e:
            logger.error(f"[VeriBot] wait_until_ready 异常: {e}")
            return

        async def signin_callback(ctx: _discord.ApplicationContext):
            try:
                user_id = str(ctx.author.id)
                logger.info(f"[VeriBot] sign-in 触发, uid={user_id}, name={ctx.author.display_name}")

                await ctx.defer(ephemeral=True)

                if self.db_engine is None:
                    logger.error("[VeriBot] DB 未连接，sign-in 失败")
                    await ctx.followup.send("Database not connected. Please contact the administrator.", ephemeral=True)
                    return

                binding = await db.get_binding(
                    self.db_engine, self._db_type,
                    self.config.get("discord_uid_table", "platform_bindings"),
                    self.config.get("discord_uid_column", "platform_user_id"),
                    self.config.get("discord_code_column", "register_code_hash"),
                    self.config.get("is_used_column", "is_used"),
                    self.config.get("platform_column", "platform"),
                    "discord", user_id,
                )

                if binding is None:
                    aux_pwd = self._get_password()
                    if not aux_pwd:
                        logger.error("[VeriBot] 辅助密码未设置，sign-in 失败")
                        await ctx.followup.send("Auxiliary password not configured. Please contact the administrator.", ephemeral=True)
                        return

                    raw_str = f"{user_id}{aux_pwd}"
                    hash_code = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

                    await db.save_auth_code(
                        self.db_engine, self._db_type,
                        self.config.get("discord_code_table", "platform_bindings"),
                        self.config.get("discord_uid_column", "platform_user_id"),
                        self.config.get("discord_code_column", "register_code_hash"),
                        self.config.get("is_used_column", "is_used"),
                        self.config.get("platform_column", "platform"),
                        "discord", user_id, hash_code,
                    )
                    code = hash_code[:12]
                    logger.info(f"[VeriBot] 初次 sign-in, uid={user_id}, code={code}")

                    await ctx.followup.send(f"Your registration invite code: {code}", ephemeral=True)

                elif not binding[self.config.get("is_used_column", "is_used")]:
                    code = binding[self.config.get("discord_code_column", "register_code_hash")][:12]
                    logger.info(f"[VeriBot] 非初次 sign-in(未注册), uid={user_id}, code={code}")
                    await ctx.followup.send(f"Your registration invite code: {code}", ephemeral=True)

                else:
                    logger.info(f"[VeriBot] 非初次 sign-in(已注册), uid={user_id}, 忽略")

            except Exception as e:
                logger.error(f"[VeriBot] sign-in callback 异常: {e}\n{traceback.format_exc()}")
                try:
                    await ctx.followup.send("An error occurred. Please try again later.", ephemeral=True)
                except Exception:
                    pass

        try:
            guild_id = getattr(platform, 'guild_id', None)
            cmd = _discord.SlashCommand(
                name="sign-in",
                description="Get registration invite code",
                func=signin_callback,
                guild_ids=[guild_id] if guild_id else None,
            )
            client.add_application_command(cmd)
            logger.info(f"[VeriBot] 适配器已就绪(guild_id={guild_id}), 追加 sign-in 指令...")

            await self._register_cmd_safe(client, "sign-in", "Get registration invite code",
                                           guild_id)
            logger.info("[VeriBot] sign-in 追加完成")
            self._discord_signin_setup = True
        except Exception as e:
            logger.error(f"[VeriBot] 注册 sign-in 指令失败: {e}\n{traceback.format_exc()}")

    async def _register_cmd_safe(self, client, name, description, guild_id):
        token = client.http.token
        app_id = client.application_id
        headers = {"Authorization": f"Bot {token}"}
        body = {"name": name, "type": 1, "description": description}
        if guild_id:
            url = f"https://discord.com/api/v10/applications/{app_id}/guilds/{guild_id}/commands"
        else:
            url = f"https://discord.com/api/v10/applications/{app_id}/commands"

        for attempt in range(4):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=body, headers=headers) as resp:
                        if resp.status in (200, 201):
                            logger.info(f"[VeriBot] {name} 指令 POST 成功 (status={resp.status})")
                            return
                        text = await resp.text()
                        logger.warning(f"[VeriBot] {name} POST 返回 {resp.status}: {text[:200]}")
                if attempt < 3:
                    wait = (attempt + 1) * 3
                    logger.info(f"[VeriBot] {name} 第{attempt + 1}次重试, {wait}s 后...")
                    await asyncio.sleep(wait)
            except Exception as e:
                logger.error(f"[VeriBot] {name} POST 异常(attempt={attempt}): {e}")
                if attempt < 3:
                    await asyncio.sleep(3)
                else:
                    raise

    async def terminate(self):
        if self.db_engine:
            await db.close_engine(self.db_engine)
            logger.info("VeriBot 数据库连接已关闭")
