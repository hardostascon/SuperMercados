import pytest
from pydantic import ValidationError


class TestConfig:
    """Tests para la configuración"""
    
    def test_settings_defaults(self):
        """Test valores por defecto de configuración"""
        from app.core.config import Settings
        
        settings = Settings(
            DATABASE_URL="test",
            _env_file=None
        )
        
        assert settings.API_V1_PREFIX == "/api/v1"
        assert settings.DEBUG is False
        assert settings.DOWNLOAD_DELAY == 2
        assert settings.CONCURRENT_REQUESTS == 8
    
    def test_settings_custom_values(self):
        """Test valores personalizados de configuración"""
        from app.core.config import Settings
        
        settings = Settings(
            DATABASE_URL="postgresql://test",
            REDIS_URL="redis://custom:6379/1",
            DEBUG=True,
            _env_file=None
        )
        
        assert settings.REDIS_URL == "redis://custom:6379/1"
        assert settings.DEBUG is True


class TestDatabase:
    """Tests para configuración de base de datos"""
    
    def test_get_database_url_aioodbc(self):
        """Test conversión de URL a aioodbc"""
        from app.core.database import get_database_url
        from unittest.mock import patch
        
        with patch("app.core.database.settings") as mock_settings:
            mock_settings.DATABASE_URL = "mssql+pyodbc://user:pass@server/db"
            
            result = get_database_url()
            
            assert "aioodbc" in result
    
    def test_get_database_url_already_aioodbc(self):
        """Test URL ya en formato aioodbc"""
        from app.core.database import get_database_url
        from unittest.mock import patch
        
        with patch("app.core.database.settings") as mock_settings:
            mock_settings.DATABASE_URL = "mssql+aioodbc://user:pass@server/db"
            
            result = get_database_url()
            
            assert result == "mssql+aioodbc://user:pass@server/db"