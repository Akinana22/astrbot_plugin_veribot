from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text

DEFAULT_PORT = {
    "postgresql": 5432,
    "mysql": 3306,
    "mariadb": 3306,
}


def _build_url(db_type, host, port, user, password, database):
    if db_type == "sqlite":
        return f"sqlite+aiosqlite:///{database}"
    p = port if port else DEFAULT_PORT.get(db_type, 0)
    return f"{db_type}+{DRIVER[db_type]}://{user}:{password}@{host}:{p}/{database}"


DRIVER = {
    "postgresql": "asyncpg",
    "mysql": "asyncmy",
    "mariadb": "asyncmy",
    "sqlite": "aiosqlite",
}


async def init_engine(db_type, host, port, database, user, password):
    url = _build_url(db_type, host, port, user, password, database)
    engine = create_async_engine(url, echo=False)
    return engine


def _create_table_sql(db_type, table, platform_col, uid_col, code_col, is_used_col):
    if db_type == "postgresql":
        return text(
            f"""CREATE TABLE IF NOT EXISTS {table} (
                id BIGSERIAL PRIMARY KEY,
                {platform_col} VARCHAR(16) NOT NULL,
                {uid_col} VARCHAR(128) NOT NULL,
                {code_col} VARCHAR(255) NOT NULL,
                {is_used_col} BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_{table}_platform_user UNIQUE ({platform_col}, {uid_col})
            )"""
        )
    elif db_type in ("mysql", "mariadb"):
        return text(
            f"""CREATE TABLE IF NOT EXISTS {table} (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                {platform_col} VARCHAR(16) NOT NULL,
                {uid_col} VARCHAR(128) NOT NULL,
                {code_col} VARCHAR(255) NOT NULL,
                {is_used_col} BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_{table}_platform_user ({platform_col}, {uid_col})
            )"""
        )
    else:
        return text(
            f"""CREATE TABLE IF NOT EXISTS {table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {platform_col} VARCHAR(16) NOT NULL,
                {uid_col} VARCHAR(128) NOT NULL,
                {code_col} VARCHAR(255) NOT NULL,
                {is_used_col} BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE({platform_col}, {uid_col})
            )"""
        )


async def ensure_tables(engine, db_type, table, platform_col, uid_col, code_col, is_used_col):
    sql = _create_table_sql(db_type, table, platform_col, uid_col, code_col, is_used_col)
    async with engine.begin() as conn:
        await conn.execute(sql)


async def get_binding(engine, db_type, table, uid_col, code_col, is_used_col, platform_col, platform_val, user_id):
    sql = text(
        f"SELECT {code_col}, {is_used_col} FROM {table} WHERE {platform_col} = :platform AND {uid_col} = :uid"
    )
    async with engine.connect() as conn:
        result = await conn.execute(sql, {"platform": platform_val, "uid": user_id})
        row = result.fetchone()
        if row is None:
            return None
        return {code_col: row[0], is_used_col: row[1]}


async def save_auth_code(engine, db_type, table, uid_col, code_col, is_used_col, platform_col, platform_val, user_id, hash_code):
    if db_type in ("mysql", "mariadb"):
        sql = text(
            f"INSERT IGNORE INTO {table} ({platform_col}, {uid_col}, {code_col}, {is_used_col}) "
            f"VALUES (:platform, :uid, :code, :used)"
        )
    elif db_type == "sqlite":
        sql = text(
            f"INSERT OR IGNORE INTO {table} ({platform_col}, {uid_col}, {code_col}, {is_used_col}) "
            f"VALUES (:platform, :uid, :code, :used)"
        )
    else:
        sql = text(
            f"INSERT INTO {table} ({platform_col}, {uid_col}, {code_col}, {is_used_col}) "
            f"VALUES (:platform, :uid, :code, :used) "
            f"ON CONFLICT ({platform_col}, {uid_col}) DO NOTHING"
        )
    async with engine.begin() as conn:
        await conn.execute(sql, {"platform": platform_val, "uid": user_id, "code": hash_code, "used": False})


async def close_engine(engine):
    await engine.dispose()
