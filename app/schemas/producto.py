from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ProductoBase(BaseModel):
    supermercado: str = Field(..., max_length=100)
    nombre: str = Field(..., max_length=500)
    marca: Optional[str] = Field(None, max_length=200)
    categoria: Optional[str] = Field(None, max_length=200)
    presentacion: Optional[str] = Field(None, max_length=100)
    precio_actual: float = Field(..., gt=0)
    precio_anterior: Optional[float] = Field(None, gt=0)
    descuento_porcentaje: Optional[float] = None
    url: Optional[str] = None
    imagen_url: Optional[str] = None

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(BaseModel):
    precio_actual: Optional[float] = Field(None, gt=0)
    precio_anterior: Optional[float] = None
    descuento_porcentaje: Optional[float] = None

class ProductoResponse(ProductoBase):
    id: int
    fecha_extraccion: datetime
    fecha_actualizacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ComparacionProducto(BaseModel):
    nombre: str
    mejor_precio: float
    supermercado_mejor_precio: str
    precio_promedio: float
    precios_por_supermercado: list[dict]