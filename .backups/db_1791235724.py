import asyncpg
from bot import config

pool = None


async def init_db():
    global pool
    pool = await asyncpg.create_pool(
        config.DATABASE_URL,
        min_size=1, max_size=10, ssl="require"
    )
    await _create_tables()
    await _migrate()


async def close_db():
    if pool:
        await pool.close()


async def _create_tables():
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                username TEXT,
                show_nsfw BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS groups (
                id SERIAL PRIMARY KEY,
                link TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                country TEXT,
                language TEXT,
                members_range TEXT,
                members_estimate INTEGER DEFAULT 0,
                is_adult BOOLEAN DEFAULT FALSE,
                tags TEXT,
                owner_id BIGINT,
                views INTEGER DEFAULT 0,
                type TEXT DEFAULT 'group',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_country  ON groups(country);
            CREATE INDEX IF NOT EXISTS idx_language ON groups(language);
            CREATE INDEX IF NOT EXISTS idx_category ON groups(category);
            CREATE INDEX IF NOT EXISTS idx_adult    ON groups(is_adult);
            CREATE INDEX IF NOT EXISTS idx_type     ON groups(type);
        """)


async def _migrate():
    async with pool.acquire() as conn:
        await conn.execute("""
            ALTER TABLE groups ADD COLUMN IF NOT EXISTS type TEXT DEFAULT 'group'
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON groups(type)")


async def upsert_user(user_id, username=None):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (id, username) VALUES ($1, $2)
            ON CONFLICT (id) DO UPDATE SET username = EXCLUDED.username
        """, user_id, username)


async def get_user(user_id):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE id=$1", user_id)


async def toggle_nsfw(user_id):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            UPDATE users SET show_nsfw = NOT show_nsfw
            WHERE id=$1 RETURNING show_nsfw
        """, user_id)
        return row["show_nsfw"]


async def group_exists(link):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id FROM groups WHERE link=$1", link)
        return row is not None


async def add_group(data):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO groups
                (link, title, description, category, country, language,
                 members_range, members_estimate, is_adult, tags, owner_id, type)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            RETURNING id
        """,
            data["link"], data["title"], data["description"],
            data["category"], data["country"], data["language"],
            data["members_range"], data["members_estimate"],
            data["is_adult"], data["tags"], data["owner_id"],
            data.get("type", "group")
        )
        return row["id"]


async def my_groups(user_id):
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM groups WHERE owner_id=$1 ORDER BY created_at DESC", user_id
        )


async def search_groups(query, filters, page=0):
    sql = """
        SELECT * FROM groups
        WHERE (title ILIKE $1 OR description ILIKE $1 OR tags ILIKE $1)
          AND ($2::text IS NULL OR country = $2)
          AND ($3::text IS NULL OR language = $3)
          AND ($4::text IS NULL OR category = $4)
          AND ($5::int  IS NULL OR members_estimate >= $5)
          AND ($6::bool IS NULL OR is_adult = $6)
          AND ($7::text IS NULL OR type = $7)
        ORDER BY members_estimate DESC, created_at DESC
        LIMIT 10 OFFSET $8
    """
    async with pool.acquire() as conn:
        return await conn.fetch(
            sql, f"%{query}%",
            filters.get("country"), filters.get("language"),
            filters.get("category"), filters.get("min_members"),
            filters.get("is_adult"), filters.get("type"),
            page * 10
        )


async def count_groups(query=None, filters=None, category=None):
    filters = filters or {}
    async with pool.acquire() as conn:
        if query is not None:
            row = await conn.fetchrow("""
                SELECT COUNT(*) FROM groups
                WHERE (title ILIKE $1 OR description ILIKE $1 OR tags ILIKE $1)
                  AND ($2::text IS NULL OR country = $2)
                  AND ($3::text IS NULL OR language = $3)
                  AND ($4::text IS NULL OR category = $4)
                  AND ($5::int  IS NULL OR members_estimate >= $5)
                  AND ($6::bool IS NULL OR is_adult = $6)
                  AND ($7::text IS NULL OR type = $7)
            """, f"%{query}%",
                filters.get("country"), filters.get("language"),
                filters.get("category"), filters.get("min_members"),
                filters.get("is_adult"), filters.get("type"))
        else:
            row = await conn.fetchrow("""
                SELECT COUNT(*) FROM groups
                WHERE category = $1
                  AND ($2::text IS NULL OR country = $2)
                  AND ($3::text IS NULL OR language = $3)
                  AND ($4::bool IS NULL OR is_adult = $4)
                  AND ($5::text IS NULL OR type = $5)
            """, category,
                filters.get("country"), filters.get("language"),
                filters.get("is_adult"), filters.get("type"))
        return row["count"]


async def browse_category(category, filters, page=0):
    sql = """
        SELECT * FROM groups
        WHERE category = $1
          AND ($2::text IS NULL OR country = $2)
          AND ($3::text IS NULL OR language = $3)
          AND ($4::bool IS NULL OR is_adult = $4)
          AND ($5::text IS NULL OR type = $5)
        ORDER BY members_estimate DESC, created_at DESC
        LIMIT 10 OFFSET $6
    """
    async with pool.acquire() as conn:
        return await conn.fetch(
            sql, category,
            filters.get("country"), filters.get("language"),
            filters.get("is_adult"), filters.get("type"), page * 10
        )


async def list_by_type(group_type, order, filters, page=0, per_page=20):
    order_sql = {
        "asc": "title ASC", "desc": "title DESC",
        "members": "members_estimate DESC, title ASC",
        "recent": "created_at DESC",
        "views": "views DESC, title ASC",
    }.get(order, "title ASC")

    sql = f"""
        SELECT * FROM groups
        WHERE ($1::text IS NULL OR type = $1)
          AND ($2::text IS NULL OR country = $2)
          AND ($3::text IS NULL OR language = $3)
          AND ($4::text IS NULL OR category = $4)
          AND ($5::int  IS NULL OR members_estimate >= $5)
          AND ($6::bool IS NULL OR is_adult = $6)
        ORDER BY {order_sql}
        LIMIT {per_page} OFFSET $7
    """
    async with pool.acquire() as conn:
        return await conn.fetch(
            sql, None if group_type == "all" else group_type,
            filters.get("country"), filters.get("language"),
            filters.get("category"), filters.get("min_members"),
            filters.get("is_adult"), page * per_page
        )


async def count_by_type(group_type=None, filters=None):
    filters = filters or {}
    sql = """
        SELECT COUNT(*) FROM groups
        WHERE ($1::text IS NULL OR type = $1)
          AND ($2::text IS NULL OR country = $2)
          AND ($3::text IS NULL OR language = $3)
          AND ($4::text IS NULL OR category = $4)
          AND ($5::int  IS NULL OR members_estimate >= $5)
          AND ($6::bool IS NULL OR is_adult = $6)
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            sql, None if group_type in (None, "all") else group_type,
            filters.get("country"), filters.get("language"),
            filters.get("category"), filters.get("min_members"),
            filters.get("is_adult")
        )
        return row["count"]


async def get_top_groups(limit=10, filters=None):
    filters = filters or {}
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM groups
            WHERE ($1::bool IS NULL OR is_adult = $1)
              AND ($2::text IS NULL OR type = $2)
            ORDER BY views DESC, members_estimate DESC
            LIMIT $3
        """, filters.get("is_adult"), filters.get("type"), limit)
