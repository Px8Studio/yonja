import asyncio

import asyncpg


async def drop_blocker():
    url = "postgresql://alim:alim_dev_password@localhost:5433/alim"
    print(f"Connecting to {url}...")
    try:
        conn = await asyncpg.connect(url)
        tables_to_drop = [
            "conversation_contexts",
            "users",
            "threads",
            "steps",
            "elements",
            "feedbacks",
        ]

        for table in tables_to_drop:
            print(f"Attempting to drop {table}...")
            await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"✅ Dropped (if existed) {table}.")

        await conn.close()
    except Exception as e:
        print(f"❌ Operation failed: {e}")


if __name__ == "__main__":
    asyncio.run(drop_blocker())
