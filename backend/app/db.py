from contextlib import asynccontextmanager
from anyio import to_thread
import psycopg
from .config import DATABASE_URL

class AsyncConn:
    def __init__(self, conn): self._c = conn
    async def commit(self): return await to_thread.run_sync(self._c.commit)

class AsyncCursor:
    def __init__(self, cur): self._c = cur
    async def execute(self, *a, **k): return await to_thread.run_sync(self._c.execute, *a, **k)
    async def fetchone(self): return await to_thread.run_sync(self._c.fetchone)
    async def fetchall(self): return await to_thread.run_sync(self._c.fetchall)
    async def close(self): return await to_thread.run_sync(self._c.close)

async def init_pool():  # kept for compatibility with app.main
    return None

async def close_pool():
    return None

@asynccontextmanager
async def conn_cursor():
    # Open a fresh connection per request to avoid pool/timeouts on Windows + Neon
    conn = await to_thread.run_sync(psycopg.connect, DATABASE_URL)
    cur = await to_thread.run_sync(conn.cursor)
    aconn, acur = AsyncConn(conn), AsyncCursor(cur)
    try:
        yield aconn, acur
    finally:
        try:
            await acur.close()
        finally:
            await to_thread.run_sync(conn.close)
