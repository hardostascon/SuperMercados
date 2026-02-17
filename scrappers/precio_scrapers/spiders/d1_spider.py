import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
import re

class D1Spider(scrapy.Spider):
    name = "d1"
    allowed_domains = ["tiendasd1.com", "domicilios.tiendasd1.com"]
    
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
            'https://domicilios.tiendasd1.com/ca/aseo%20hogar/ASEO%20HOGAR',
        ]
        
        for url in urls:
            yield scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_timeout', 8000),
                        PageMethod('evaluate', 'window.scrollTo(0, document.body.scrollHeight)'),
                        PageMethod('wait_for_timeout', 3000),
                    ],
                },
                callback=self.parse
            )
    
    def parse(self, response):
        self.logger.info(f'URL scrapeada: {response.url}')
        
        productos = response.css('[class*="product-card"]')
        if not productos:
            productos = response.css('[class*="productCard"]')
        if not productos:
            productos = response.css('[class*="item-product"]')
        if not productos:
            productos = response.css('.vtex-search-result-3-x-galleryItem')
        if not productos:
            productos = response.css('[data-testid*="product"]')
        
        self.logger.info(f'Productos encontrados: {len(productos)}')
        
        if not productos:
            self.logger.warning('No se encontraron productos. Guardando HTML para debug...')
            with open('d1_debug.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            self.logger.warning('HTML guardado en d1_debug.html')
            return
        
        for producto in productos:
            try:
                item = self.extraer_producto(producto, response)
                if item:
                    yield item
            except Exception as e:
                self.logger.error(f'Error extrayendo producto: {e}')
                continue
    
    def extraer_producto(self, producto, response):
        nombre = producto.css('[class*="name"]::text, [class*="Name"]::text, h3::text, h4::text').get()
        if not nombre:
            nombre = producto.css('[data-testid*="name"]::text').get()
        
        precio_texto = producto.css('[class*="price"]::text, [class*="Price"]::text, .value::text').get()
        if not precio_texto:
            precio_texto = producto.css('[data-testid*="price"]::text').get()
        
        if not nombre or not precio_texto:
            return None
        
        precio_actual = self.limpiar_precio(precio_texto)
        if not precio_actual:
            return None
        
        precio_anterior = None
        descuento_porcentaje = None
        
        precio_anterior_texto = producto.css('[class*="oldPrice"]::text, [class*="old-price"]::text').get()
        if precio_anterior_texto:
            precio_anterior = self.limpiar_precio(precio_anterior_texto)
            if precio_anterior and precio_actual < precio_anterior:
                descuento_porcentaje = round(((precio_anterior - precio_actual) / precio_anterior) * 100, 2)
        
        imagen = producto.css('img::attr(src), img::attr(data-src), img::attr(data-original)').get()
        url_producto = producto.css('a::attr(href)').get()
        
        marca = producto.css('[class*="brand"]::text, [class*="Brand"]::text').get()
        
        return {
            'supermercado': 'D1',
            'nombre': nombre.strip() if nombre else '',
            'marca': marca.strip() if marca else None,
            'categoria': 'Aseo Hogar',
            'presentacion': self.extraer_presentacion(nombre),
            'precio_actual': precio_actual,
            'precio_anterior': precio_anterior,
            'descuento_porcentaje': descuento_porcentaje,
            'url': response.urljoin(url_producto) if url_producto else response.url,
            'imagen_url': imagen,
            'fecha_extraccion': datetime.utcnow().isoformat(),
        }
    
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
            r'(\d+(\.\d+)?)\s*(rollo|rollos)',
            r'(\d+(\.\d+)?)\s*(x\s*\d+)',
        ]
        
        nombre_lower = nombre.lower()
        for patron in patrones:
            match = re.search(patron, nombre_lower)
            if match:
                return match.group(0)
        
        return None
