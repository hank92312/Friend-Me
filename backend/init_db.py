import asyncio
from database import engine, Base
import models  # 確保 models 被載入以註冊 Base.metadata

async def init_models():
    async with engine.begin() as conn:
        # 如果需要重新建立，可以先 drop_all
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created.")

if __name__ == "__main__":
    asyncio.run(init_models())
