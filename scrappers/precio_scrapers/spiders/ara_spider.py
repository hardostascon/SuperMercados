import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
import re

class AraSpider(scrapy.Spider):
    name = "ara"
    allowed_domains = ["losprecios.co"]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 4,
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
        }
    }
    
    def start_requests(self):
        urls = [
            'https://losprecios.co/ara_t2',
        ]
        
        for url in urls:
            yield scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_timeout', 10000),
                        PageMethod('evaluate', 'window.scrollTo(0, document.body.scrollHeight)'),
                        PageMethod('wait_for_timeout', 3000),
                    ],
                    'page': 1
                },
                callback=self.parse,
            )
    
    def parse(self, response):
        page = response.meta.get('page', 1)
        self.logger.info(f'URL scrapeada: {response.url} (Página {page})')
        
        html = response.text
        
        productos = []
        patrón = r'<button[^>]*class="btn btn-secondary btn-xs b-ed-pr"[^>]*data-n-tienda="Ara"[^>]*data-n-ítem="([^"]+)"[^>]*data-precio="([^"]+)"[^>]*data-img-ítem="([^"]*)"[^>]*>'
        
        matches = re.findall(patrón, html)
        
        self.logger.info(f'Productos encontrados en página {page}: {len(matches)}')
        
        if not matches and page == 1:
            self.logger.warning('No se encontraron productos en la primera página. Guardando HTML para debug...')
            with open('ara_debug.html', 'w', encoding='utf-8') as f:
                f.write(html)
            self.logger.warning('HTML guardado en ara_debug.html')
            return
        
        productos_scraped = 0
        for nombre, precio_texto, imagen in matches:
            try:
                precio_actual = self.limpiar_precio(precio_texto)
                if precio_actual:
                    item = {
                        'supermercado': 'ARA',
                        'nombre': nombre.strip(),
                        'marca': None,
                        'categoria': 'Productos ARA',
                        'presentacion': self.extraer_presentacion(nombre),
                        'precio_actual': precio_actual,
                        'precio_anterior': None,
                        'descuento_porcentaje': None,
                        'url': response.url,
                        'imagen_url': imagen if imagen else None,
                        'fecha_extraccion': datetime.utcnow().isoformat(),
                    }
                    yield item
                    productos_scraped += 1
            except Exception as e:
                self.logger.error(f'Error procesando producto: {e}')
                continue
        
        self.logger.info(f'Productos scrapeados en página {page}: {productos_scraped}')
        
        next_page = page + 1
        next_url = f'https://losprecios.co/ara_t2?p={next_page}'
        
        yield scrapy.Request(
            next_url,
            meta={
                'playwright': True,
                'playwright_page_methods': [
                    PageMethod('wait_for_timeout', 10000),
                    PageMethod('evaluate', 'window.scrollTo(0, document.body.scrollHeight)'),
                    PageMethod('wait_for_timeout', 3000),
                ],
                'page': next_page
            },
            callback=self.parse,
        )
    
    def limpiar_precio(self, precio_texto):
        """Limpia precio en formato Colombia (miles con punto, decimales con coma)"""
        if not precio_texto:
            return None
        try:
            precio_texto = precio_texto.strip()
            precio_texto = re.sub(r'[^\d.,]', '', precio_texto)
            
            if ',' in precio_texto:
                parts = precio_texto.rsplit(',', 1)
                if len(parts[1]) <= 2:
                    precio_texto = precio_texto.replace('.', '').replace(',', '.')
            
            precio_texto = precio_texto.replace('.', '')
            
            return float(precio_texto) if precio_texto else None
        except (ValueError, AttributeError):
            return None
    
    def extraer_presentacion(self, nombre):
        if not nombre:
            return None
        
        patrones = [
            r'(\d+(\.\d+)?)\s*(kg|kilogramo|kilogramos)',
            r'(\d+(\.\d+)?)\s*(g|gramo|gramos)',
            r'(\d+(\.\d+)?)\s*(l|lt|litro|litros)',
            r'(\d+(\.\d+)?)\s*(ml|mililitro|mililitros)',
            r'(\d+)\s*(unidades|unds|und|un)',
            r'(\d+(\.\d+)?)\s*(paquete|packs|pack)',
            r'(\d+(\.\d+)?)\s*(x\s*\d+)',
        ]
        
        nombre_lower = nombre.lower()
        for patron in patrones:
            match = re.search(patron, nombre_lower)
            if match:
                return match.group(0)
        
        return None
