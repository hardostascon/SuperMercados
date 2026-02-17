"""
Script para probar el pipeline de guardado en SQL Server
"""
import sys
import os

# Agregar el path del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from precio_scrapers.spiders.exito_spider import ExitoSpider

def run_test():
    print("=" * 60)
    print("PRUEBA DE GUARDADO EN BASE DE DATOS")
    print("=" * 60)
    print(f"PYTHONPATH: {sys.path[:3]}")
    
    settings = get_project_settings()
    settings.setmodule('precio_scrapers.settings')
    settings['LOG_LEVEL'] = 'INFO'
    settings['CLOSESPIDER_PAGECOUNT'] = 1  # Solo 1 página para probar
    
    process = CrawlerProcess(settings)
    process.crawl(ExitoSpider)
    process.start()
    
    print("=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    run_test()
