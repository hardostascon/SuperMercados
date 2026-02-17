import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from decimal import Decimal
from datetime import datetime


@pytest.fixture
def mock_db_session():
    """Mock de sesión de base de datos"""
    session = AsyncMock()
    return session


@pytest.fixture
def sample_producto():
    """Producto de ejemplo para tests"""
    return {
        "id": 1,
        "supermercado": "Exito",
        "nombre": "Arroz Diana 1kg",
        "marca": "Diana",
        "categoria": "Granos",
        "presentacion": "1kg",
        "precio_actual": 4500.00,
        "precio_anterior": 5000.00,
        "descuento_porcentaje": 10.0,
        "url": "https://exito.com/producto/123",
        "imagen_url": "https://exito.com/img/123.jpg",
        "fecha_extraccion": datetime.utcnow(),
        "fecha_actualizacion": None,
    }


class TestProductosEndpoints:
    """Tests para endpoints de productos"""
    
    @pytest.mark.asyncio
    async def test_listar_productos_empty(self, mock_db_session):
        """Test listar productos cuando no hay datos"""
        from app.api.endpoints.productos import listar_productos
        
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
        
        result = await listar_productos(db=mock_db_session)
        assert result == []
    
    @pytest.mark.asyncio
    async def test_listar_productos_with_filters(self, mock_db_session, sample_producto):
        """Test listar productos con filtros"""
        from app.api.endpoints.productos import listar_productos
        from app.models.producto import Producto
        
        mock_producto = Producto(**sample_producto)
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = [mock_producto]
        
        result = await listar_productos(
            supermercado="Exito",
            categoria="Granos",
            db=mock_db_session
        )
        
        assert len(result) == 1
        assert result[0].supermercado == "Exito"
    
    @pytest.mark.asyncio
    async def test_obtener_producto_not_found(self, mock_db_session):
        """Test obtener producto que no existe"""
        from app.api.endpoints.productos import obtener_producto
        from fastapi import HTTPException
        
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await obtener_producto(999, db=mock_db_session)
        
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_buscar_productos(self, mock_db_session, sample_producto):
        """Test búsqueda de productos"""
        from app.api.endpoints.productos import buscar_productos
        from app.models.producto import Producto
        
        mock_producto = Producto(**sample_producto)
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = [mock_producto]
        
        result = await buscar_productos("arroz", db=mock_db_session)
        assert len(result) == 1


class TestProductoModel:
    """Tests para el modelo Producto"""
    
    def test_producto_creation(self, sample_producto):
        """Test creación de modelo Producto"""
        from app.models.producto import Producto
        
        producto = Producto(**sample_producto)
        
        assert producto.nombre == sample_producto["nombre"]
        assert producto.supermercado == sample_producto["supermercado"]
        assert producto.precio_actual == Decimal(str(sample_producto["precio_actual"]))
    
    def test_producto_repr(self, sample_producto):
        """Test representación string de Producto"""
        from app.models.producto import Producto
        
        producto = Producto(**sample_producto)
        repr_str = repr(producto)
        
        assert "Producto" in repr_str
        assert sample_producto["nombre"] in repr_str


class TestProductoSchemas:
    """Tests para schemas de Producto"""
    
    def test_producto_base_validation(self, sample_producto):
        """Test validación de ProductoBase"""
        from app.schemas.producto import ProductoBase
        
        producto_base = ProductoBase(**sample_producto)
        
        assert producto_base.nombre == sample_producto["nombre"]
        assert producto_base.precio_actual == sample_producto["precio_actual"]
    
    def test_producto_create(self, sample_producto):
        """Test schema de creación de producto"""
        from app.schemas.producto import ProductoCreate
        
        producto_create = ProductoCreate(**sample_producto)
        
        assert producto_create.nombre == sample_producto["nombre"]
    
    def test_producto_response(self, sample_producto):
        """Test schema de respuesta de producto"""
        from app.schemas.producto import ProductoResponse
        
        sample_producto["id"] = 1
        sample_producto["fecha_extraccion"] = datetime.utcnow()
        
        producto_response = ProductoResponse(**sample_producto)
        
        assert producto_response.id == 1
    
    def test_precio_positive_validation(self, sample_producto):
        """Test que precio debe ser positivo"""
        from app.schemas.producto import ProductoBase
        from pydantic import ValidationError
        
        sample_producto["precio_actual"] = -100
        
        with pytest.raises(ValidationError):
            ProductoBase(**sample_producto)