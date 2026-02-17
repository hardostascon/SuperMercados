import sys
sys.path.insert(0, '../..')

from app.core.config import settings
from app.core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_connection():
    logger.info(f"DATABASE_URL: {settings.DATABASE_URL}")
    logger.info(f"Test mode: {'Si' if not settings.DATABASE_URL else 'No'}")
    
    if not settings.DATABASE_URL:
        logger.error("DATABASE_URL no está configurada - Modo prueba activo")
        return False
    
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("SELECT 1"))
            logger.info("¡Conexión a SQL Server exitosa!")
            return True
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_database_connection())
