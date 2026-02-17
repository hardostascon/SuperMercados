import scrapy
from scrapy_playwright.page import PageMethod

#scrapy runspider test_carulla_fixed.py   esto es para correr el spider
class CarullaAnalyzerSpider(scrapy.Spider):
    """
    Spider para identificar los selectores CSS de Carulla/Mercar
    """
    name = 'mercar_analyzer'
    
    custom_settings = {
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': False,  # Ver el navegador en acción
        },
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
    }
    
    def start_requests(self):
        url = 'https://www.carulla.com/delicatessen'
        
        yield scrapy.Request(
            url,
            meta={
                'playwright': True,
                'playwright_include_page': True,
                'playwright_page_methods': [
                    # Esperar carga inicial
                    PageMethod('wait_for_timeout', 3000),
                    
                    # Scroll para activar lazy loading
                    PageMethod('evaluate', '''
                        async () => {
                            for(let i = 0; i < 3; i++) {
                                window.scrollTo(0, document.body.scrollHeight);
                                await new Promise(r => setTimeout(r, 1500));
                            }
                            window.scrollTo(0, 0);
                        }
                    '''),
                    
                    # Espera final
                    PageMethod('wait_for_timeout', 2000),
                    
                    # Screenshot para inspección visual
                    PageMethod('screenshot', path='mercar_page.png', full_page=True),
                ],
            },
            callback=self.analyze_page,
            errback=self.error_handler
        )
    
    async def analyze_page(self, response):
        page = response.meta.get('playwright_page')
        
        try:
            print("\n" + "="*80)
            print("ANÁLISIS DE SELECTORES - MERCAR")
            print("="*80)
            
            # Guardar HTML completo
            with open('carulla_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("\n✅ HTML guardado en: carulla_page.html")
            print("✅ Screenshot guardado en: mercar_page.png")
            
            # 1. BUSCAR CONTENEDORES DE PRODUCTOS
            print("\n" + "-"*80)
            print("1. CONTENEDORES DE PRODUCTOS")
            print("-"*80)
            
            product_selectors = [
                'article',
                'li.product',
                '.product',
                '[class*="product"]',
                '.type-product',
                'div.product-small',
                'div[class*="product-small"]',
                '.product-item',
                'ul.products > li',
                '[data-testid*="product"]',
                '[class*="Product"]',
                '[class*="item"]',
            ]
            
            products = []
            for selector in product_selectors:
                elements = response.css(selector)
                print(f"{selector:40} → {len(elements)} elementos")
                if len(elements) > 0 and not products:
                    products = elements
                    print(f"  ✅ SELECTOR ENCONTRADO: {selector}")
                    # Mostrar clases del primer elemento
                    first_classes = elements[0].attrib.get('class', '')
                    print(f"  📌 Clases: {first_classes}")
            
            if not products:
                print("  ❌ No se encontraron productos")
                print("\n⚠️  Guardando HTML completo para inspección manual...")
                return
            
            # 2. ANALIZAR ESTRUCTURA DE UN PRODUCTO
            print("\n" + "-"*80)
            print("2. ESTRUCTURA DEL PRIMER PRODUCTO")
            print("-"*80)
            
            first_product = products[0]
            
            # Nombre/Título
            print("\nNOMBRE DEL PRODUCTO:")
            title_selectors = [
                'h2::text', 'h3::text', 'h4::text',
                '.product-title::text',
                '[class*="title"]::text',
                'a.woocommerce-loop-product__title::text',
                '.woocommerce-loop-product__title::text',
                '[class*="name"]::text',
                '[class*="Name"]::text',
            ]
            for selector in title_selectors:
                text = first_product.css(selector).get()
                if text:
                    print(f"  ✅ {selector:50} → {text.strip()[:60]}")
            
            # Precio
            print("\nPRECIO:")
            price_selectors = [
                '.price::text',
                'span.price::text',
                '[class*="price"]::text',
                '[class*="Price"]::text',
                '.amount::text',
                'bdi::text',
                '.woocommerce-Price-amount::text',
            ]
            for selector in price_selectors:
                text = first_product.css(selector).get()
                if text:
                    print(f"  ✅ {selector:50} → {text.strip()}")
            
            # Imagen
            print("\nIMAGEN:")
            image_selectors = [
                'img::attr(src)',
                'img::attr(data-src)',
                'img::attr(data-lazy-src)',
                '.attachment-woocommerce_thumbnail::attr(src)',
                'img::attr(srcset)',
            ]
            for selector in image_selectors:
                img = first_product.css(selector).get()
                if img and not img.startswith('data:'):
                    print(f"  ✅ {selector:50} → {img[:80]}...")
            
            # Link
            print("\nENLACE:")
            link_selectors = [
                'a::attr(href)',
                '.product-link::attr(href)',
                '.woocommerce-LoopProduct-link::attr(href)',
            ]
            for selector in link_selectors:
                link = first_product.css(selector).get()
                if link:
                    print(f"  ✅ {selector:50} → {link[:80]}...")
            
            # SKU o ID
            print("\nSKU / ID:")
            sku_selectors = [
                '::attr(data-product-id)',
                '::attr(data-product_id)',
                '::attr(id)',
                '::attr(data-id)',
            ]
            for selector in sku_selectors:
                sku = first_product.css(selector).get()
                if sku:
                    print(f"  ✅ {selector:50} → {sku}")
            
            # 3. MOSTRAR HTML DEL PRIMER PRODUCTO
            print("\n" + "-"*80)
            print("3. HTML DEL PRIMER PRODUCTO (primeros 500 caracteres)")
            print("-"*80)
            product_html = first_product.get()
            print(product_html[:500])
            
            # Guardar HTML del primer producto completo
            with open('first_product.html', 'w', encoding='utf-8') as f:
                f.write(product_html)
            print("\n✅ HTML del primer producto guardado en: first_product.html")
            
            # 4. CONTAR TODOS LOS PRODUCTOS
            print("\n" + "-"*80)
            print("4. RESUMEN")
            print("-"*80)
            print(f"Total de productos encontrados: {len(products)}")
            
            # 5. BUSCAR PAGINACIÓN
            print("\n" + "-"*80)
            print("5. PAGINACIÓN")
            print("-"*80)
            
            pagination_selectors = [
                '.next.page-numbers::attr(href)',
                'a.next::attr(href)',
                '.pagination a.next::attr(href)',
                'a[rel="next"]::attr(href)',
                '[class*="next"]::attr(href)',
                '[class*="Next"]::attr(href)',
            ]
            
            for selector in pagination_selectors:
                next_page = response.css(selector).get()
                if next_page:
                    print(f"  ✅ {selector:50} → {next_page}")
            
            print("\n" + "="*80)
            print("ANÁLISIS COMPLETADO")
            print("="*80)
            print("\nArchivos generados:")
            print("  - carulla_page.html (página completa)")
            print("  - first_product.html (primer producto)")
            print("  - mercar_page.png (screenshot)")
            print("\nRevisa estos archivos para confirmar los selectores encontrados.")
            print("="*80 + "\n")
            
        finally:
            # Asegurar que se cierre la página
            if page:
                await page.close()
    
    def error_handler(self, failure):
        print(f"\n❌ ERROR: {failure.request.url}")
        print(f"Tipo: {failure.type}")
        print(f"Detalle: {failure.value}")