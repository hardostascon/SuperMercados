import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

class ExitoSpider(scrapy.Spider):
    name = "exito"
    allowed_domains = ["exito.com"]
    
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
            ('https://www.exito.com/mercado/frutas-y-verduras/verduras-y-hortalizas', 'Verduras y Hortalizas'),
            ('https://www.exito.com/mercado/despensa', 'Despensa'),
            ('https://www.exito.com/mercado/aseo-del-hogar?page=1', 'Aseo del Hogar'),
        ]
        
        for url, categoria in urls:
            yield scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_timeout', 8000),
                        PageMethod('evaluate', 'window.scrollTo(0, document.body.scrollHeight)'),
                        PageMethod('wait_for_timeout', 3000),
                    ],
                    'categoria': categoria,
                    'page': 1
                },
                callback=self.parse
            )
    
    def parse(self, response):
        page = response.meta.get('page', 1)
        categoria = response.meta.get('categoria', 'General')
        self.logger.info(f'URL scrapeada: {response.url} (Página {page}, Categoría: {categoria})')
        
        productos = response.css('.vtex-search-result-3-x-galleryItem')
        if not productos:
            productos = response.css('[class*="galleryItem"]')
        if not productos:
            productos = response.css('.product-item')
        if not productos:
            productos = response.css('[class*="productCard"]')
        if not productos:
            productos = response.css('[class*="product-item"]')
        
        self.logger.info(f'Productos encontrados: {len(productos)}')
        
        if not productos and page == 1:
            self.logger.warning('No se encontraron productos. Guardando HTML para debug...')
            with open('exito_debug.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            self.logger.warning('HTML guardado en exito_debug.html')
            return
        
        productos_scraped = 0
        for producto in productos:
            try:
                item = self.extraer_producto(producto, response, categoria)
                if item:
                    yield item
                    productos_scraped += 1
            except Exception as e:
                self.logger.error(f'Error extrayendo producto: {e}')
                continue
        
        self.logger.info(f'Productos scrapeados: {productos_scraped}')
        
        if productos_scraped == 0:
            self.logger.info(f'No hay más productos en página {page}. Deteniendo paginación.')
            return
        
        next_page = page + 1
        next_url = self._increment_page(response.url, next_page)
        
        yield scrapy.Request(
            next_url,
            meta={
                'playwright': True,
                'playwright_page_methods': [
                    PageMethod('wait_for_timeout', 8000),
                    PageMethod('evaluate', 'window.scrollTo(0, document.body.scrollHeight)'),
                    PageMethod('wait_for_timeout', 3000),
                ],
                'categoria': categoria,
                'page': next_page
            },
            callback=self.parse
        )
    
    def _increment_page(self, url, next_page):
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        query_params['page'] = [str(next_page)]
        new_query = urlencode(query_params, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
    
    def extraer_producto(self, producto, response, categoria):
        nombre = producto.css('[class*="productName"]::text, [class*="product-name"]::text, .name::text, h3::text, h4::text').get()
        if not nombre:
            nombre = producto.css('[data-testid="product-name"]::text').get()
        
        precio_texto = producto.css('[class*="price"]::text, [class*="Price"]::text, .value::text, .price-current::text').get()
        if not precio_texto:
            precio_texto = producto.css('[data-testid="product-price"]::text').get()
        
        if not nombre or not precio_texto:
            return None
        
        precio_actual = self.limpiar_precio(precio_texto)
        if not precio_actual:
            return None
        
        precio_anterior = None
        descuento_porcentaje = None
        
        precio_anterior_texto = producto.css('[class*="oldPrice"]::text, [class*="old-price"]::text, .price-before::text').get()
        if precio_anterior_texto:
            precio_anterior = self.limpiar_precio(precio_anterior_texto)
            if precio_anterior and precio_actual < precio_anterior:
                descuento_porcentaje = round(((precio_anterior - precio_actual) / precio_anterior) * 100, 2)
        
        imagen = producto.css('img::attr(src), img::attr(data-src), img::attr(data-original)').get()
        url_producto = producto.css('a::attr(href)').get()
        
        marca = producto.css('[class*="brand"]::text, [class*="Brand"]::text').get()
        
        return {
            'supermercado': 'Exito',
            'nombre': nombre.strip() if nombre else '',
            'marca': marca.strip() if marca else None,
            'categoria': categoria,
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
        ]
        
        nombre_lower = nombre.lower()
        for patron in patrones:
            match = re.search(patron, nombre_lower)
            if match:
                return match.group(0)
        
        return None
