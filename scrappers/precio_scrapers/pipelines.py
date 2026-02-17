from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from decimal import Decimal
import json
import os
import logging

logger = logging.getLogger(__name__)

class DataCleaningPipeline:
    """Pipeline para limpiar y validar datos antes de guardar"""
    
    def process_item(self, item, spider):
        if not item.get('nombre') or not item.get('precio_actual'):
            raise Exception(f"Item inválido: falta nombre o precio")
        
        item['nombre'] = item['nombre'].strip()
        if item.get('marca'):
            item['marca'] = item['marca'].strip()
        
        if item['precio_actual'] <= 0:
            raise Exception(f"Precio inválido: {item['precio_actual']}")
        
        if item.get('url') and len(item['url']) > 2000:
            item['url'] = item['url'][:2000]
        
        if item.get('imagen_url') and len(item['imagen_url']) > 2000:
            item['imagen_url'] = item['imagen_url'][:2000]
        
        return item


class SQLServerPipeline:
    """Pipeline para guardar productos en SQL Server"""
    
    def __init__(self):
        self.test_mode = True
        self.items = []
        self.engine = None
        self.Session = None
        
        db_url = os.environ.get(
            'DATABASE_URL', 
            'mssql+pyodbc://HARDOS/precio_comparador?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&TrustServerCertificate=yes'
        )
        
        if db_url and 'mssql' in db_url:
            try:
                if '+aioodbc://' in db_url:
                    db_url = db_url.replace('+aioodbc://', '+pyodbc://')
                
                self.engine = create_engine(
                    db_url,
                    connect_args={"timeout": 30},
                    pool_pre_ping=True,
                    pool_recycle=3600,
                )
                self.Session = sessionmaker(bind=self.engine)
                self.test_mode = False
                logger.info(f"Conexion a SQL Server establecida: {db_url[:50]}...")
            except Exception as e:
                logger.warning(f"No se pudo conectar a BD: {e} - Modo prueba activo")
                self.test_mode = True
        else:
            logger.warning("DATABASE_URL no configurada - Modo prueba activo")
    
    def open_spider(self, spider):
        logger.info(f"Spider {spider.name} iniciado - Modo: {'Prueba' if self.test_mode else 'Producción'}")
    
    def close_spider(self, spider):
        if self.test_mode:
            output_file = f"{spider.name}_productos.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.items, f, ensure_ascii=False, indent=2)
            logger.info(f"Guardados {len(self.items)} productos en {output_file}")
        
        if self.engine:
            self.engine.dispose()
        logger.info(f"Spider {spider.name} finalizado")
    
    def process_item(self, item, spider):
        if self.test_mode:
            self.items.append(dict(item))
            logger.info(f"Producto agregado (prueba): {item['nombre'][:50]}...")
            return item
        
        session = self.Session()
        
        try:
            precio_actual = float(item['precio_actual'])
            precio_anterior = float(item['precio_anterior']) if item.get('precio_anterior') else None
            descuento = float(item['descuento_porcentaje']) if item.get('descuento_porcentaje') else None
            
            logger.debug(f"Procesando: {item['nombre'][:30]}...")
            
            check_query = text("""
                SELECT id FROM Hardos.productos 
                WHERE nombre = :nombre AND supermercado = :supermercado
            """)
            existente = session.execute(check_query, {
                'nombre': item['nombre'],
                'supermercado': item['supermercado']
            }).fetchone()
            
            if existente:
                if precio_anterior is not None:
                    update_query = text("""
                        UPDATE Hardos.productos 
                        SET precio_anterior = precio_actual,
                            precio_actual = :precio_actual,
                            descuento_porcentaje = :descuento,
                            fecha_extraccion = GETDATE()
                        WHERE id = :id
                    """)
                    session.execute(update_query, {
                        'precio_actual': precio_actual,
                        'descuento': descuento,
                        'id': existente[0]
                    })
                    session.commit()
                    logger.info(f"Precio actualizado: {item['nombre'][:50]}...")
            else:
                insert_query = text("""
                    INSERT INTO Hardos.productos 
                    (supermercado, nombre, marca, categoria, presentacion, 
                     precio_actual, precio_anterior, descuento_porcentaje, url, imagen_url)
                    VALUES 
                    (:supermercado, :nombre, :marca, :categoria, :presentacion,
                     :precio_actual, :precio_anterior, :descuento, :url, :imagen_url)
                """)
                session.execute(insert_query, {
                    'supermercado': item['supermercado'],
                    'nombre': item['nombre'],
                    'marca': item.get('marca'),
                    'categoria': item.get('categoria'),
                    'presentacion': item.get('presentacion'),
                    'precio_actual': precio_actual,
                    'precio_anterior': precio_anterior,
                    'descuento': descuento,
                    'url': item.get('url'),
                    'imagen_url': item.get('imagen_url'),
                })
                session.commit()
                logger.info(f"Nuevo producto: {item['nombre'][:50]}...")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error guardando producto {item.get('nombre', 'UNKNOWN')}: {e}")
        finally:
            session.close()
        
        return item
