import asyncpg

CREATE_USERS_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id            BIGSERIAL PRIMARY KEY,
    username      VARCHAR(64) NOT NULL,
    user_number   INTEGER NOT NULL,
    account       VARCHAR(128) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_username_number UNIQUE (username, user_number)
);
"""

CREATE_INDEX_USERS_ACCOUNT_SQL = """
CREATE INDEX IF NOT EXISTS idx_users_account ON users (account);
"""

CREATE_PLATFORM_BINDINGS_SQL = """
CREATE TABLE IF NOT EXISTS platform_bindings (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform            VARCHAR(16) NOT NULL,
    platform_user_id    VARCHAR(128) NOT NULL,
    register_code_hash  VARCHAR(255) NOT NULL,
    is_used             BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_platform_user UNIQUE (platform, platform_user_id)
);
"""

CREATE_INDEX_PLATFORM_BINDINGS_LOOKUP_SQL = """
CREATE INDEX IF NOT EXISTS idx_platform_bindings_lookup ON platform_bindings (platform, platform_user_id);
"""

CREATE_INDEX_PLATFORM_BINDINGS_USER_SQL = """
CREATE INDEX IF NOT EXISTS idx_platform_bindings_user ON platform_bindings (user_id);
"""


async def init_pool(host, port, database, user, password):
    pool = await asyncpg.create_pool(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
    )
    async with pool.acquire() as conn:
        await conn.execute(CREATE_USERS_SQL)
        await conn.execute(CREATE_INDEX_USERS_ACCOUNT_SQL)
        await conn.execute(CREATE_PLATFORM_BINDINGS_SQL)
        await conn.execute(CREATE_INDEX_PLATFORM_BINDINGS_LOOKUP_SQL)
        await conn.execute(CREATE_INDEX_PLATFORM_BINDINGS_USER_SQL)
    return pool


async def get_binding(pool, platform, platform_user_id):
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT register_code_hash, is_used FROM platform_bindings WHERE platform = $1 AND platform_user_id = $2",
            platform,
            platform_user_id,
        )


async def save_auth_code(pool, platform, platform_user_id, register_code_hash):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO platform_bindings (platform, platform_user_id, register_code_hash, is_used)
            VALUES ($1, $2, $3, FALSE)
            ON CONFLICT (platform, platform_user_id) DO NOTHING
            """,
            platform,
            platform_user_id,
            register_code_hash,
        )
