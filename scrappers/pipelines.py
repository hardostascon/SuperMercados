from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.producto import Producto
from app.core.config import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class SQLServerPipeline:
    """Pipeline para guardar productos en SQL Server"""
    
    def __init__(self):
        # Convertir URL async a sync para Scrapy
        db_url = settings.DATABASE_URL
        
        # Cambiar de aioodbc a pyodbc (sync)
        if '+aioodbc://' in db_url:
            db_url = db_url.replace('+aioodbc://', '+pyodbc://')
        
        self.engine = create_engine(
            db_url,
            # SQL Server opciones específicas
            connect_args={
                "timeout": 30,
            },
            pool_pre_ping=True,  # Verificar conexiones antes de usar
            pool_recycle=3600,   # Reciclar conexiones cada hora
        )
        self.Session = sessionmaker(bind=self.engine)
    
    def open_spider(self, spider):
        """Se ejecuta cuando el spider inicia"""
        logger.info(f"Spider {spider.name} iniciado - Conectando a SQL Server")
    
    def close_spider(self, spider):
        """Se ejecuta cuando el spider termina"""
        self.engine.dispose()
        logger.info(f"Spider {spider.name} finalizado - Conexión SQL Server cerrada")
    
    def process_item(self, item, spider):
        """Procesa cada item scrapeado"""
        session = self.Session()
        
        try:
            # Verificar si el producto ya existe (mismo nombre y supermercado)
            producto_existente = session.query(Producto).filter_by(
                nombre=item['nombre'],
                supermercado=item['supermercado']
            ).first()
            
            # Convertir precios a Decimal para SQL Server
            precio_actual = Decimal(str(item['precio_actual']))
            precio_anterior = Decimal(str(item['precio_anterior'])) if item.get('precio_anterior') else None
            descuento = Decimal(str(item['descuento_porcentaje'])) if item.get('descuento_porcentaje') else None
            
            if producto_existente:
                # Actualizar precio si es diferente
                if producto_existente.precio_actual != precio_actual:
                    producto_existente.precio_anterior = producto_existente.precio_actual
                    producto_existente.precio_actual = precio_actual
                    producto_existente.descuento_porcentaje = descuento
                    
                    logger.info(f"Precio actualizado: {item['nombre']} - ${precio_actual}")
            else:
                # Crear nuevo producto
                nuevo_producto = Producto(
                    supermercado=item['supermercado'],
                    nombre=item['nombre'],
                    marca=item.get('marca'),
                    categoria=item.get('categoria'),
                    presentacion=item.get('presentacion'),
                    precio_actual=precio_actual,
                    precio_anterior=precio_anterior,
                    descuento_porcentaje=descuento,
                    url=item.get('url'),
                    imagen_url=item.get('imagen_url'),
                )
                session.add(nuevo_producto)
                logger.info(f"Nuevo producto agregado: {item['nombre']}")
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error al guardar producto en SQL Server: {e}")
            logger.error(f"Item: {item}")
            raise
        
        finally:
            session.close()
        
        return item

class DataCleaningPipeline:
    """Pipeline para limpiar y validar datos antes de guardar"""
    
    def process_item(self, item, spider):
        # Validar campos obligatorios
        if not item.get('nombre') or not item.get('precio_actual'):
            raise Exception(f"Item inválido: falta nombre o precio")
        
        # Limpiar espacios
        item['nombre'] = item['nombre'].strip()
        if item.get('marca'):
            item['marca'] = item['marca'].strip()
        
        # Validar precio positivo
        if item['precio_actual'] <= 0:
            raise Exception(f"Precio inválido: {item['precio_actual']}")
        
        # Truncar URLs si son muy largas (SQL Server límite)
        if item.get('url') and len(item['url']) > 2000:
            item['url'] = item['url'][:2000]
        
        if item.get('imagen_url') and len(item['imagen_url']) > 2000:
            item['imagen_url'] = item['imagen_url'][:2000]
        
        return item