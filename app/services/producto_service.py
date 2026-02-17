from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from app.repositories.producto_repository import ProductoRepository
from app.schemas.producto import ProductoCreate, ProductoUpdate, ComparacionProducto


class ProductoService:
    """Servicio para lógica de negocio de productos"""
    
    def __init__(self, db: AsyncSession):
        self.repository = ProductoRepository(db)
    
    async def get_producto(self, producto_id: int):
        """Obtener un producto por ID"""
        return await self.repository.get_by_id(producto_id)
    
    async def list_productos(
        self,
        skip: int = 0,
        limit: int = 100,
        supermercado: Optional[str] = None,
        categoria: Optional[str] = None
    ):
        """Listar productos con filtros"""
        return await self.repository.get_all(
            skip=skip,
            limit=limit,
            supermercado=supermercado,
            categoria=categoria
        )
    
    async def search_productos(self, termino: str, limit: int = 50):
        """Buscar productos por término"""
        termino_limpio = self._sanitizar_termino(termino)
        return await self.repository.search_by_name(termino_limpio, limit)
    
    async def comparar_precios(self, termino: str) -> Optional[ComparacionProducto]:
        """Comparar precios de un producto entre supermercados"""
        termino_limpio = self._sanitizar_termino(termino)
        productos = await self.repository.get_for_comparison(termino_limpio)
        
        if not productos:
            return None
        
        precios = [p.precio_actual for p in productos if p.precio_actual]
        if not precios:
            return None
        
        mejor_precio = min(precios)
        precio_promedio = sum(precios) / len(precios)
        
        producto_mejor = next(
            (p for p in productos if p.precio_actual == mejor_precio),
            productos[0]
        )
        
        precios_por_super = [
            {
                "supermercado": p.supermercado,
                "precio": float(p.precio_actual) if p.precio_actual else None,
                "descuento": float(p.descuento_porcentaje) if p.descuento_porcentaje else None,
                "url": p.url
            }
            for p in productos
            if p.precio_actual
        ]
        
        return ComparacionProducto(
            nombre=productos[0].nombre,
            mejor_precio=float(mejor_precio),
            supermercado_mejor_precio=producto_mejor.supermercado,
            precio_promedio=round(float(precio_promedio), 2),
            precios_por_supermercado=precios_por_super
        )
    
    async def get_supermercados(self) -> List[str]:
        """Obtener lista de supermercados"""
        return await self.repository.get_supermercados()
    
    async def get_categorias(self) -> List[str]:
        """Obtener lista de categorías"""
        return await self.repository.get_categorias()
    
    async def create_producto(self, producto_data: ProductoCreate):
        """Crear nuevo producto"""
        data = producto_data.model_dump()
        data["precio_actual"] = Decimal(str(data["precio_actual"]))
        if data.get("precio_anterior"):
            data["precio_anterior"] = Decimal(str(data["precio_anterior"]))
        if data.get("descuento_porcentaje"):
            data["descuento_porcentaje"] = Decimal(str(data["descuento_porcentaje"]))
        
        return await self.repository.create(data)
    
    async def update_precio(
        self,
        producto_id: int,
        nuevo_precio: Decimal,
        descuento: Optional[Decimal] = None
    ):
        """Actualizar precio de un producto"""
        producto = await self.repository.get_by_id(producto_id)
        if not producto:
            return None
        
        return await self.repository.update_precio(producto, nuevo_precio, descuento)
    
    async def limpiar_antiguos(self, dias: int = 30) -> int:
        """Limpiar productos antiguos"""
        return await self.repository.delete_old(dias)
    
    async def get_estadisticas(self) -> Dict[str, Any]:
        """Obtener estadísticas de productos"""
        supermercados = await self.repository.get_supermercados()
        
        stats = {
            "supermercados": [],
            "total_productos": 0
        }
        
        for super in supermercados:
            count = await self.repository.count_by_supermercado(super)
            stats["supermercados"].append({
                "nombre": super,
                "total": count
            })
            stats["total_productos"] += count
        
        return stats
    
    def _sanitizar_termino(self, termino: str) -> str:
        """Sanitiza término de búsqueda para evitar SQL injection"""
        termino = termino.strip()
        termino = termino.replace("%", "\\%")
        termino = termino.replace("_", "\\_")
        termino = termino.replace(";", "")
        termino = termino.replace("--", "")
        termino = termino.replace("'", "''")
        
        if len(termino) > 500:
            termino = termino[:500]
        
        return termino