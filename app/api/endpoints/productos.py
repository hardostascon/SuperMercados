from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.services.producto_service import ProductoService
from app.schemas.producto import ProductoResponse, ComparacionProducto

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db)) -> ProductoService:
    """Dependency para obtener instancia del servicio"""
    return ProductoService(db)


@router.get("/productos", response_model=List[ProductoResponse])
async def listar_productos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    supermercado: Optional[str] = None,
    categoria: Optional[str] = None,
    service: ProductoService = Depends(get_service)
):
    """Lista productos con filtros opcionales"""
    productos = await service.list_productos(
        skip=skip,
        limit=limit,
        supermercado=supermercado,
        categoria=categoria
    )
    return productos


@router.get("/productos/{producto_id}", response_model=ProductoResponse)
async def obtener_producto(
    producto_id: int,
    service: ProductoService = Depends(get_service)
):
    """Obtiene un producto específico por ID"""
    producto = await service.get_producto(producto_id)
    
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    return producto


@router.get("/productos/buscar/{termino}", response_model=List[ProductoResponse])
async def buscar_productos(
    termino: str,
    limit: int = Query(50, ge=1, le=200),
    service: ProductoService = Depends(get_service)
):
    """Busca productos por nombre"""
    productos = await service.search_productos(termino, limit)
    return productos


@router.get("/comparar/{termino}", response_model=ComparacionProducto)
async def comparar_precios(
    termino: str,
    service: ProductoService = Depends(get_service)
):
    """Compara precios del mismo producto en diferentes supermercados"""
    resultado = await service.comparar_precios(termino)
    
    if not resultado:
        raise HTTPException(status_code=404, detail="No se encontraron productos recientes")
    
    return resultado


@router.get("/supermercados", response_model=List[str])
async def listar_supermercados(service: ProductoService = Depends(get_service)):
    """Lista todos los supermercados disponibles"""
    return await service.get_supermercados()


@router.get("/categorias", response_model=List[str])
async def listar_categorias(service: ProductoService = Depends(get_service)):
    """Lista todas las categorías disponibles"""
    return await service.get_categorias()


@router.get("/estadisticas")
async def obtener_estadisticas(service: ProductoService = Depends(get_service)):
    """Obtiene estadísticas de productos por supermercado"""
    return await service.get_estadisticas()