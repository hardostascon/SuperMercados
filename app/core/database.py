from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.core.config import settings
import urllib.parse

# Procesar URL para SQL Server
def get_database_url():
    """
    Procesa la URL de conexión para SQL Server
    Asegura formato correcto para aioodbc
    """
    url = settings.DATABASE_URL
    
    # Si la URL ya tiene el formato correcto, retornarla
    if url.startswith('mssql+aioodbc://'):
        return url
    
    # Si es formato pyodbc, convertir a aioodbc
    if url.startswith('mssql+pyodbc://'):
        return url.replace('mssql+pyodbc://', 'mssql+aioodbc://')
    
    return url

# Create async engine para SQL Server
engine = create_async_engine(
    get_database_url(),
    echo=settings.DEBUG,
    future=True,
    # SQL Server a veces tiene problemas con pool, usar NullPool
    poolclass=NullPool,
    # Parámetros específicos para SQL Server
    connect_args={
        "timeout": 30,
    }
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()