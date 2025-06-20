import asyncio
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.models import Base

tmpPostgres = urlparse(settings.DATABASE_URL)

async def async_main() -> None:
    engine = create_async_engine(f"postgresql+asyncpg://{tmpPostgres.username}:{tmpPostgres.password}@{tmpPostgres.hostname}{tmpPostgres.path}?ssl=require", echo=True)
    
    try:
        async with engine.begin() as conn:  # Use begin() instead of connect() for auto-commit
            # ✅ ADD THIS: Create all tables
            await conn.run_sync(Base.metadata.drop_all) 
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created successfully!")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(async_main())