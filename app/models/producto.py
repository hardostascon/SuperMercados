from sqlalchemy import Column, Integer, String, DateTime, Index, DECIMAL
from sqlalchemy.sql import func
from app.core.database import Base

class Producto(Base):
    __tablename__ = "productos"
    
    __table_args__ = (
        Index('idx_nombre_supermercado', 'nombre', 'supermercado'),
        Index('idx_fecha_extraccion', 'fecha_extraccion'),
        Index('idx_categoria', 'categoria'),
        {'schema': 'Hardos'},
    )
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supermercado = Column(String(100), nullable=False, index=True)
    nombre = Column(String(500), nullable=False)
    marca = Column(String(200))
    categoria = Column(String(200), index=True)
    presentacion = Column(String(100))
    
    precio_actual = Column(DECIMAL(10, 2), nullable=False)
    precio_anterior = Column(DECIMAL(10, 2), nullable=True)
    descuento_porcentaje = Column(DECIMAL(5, 2), nullable=True)
    
    url = Column(String(2000))
    imagen_url = Column(String(2000))
    
    fecha_extraccion = Column(DateTime, server_default=func.getdate())
    fecha_actualizacion = Column(DateTime, onupdate=func.getdate())
    
    def __repr__(self):
        return f"<Producto(nombre={self.nombre}, supermercado={self.supermercado}, precio={self.precio_actual})>"