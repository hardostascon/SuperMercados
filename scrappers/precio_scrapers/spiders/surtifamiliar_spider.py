import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

class SurtifamiliarSpider(scrapy.Spider):
    name = "surtifamiliar"
    allowed_domains = ["surtifamiliar.com"]
    
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
            ('https://surtifamiliar.com/limpieza-hogar-limpiadores-516/products', 'Limpieza Hogar'),
            ('https://surtifamiliar.com/verduras/products', 'Verduras'),
            ('https://surtifamiliar.com/frutas-a-granel/products', 'Frutas a Granel'),
            ('https://surtifamiliar.com/pollo/products', 'Pollo'),
            ('https://surtifamiliar.com/carne-de-res/products', 'Carne de Res'),
            ('https://surtifamiliar.com/carne-de-cerdo/products', 'Carne de Cerdo'),
            ('https://surtifamiliar.com/carnes-salsamentaria-545/products', 'Carnes y Salsamentaria'),
            
        ]
        
        for url, categoria in urls:
            yield scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_timeout', 5000),
                        PageMethod('wait_for_selector', '.box-product', timeout=20000),
                        PageMethod('evaluate', 'window.scrollTo(0, document.body.scrollHeight)'),
                        PageMethod('wait_for_timeout', 3000)
                    ],
                    'pageNumber': 1,
                    'categoria': categoria
                },
                callback=self.parse
            )
    
    def parse(self, response):
        page = response.meta.get('pageNumber', 1)
        categoria = response.meta.get('categoria', 'sin-categoria')
        
        self.logger.info(f"Procesando pagina {page}: {response.url}")
        
        productos_contenedor = response.css('.box-product')
        
        if productos_contenedor:
            productos = productos_contenedor[0].css('.box-product-item')
        else:
            productos = response.css('[class*="product-item"]')
        
        self.logger.info(f"Productos encontrados en pagina {page}: {len(productos)}")
        
        if len(productos) == 0:
            if page == 1:
                self.logger.warning('No se encontraron productos en la primera pagina. Guardando HTML...')
                with open('surtifamiliar_debug.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                self.logger.warning('HTML guardado en surtifamiliar_debug.html')
            else:
                self.logger.info(f"No hay mas productos en pagina {page}. Finalizando paginacion.")
            return
        
        productos_validos = 0
        
        for index, product in enumerate(productos, 1):
            try:
                name = product.css('[class*="name"]::text').get()
                if not name:
                    name = product.css('h4::text').get()
                
                price = product.css('span[class*="price"]::text').get()
                if not price:
                    price = product.css('[class*="price"]::text').get()
                
                image = product.css('img::attr(src)').get()
                if not image:
                    image = product.css('img::attr(data-src)').get()
                
                product_link = product.css('a::attr(href)').get()
                
                self.logger.info(f"  {index}. {name.strip() if name else 'Sin nombre'} - {price.strip() if price else 'Sin precio'}")
                
                if name and price:
                    precio_numerico = self.clean_price(price)
                    if precio_numerico:
                        item = {
                            'supermercado': 'Surtifamiliar',
                            'nombre': name.strip(),
                            'precio_texto': price.strip(),
                            'precio_actual': precio_numerico,
                            'imagen': response.urljoin(image) if image else None,
                            'url': response.urljoin(product_link) if product_link else response.url,
                            'categoria': categoria,
                            'fecha_extraccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        }
                        productos_validos += 1
                        yield item
            except Exception as e:
                self.logger.error(f'Error procesando producto {index}: {e}')
                continue
        
        self.logger.info(f"Productos validos extraidos en pagina {page}: {productos_validos}")
        
        if productos_validos > 0:
            next_page = page + 1
            next_url = self._increment_page(response.url, next_page)
            
            self.logger.info(f"Solicitando siguiente pagina: {next_page}")
            
            yield scrapy.Request(
                next_url,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_timeout', 5000),
                        PageMethod('wait_for_selector', '.box-product', timeout=20000),
                        PageMethod('evaluate', 'window.scrollTo(0, document.body.scrollHeight)'),
                        PageMethod('wait_for_timeout', 3000),
                    ],
                    'pageNumber': next_page,
                    'categoria': categoria
                },
                callback=self.parse,
                errback=self.error_handler,
                dont_filter=True
            )
        else:
            self.logger.info(f"Scraping completado. Ultima pagina: {page}")
    
    def _increment_page(self, url, next_page):
        """Incrementa el numero de pagina en la URL"""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        query_params['pageNumber'] = [str(next_page)]
        new_query = urlencode(query_params, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
    
    def clean_price(self, price_text):
        """Extrae el precio numerico del texto - Formato Colombia"""
        if not price_text:
            return None
        
        try:
            price_text = price_text.strip()
            price_text = re.sub(r'[^\d.,]', '', price_text)
            
            if ',' in price_text:
                parts = price_text.rsplit(',', 1)
                if len(parts[1]) <= 2:
                    price_text = price_text.replace('.', '').replace(',', '.')
            
            price_text = price_text.replace('.', '')
            
            if price_text:
                return float(price_text)
            return None
        except (ValueError, AttributeError):
            return None
    
    def error_handler(self, failure):
        self.logger.error(f"ERROR: {failure.request.url}")
        self.logger.error(f"Tipo: {failure.type}")
        self.logger.error(f"Detalle: {failure.value}")
