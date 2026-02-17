from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.producto import Producto


class ProductoRepository:
    """Repositorio para operaciones de base de datos de Producto"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, producto_id: int) -> Optional[Producto]:
        """Obtener producto por ID"""
        result = await self.db.execute(
            select(Producto).where(Producto.id == producto_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        supermercado: Optional[str] = None,
        categoria: Optional[str] = None
    ) -> List[Producto]:
        """Obtener lista de productos con filtros opcionales"""
        query = select(Producto)
        
        if supermercado:
            query = query.where(Producto.supermercado == supermercado)
        if categoria:
            query = query.where(Producto.categoria == categoria)
        
        query = query.offset(skip).limit(limit).order_by(Producto.fecha_extraccion.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def search_by_name(self, termino: str, limit: int = 50) -> List[Producto]:
        """Buscar productos por nombre"""
        query = select(Producto).where(
            Producto.nombre.ilike(f"%{termino}%")
        ).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_for_comparison(
        self,
        termino: str,
        horas: int = 24
    ) -> List[Producto]:
        """Obtener productos para comparación de precios"""
        fecha_limite = datetime.utcnow() - timedelta(hours=horas)
        
        query = select(Producto).where(
            and_(
                Producto.nombre.ilike(f"%{termino}%"),
                Producto.fecha_extraccion >= fecha_limite
            )
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_supermercados(self) -> List[str]:
        """Obtener lista de supermercados únicos"""
        query = select(Producto.supermercado).distinct()
        result = await self.db.execute(query)
        return [row[0] for row in result.all()]
    
    async def get_categorias(self) -> List[str]:
        """Obtener lista de categorías únicas"""
        query = select(Producto.categoria).distinct().where(Producto.categoria.isnot(None))
        result = await self.db.execute(query)
        return [row[0] for row in result.all()]
    
    async def create(self, producto_data: dict) -> Producto:
        """Crear nuevo producto"""
        producto = Producto(**producto_data)
        self.db.add(producto)
        await self.db.commit()
        await self.db.refresh(producto)
        return producto
    
    async def update_precio(
        self,
        producto: Producto,
        nuevo_precio: Decimal,
        descuento: Optional[Decimal] = None
    ) -> Producto:
        """Actualizar precio de un producto"""
        producto.precio_anterior = producto.precio_actual
        producto.precio_actual = nuevo_precio
        producto.descuento_porcentaje = descuento
        await self.db.commit()
        await self.db.refresh(producto)
        return producto
    
    async def delete_old(self, dias: int = 30) -> int:
        """Eliminar productos antiguos"""
        fecha_limite = datetime.utcnow() - timedelta(days=dias)
        
        result = await self.db.execute(
            delete(Producto).where(Producto.fecha_extraccion < fecha_limite)
        )
        await self.db.commit()
        return result.rowcount
    
    async def count_by_supermercado(self, supermercado: str) -> int:
        """Contar productos por supermercado"""
        query = select(func.count()).where(Producto.supermercado == supermercado)
        result = await self.db.execute(query)
        return result.scalar()
    
    async def exists_by_nombre_supermercado(
        self,
        nombre: str,
        supermercado: str
    ) -> bool:
        """Verificar si existe un producto por nombre y supermercado"""
        query = select(func.count()).where(
            and_(
                Producto.nombre == nombre,
                Producto.supermercado == supermercado
            )
        )
        result = await self.db.execute(query)
        return result.scalar() > 0