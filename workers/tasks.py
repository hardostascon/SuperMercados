from workers.celery_app import celery_app
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker
from app.models.producto import Producto
from app.core.config import settings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name='workers.tasks.scrape_exito')
def scrape_exito():
    """Ejecuta el spider de Exito"""
    try:
        from scrappers.spiders.exito_spider import ExitoSpider
        
        process = CrawlerProcess(get_project_settings())
        process.crawl(ExitoSpider)
        process.start()
        
        logger.info("Spider Exito ejecutado exitosamente")
        return {"status": "success", "spider": "exito"}
    
    except Exception as e:
        logger.error(f"Error ejecutando spider Exito: {e}")
        return {"status": "error", "message": str(e)}

@celery_app.task(name='workers.tasks.scrape_carulla')
def scrape_carulla():
    """Ejecuta el spider de Carulla"""
    # Implementar similar a scrape_exito
    logger.info("Spider Carulla - Por implementar")
    return {"status": "pending", "spider": "carulla"}

@celery_app.task(name='workers.tasks.scrape_jumbo')
def scrape_jumbo():
    """Ejecuta el spider de Jumbo"""
    # Implementar similar a scrape_exito
    logger.info("Spider Jumbo - Por implementar")
    return {"status": "pending", "spider": "jumbo"}

@celery_app.task(name='workers.tasks.limpiar_datos_antiguos')
def limpiar_datos_antiguos(dias=30):
    """Elimina productos con más de X días de antigüedad"""
    try:
        db_url = settings.DATABASE_URL.replace('+asyncpg', '')
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        fecha_limite = datetime.utcnow() - timedelta(days=dias)
        
        # Eliminar productos antiguos
        result = session.execute(
            delete(Producto).where(Producto.fecha_extraccion < fecha_limite)
        )
        
        session.commit()
        eliminados = result.rowcount
        
        session.close()
        engine.dispose()
        
        logger.info(f"Eliminados {eliminados} productos antiguos")
        return {"status": "success", "eliminados": eliminados}
    
    except Exception as e:
        logger.error(f"Error limpiando datos: {e}")
        return {"status": "error", "message": str(e)}

@celery_app.task(name='workers.tasks.scrape_all')
def scrape_all():
    """Ejecuta todos los spiders"""
    results = []
    
    results.append(scrape_exito.delay())
    results.append(scrape_carulla.delay())
    results.append(scrape_jumbo.delay())
    
    return {"status": "scheduled", "tasks": len(results)}