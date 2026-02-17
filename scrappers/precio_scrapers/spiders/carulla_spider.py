# https://www.carulla.com/aseo-del-hogar
# scrapy runspider carulla_spider.py -o productos.json  esto es para correr el spider y guardar los productos en un archivo json
import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
import re
from urllib.parse import urlparse, urlunparse

# ============================================================================
# SELECTORES CORREGIDOS BASADOS EN EL HTML REAL DE CARULLA
# ============================================================================
# Carulla usa React con clases CSS modulares (hash aleatorio)
# 
# Contenedor de producto: article.productCard_productCard__M0677
# Nombre: h3.styles_name__qQJiK
# Precio: p.ProductPrice_container__price__XmMWA (dentro de div[data-fs-container-price-otros="true"])
# Imagen: a[data-testid="product-link"] img::attr(src)
# Link: a[data-testid="product-link"]::attr(href)
# Precio unitario: span.product-unit_price-unit__text__qeheS
# ============================================================================


class CarullaSpider(scrapy.Spider):
    name = "carulla"
    allowed_domains = ["www.carulla.com"]

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 4,
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
        },
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
    }

    # Selector principal para productos (usar clase más estable)
    PRODUCT_SELECTOR = 'article[class*="productCard"]'

    def start_requests(self):
        urls = [
            ('https://www.carulla.com/delicatessen', 'Delicatessen'), 
            ('https://www.carulla.com/delicatessen/quesos','Quesos'),
            ('https://www.carulla.com/delicatessen/carnes-maduradas','Carnes Maduradas'),
            ('https://www.carulla.com/delicatessen/encurtidos-pates-y-dulces','Encurtidos, Pates y Dulces'),
            ('https://www.carulla.com/aseo-del-hogar', 'Aseo del Hogar'),
            ('https://www.carulla.com/lacteos-huevos-y-refrigerados', 'Lacteos, Huevos y Refrigerados'),
            ('https://www.carulla.com/frutas-y-verduras', 'Frutas y Verduras'),
            ('https://www.carulla.com/confiteria', 'Confitería'),
            ('https://www.carulla.com/cuidado-personal', 'Cuidado Personal'),
            ('https://www.carulla.com/despensa', 'Despensa'),
            ('https://www.carulla.com/electrodomesticos', 'Electrodomesticos'),
            ('https://www.carulla.com/juguetes', 'Juguetes'),
            ('https://www.carulla.com/libros', 'Libros'),
            ('https://www.carulla.com/mascotas', 'Mascotas'),
            ('https://www.carulla.com/tecnologia', 'Tecnología'),
            ('https://www.carulla.com/viajes', 'Viajes'),
            ('https://www.carulla.com/vinos-y-licores', 'Vinos y Licores'),
            ('https://www.carulla.com/bebidas-snacks-y-dulces', 'Bebidas, Snacks y Dulces'),
            ('https://www.carulla.com/panaderia', 'Panadería'),
            ('https://www.carulla.com/congelados', 'Congelados'),
            ('https://www.carulla.com/salud-y-belleza', 'Salud y Belleza'),
            ('https://www.carulla.com/jugueteria', 'Jugueteria'),
            ('https://www.carulla.com/hogar-y-decoracion/mesa', 'Mesa'),
            ('https://www.carulla.com/hogar-y-decoracion','Hogar y Decoración'),
            ('https://www.carulla.com/papeleria','Papelería'),
            ('https://www.carulla.com/tecnologia-electrodomesticos-moda','Tecnología, Electrodomesticos y Moda'),
           
            
        ]

        for url, categoria in urls:
            yield scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        # Esperar carga inicial
                        PageMethod('wait_for_timeout', 3000),
                        
                        # Esperar que aparezcan productos
                        PageMethod('wait_for_selector', self.PRODUCT_SELECTOR, timeout=30000),
                        
                        # Scroll para lazy loading (3 veces)
                        PageMethod('evaluate', '''
                            async () => {
                                for(let i = 0; i < 3; i++) {
                                    window.scrollTo(0, document.body.scrollHeight);
                                    await new Promise(r => setTimeout(r, 2000));
                                }
                                window.scrollTo(0, 0);
                                await new Promise(r => setTimeout(r, 1000));
                            }
                        '''),
                    ],
                    'page': 1,  
                    'categoria': categoria
                },
                callback=self.parse,
                errback=self.error_handler
            )
    
    async def parse(self, response):
        page_num = response.meta.get('page', 1)
        categoria = response.meta.get('categoria', 'sin-categoria')
        playwright_page = response.meta.get('playwright_page')

        self.logger.info(f"📄 Procesando página {page_num}: {response.url}")

        # ============================================================================
        # SELECTORES CORREGIDOS
        # ============================================================================
        # Buscar productos usando el selector correcto
        productos = response.css('article[class*="productCard"]')
        
        self.logger.info(f"✅ Productos encontrados en página {page_num}: {len(productos)}")

        if len(productos) == 0:
            if page_num == 1:
                self.logger.warning('⚠️  No se encontraron productos en la primera página. Guardando HTML...')
                with open(f'carulla_debug_page{page_num}.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                self.logger.warning(f'📝 HTML guardado en carulla_debug_page{page_num}.html')
            else:
                self.logger.info(f"✓ No hay más productos en página {page_num}. Finalizando paginación.")
            
            # Cerrar la página de Playwright
            if playwright_page:
                await playwright_page.close()
            return

        productos_validos = 0

        for index, product in enumerate(productos, 1):
            try:
                # ============================================================================
                # NOMBRE - h3.styles_name__qQJiK
                # ============================================================================
                name = product.css('h3[class*="styles_name"]::text').get()
                if not name:
                    name = product.css('h3::text').get()
                
                # ============================================================================
                # PRECIO - p[data-fs-container-price-otros="true"]
                # El precio está en: <p class="ProductPrice_container__price__XmMWA">$ 7.970</p>
                # ============================================================================
                price = product.css('p[data-fs-container-price-otros="true"]::text').get()
                if not price:
                    # Fallback: buscar cualquier precio
                    price = product.css('p[class*="ProductPrice_container__price"]::text').get()
                
                # ============================================================================
                # PRECIO UNITARIO (opcional) - span.product-unit_price-unit__text__qeheS
                # Formato: "(Gr a $ 99,63)"
                # ============================================================================
                unit_price = product.css('span[class*="price-unit__text"]::text').get()
                
                # ============================================================================
                # IMAGEN - a[data-testid="product-link"] img::attr(src)
                # ============================================================================
                image = product.css('a[data-testid="product-link"] img::attr(src)').get()
                if not image:
                    image = product.css('img::attr(src)').get()
                
                # ============================================================================
                # LINK - a[data-testid="product-link"]::attr(href)
                # Formato: "/jamon-serrano-1901-80-gr-3010835/p"
                # ============================================================================
                product_link = product.css('a[data-testid="product-link"]::attr(href)').get()
                
                # ============================================================================
                # VENDEDOR (opcional) - span[data-fs-product-details-seller__name="true"]
                # ============================================================================
                seller = product.css('span[data-fs-product-details-seller__name="true"] + ::text').get()
                if seller:
                    seller = seller.strip()

                # Logging para debug
                self.logger.debug(f"  {index}. {name.strip() if name else 'Sin nombre'} - {price.strip() if price else 'Sin precio'}")

                if name and price:
                    precio_numerico = self.clean_price(price)
                    if precio_numerico:
                        item = {
                            'supermercado': 'Carulla',
                            'nombre': name.strip(),
                            'precio_actual': precio_numerico,
                            'precio_anterior': None,  # TODO: detectar si hay precio anterior
                            'descuento_porcentaje': None,  # TODO: calcular si hay descuento
                            'marca': None,  # No visible en el HTML proporcionado
                            'presentacion': unit_price.strip() if unit_price else None,
                            'url': response.urljoin(product_link) if product_link else response.url,
                            'imagen_url': image if image and image.startswith('http') else None,
                            'categoria': categoria,
                            'vendedor': seller if seller else 'Carulla',
                            'fecha_extraccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        }
                        productos_validos += 1
                        yield item
                else:
                    self.logger.warning(f"  ⚠️  Producto {index} sin nombre o precio: name={name}, price={price}")
                    
            except Exception as e:
                self.logger.error(f'❌ Error procesando producto {index}: {e}')
                continue

        self.logger.info(f"✅ Productos válidos extraídos en página {page_num}: {productos_validos}")
        
        # ============================================================================
        # PAGINACIÓN
        # ============================================================================
        # Carulla probablemente use scroll infinito o botón "Cargar más"
        # Buscar posibles selectores de paginación
        
        # Opción 1: Botón "siguiente" tradicional
        next_button = response.css('a[rel="next"]::attr(href)').get()
        if not next_button:
            next_button = response.css('a[class*="next"]::attr(href)').get()
        if not next_button:
            next_button = response.css('button[class*="next"]::attr(data-url)').get()
        
        if next_button:
            next_page_num = page_num + 1
            next_url = response.urljoin(next_button)
            
            self.logger.info(f"➡️  Navegando a página {next_page_num}: {next_url}")
            
            yield scrapy.Request(
                next_url,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_timeout', 3000),
                        PageMethod('wait_for_selector', self.PRODUCT_SELECTOR, timeout=30000),
                        PageMethod('evaluate', '''
                            async () => {
                                for(let i = 0; i < 3; i++) {
                                    window.scrollTo(0, document.body.scrollHeight);
                                    await new Promise(r => setTimeout(r, 2000));
                                }
                                window.scrollTo(0, 0);
                            }
                        '''),
                    ],
                    'page': next_page_num,
                    'categoria': categoria
                },
                callback=self.parse,
                errback=self.error_handler,
                dont_filter=True
            )
        else:
            self.logger.info(f"✓ Categoría '{categoria}' completada. Total páginas: {page_num}")
        
        # Cerrar la página de Playwright
        if playwright_page:
            await playwright_page.close()

    def clean_price(self, price_text):
        """
        Extrae el precio numérico - Formato Colombia: $ 7.970
        Los puntos son separadores de miles
        """
        if not price_text:
            return None

        try:
            price_text = price_text.strip()
            # Remover símbolo de pesos y espacios
            price_text = price_text.replace('$', '').replace(' ', '')
            
            # En Colombia, el punto es separador de miles, la coma es decimal
            # Ejemplo: $ 7.970 = 7970 pesos
            # Ejemplo: $ 1.234.567 = 1234567 pesos
            # Ejemplo: $ 1.234,50 = 1234.50 pesos
            
            if ',' in price_text:
                # Tiene coma decimal
                # Remover puntos (miles) y reemplazar coma por punto
                price_text = price_text.replace('.', '').replace(',', '.')
            else:
                # Solo puntos (son separadores de miles)
                price_text = price_text.replace('.', '')
            
            if price_text:
                return float(price_text)
            return None
        except (ValueError, AttributeError) as e:
            self.logger.error(f"Error limpiando precio '{price_text}': {e}")
            return None
    
    def error_handler(self, failure):
        self.logger.error(f"❌ ERROR: {failure.request.url}")
        self.logger.error(f"Tipo: {failure.type}")
        self.logger.error(f"Detalle: {failure.value}")