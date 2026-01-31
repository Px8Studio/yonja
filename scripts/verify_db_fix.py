import asyncio

import asyncpg


async def verify():
    url = "postgresql://alim:alim_dev_password@localhost:5433/alim"
    print(f"Connecting to {url}...")
    try:
        conn = await asyncpg.connect(url)
        tables = await conn.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )
        table_names = [t["table_name"] for t in tables]
        print("Existing tables:", table_names)

        required = ["users", "threads", "steps", "checkpoints", "checkpoint_writes"]
        missing = [t for t in required if t not in table_names]

        if missing:
            print(f"❌ Missing tables: {missing}")
        else:
            print("✅ All required tables exist!")

        await conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(verify())
