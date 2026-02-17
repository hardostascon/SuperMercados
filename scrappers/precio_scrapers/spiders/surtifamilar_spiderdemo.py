import scrapy
from scrapy_playwright.page import PageMethod
import json


class SurtifamiliarSpider(scrapy.Spider):
    name = 'surtifamiliarscanner'
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2,
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': False,  # Cambia a True en producción
        },
    }
    
    def start_requests(self):
        urls = [
            'https://surtifamiliar.com/limpieza-hogar-limpiadores-516/products?pageNumber=1&productLowPrice=0&productHighPrice=0&sort=1&attributes=%5B%5D'
        ]
        
        for url in urls:
            yield scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        # Esperar a que cargue la aplicación
                        PageMethod('wait_for_timeout', 3000),
                        
                        # Esperar al contenedor de productos
                        PageMethod('wait_for_selector', '.product-card, .card-product, [class*="product"], article', timeout=20000),
                        
                        # Scroll para cargar lazy loading
                        PageMethod('evaluate', '''
                            async () => {
                                for(let i = 0; i < 3; i++) {
                                    window.scrollTo(0, document.body.scrollHeight);
                                    await new Promise(r => setTimeout(r, 1500));
                                }
                            }
                        '''),
                        
                        # Espera final
                        PageMethod('wait_for_timeout', 2000),
                        
                        # Screenshot para debug
                        PageMethod('screenshot', path='surtifamiliar_debug.png', full_page=True),
                    ],
                },
                callback=self.parse,
                errback=self.error_handler
            )
    
    async def parse(self, response):
        page = response.meta.get('playwright_page')
        
        self.logger.info(f"✅ Procesando: {response.url}")
        
        # Guardar HTML para inspección
        with open('surtifamiliar_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # SELECTORES COMUNES A PROBAR (ajusta según lo que veas en el HTML guardado)
        selectors_to_try = [
            '.product-card',
            '.card-product',
            'article.product',
            '[class*="ProductCard"]',
            '[class*="product-item"]',
            '.product-list > div',
            '[data-product-id]',
        ]
        
        products = []
        for selector in selectors_to_try:
            products = response.css(selector)
            if len(products) > 0:
                self.logger.info(f"✅ Selector encontrado: '{selector}' - {len(products)} productos")
                break
        
        if len(products) == 0:
            self.logger.error("❌ No se encontraron productos con ningún selector")
            if page:
                await page.close()
            return
        
        # EXTRAER DATOS DE CADA PRODUCTO
        for product in products:
            # Prueba estos selectores y ajusta según tu HTML
            item = {
                # Nombre del producto - prueba estos:
                'name': (
                    product.css('.product-name::text').get() or
                    product.css('h2::text').get() or
                    product.css('h3::text').get() or
                    product.css('[class*="title"]::text').get() or
                    product.css('a::attr(title)').get()
                ),
                
                # Precio - prueba estos:
                'price': (
                    product.css('.price::text').get() or
                    product.css('[class*="price"]::text').get() or
                    product.css('.product-price::text').get() or
                    product.css('span[class*="Price"]::text').get()
                ),
                
                # Precio anterior (si está en oferta)
                'old_price': (
                    product.css('.old-price::text').get() or
                    product.css('[class*="old-price"]::text').get() or
                    product.css('.price-before::text').get()
                ),
                
                # Imagen
                'image': (
                    product.css('img::attr(src)').get() or
                    product.css('img::attr(data-src)').get() or
                    product.css('[class*="image"] img::attr(src)').get()
                ),
                
                # SKU o ID del producto
                'sku': (
                    product.css('[data-product-id]::attr(data-product-id)').get() or
                    product.css('[data-sku]::attr(data-sku)').get()
                ),
                
                # Link del producto
                'url': (
                    product.css('a::attr(href)').get()
                ),
                
                # Disponibilidad
                'available': (
                    product.css('.in-stock::text').get() or
                    product.css('[class*="stock"]::text').get()
                ),
            }
            
            # Limpiar datos
            if item['price']:
                item['price'] = item['price'].strip()
            if item['name']:
                item['name'] = item['name'].strip()
            if item['url'] and not item['url'].startswith('http'):
                item['url'] = response.urljoin(item['url'])
            
            self.logger.info(f"📦 Producto: {item['name']} - ${item['price']}")
            yield item
        
        # Cerrar página de Playwright
        if page:
            await page.close()
    
    def error_handler(self, failure):
        self.logger.error(f"❌ ERROR: {failure.request.url}")
        self.logger.error(f"Tipo: {failure.type}")
        self.logger.error(f"Detalle: {failure.value}")
        
        page = failure.request.meta.get('playwright_page')
        if page:
            import asyncio
            asyncio.create_task(page.close())