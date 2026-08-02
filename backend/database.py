from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

import os

# 使用非同步 SQLite (aiosqlite)
# 支援透過環境變數指定資料庫路徑 (Fly.io Volume 需要)
DB_PATH = os.getenv("DB_PATH", "./friends_and_me.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# echo 會把每一句 SQL「連同繫結參數」寫進 stdout，也就是玩家暱稱、答題原文與題目
# 全都會進入平台的 log。這與隱私權政策「僅暫存於 RAM、零永久儲存」相抵觸，
# 因此預設關閉；本機除錯時可用 SQL_ECHO=1 開啟。
SQL_ECHO = os.getenv("SQL_ECHO", "0") == "1"

engine = create_async_engine(DATABASE_URL, echo=SQL_ECHO)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        from models import Base
        await conn.run_sync(Base.metadata.create_all)
