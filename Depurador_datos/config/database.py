# config/database.py
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import urllib

class DatabaseConfig:
    """Configuración para SQL Server"""
    
    @staticmethod
    def get_engine():
        """Obtiene engine desde variable de entorno"""
        load_dotenv()  # Carga variables del archivo .env
        
        # Opción 1: Usar directamente la URL
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            # Asegurar que usa pyodbc en lugar de aioodbc
            database_url = database_url.replace('aioodbc', 'pyodbc')
            engine = create_engine(database_url)
        else:
            # Opción 2: Construir manualmente
            engine = DatabaseConfig.get_engine_manual()
        
        print(f"Conexión establecida a SQL Server")
        return engine
    
    @staticmethod
    def get_engine_manual():
        """Construye la conexión manualmente con tus datos"""
        server = 'HARDOS'
        database = 'precio_comparador'
        username = 'Hardos'
        password = '12345'
        port = 1433
        driver = 'ODBC Driver 18 for SQL Server'
        
        # URL encode de la contraseña por si tiene caracteres especiales
        password_encoded = urllib.parse.quote_plus(password)
        driver_encoded = urllib.parse.quote_plus(driver)
        
        connection_string = (
            f"mssql+pyodbc://{username}:{password_encoded}"
            f"@{server}:{port}/{database}"
            f"?driver={driver_encoded}"
            f"&TrustServerCertificate=yes"
        )
        
        engine = create_engine(
            connection_string,
            # Opciones adicionales recomendadas
            pool_pre_ping=True,  # Verifica conexión antes de usar
            pool_recycle=3600,   # Recicla conexiones cada hora
            echo=False           # True para debug SQL
        )
        
        return engine
    
    @staticmethod
    def test_connection(engine):
        """Prueba la conexión"""
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT @@VERSION"))
                version = result.fetchone()[0]
                print(f"Versión SQL Server: {version[:50]}...")
                return True
        except Exception as e:
            print(f"Error de conexión: {e}")
            return False