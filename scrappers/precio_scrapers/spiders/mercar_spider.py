# https://supermercadomercar.com/product-category/aseo-general/

# https://supermercadomercar.com/product-category/aseo-general/

import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
import re
from urllib.parse import urlparse, urlunparse

# Selectores Mercar (Elementor + WooCommerce):
# Productos: div[data-elementor-type="loop-item"] o div.e-loop-item.product
# Precio: span.woocommerce-Price-amount.amount
# Nombre: h2.elementor-heading-title (primer h2 del producto)
# Paginacion: WooCommerce usa /page/N/ en la URL (infinite scroll en frontend)


class MercarSpider(scrapy.Spider):
    name = "mercar"
    allowed_domains = ["supermercadomercar.com"]

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 4,
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
        }
    }

    # Selector para esperar a que carguen los productos
    PRODUCT_SELECTOR = 'div[data-elementor-type="loop-item"]'

    def start_requests(self):
        urls = [
            ('https://supermercadomercar.com/product-category/aseo-general/', 'Limpieza Hogar'),
            ('https://supermercadomercar.com/product-category/aseo-personal/', 'Aseo Personal'),
            ('https://supermercadomercar.com/product-category/cervezas-y-licores/', 'Bebidas con Alcohol'),
            ('https://supermercadomercar.com/product-category/confiteria/', 'Confitería'),
            ('https://supermercadomercar.com/product-category/cuidado-del-bebe/', 'Cuidado del Bebé'),
            ('https://supermercadomercar.com/product-category/cuidado-personal/', 'Cuidado Personal'),
            ('https://supermercadomercar.com/product-category/despensa/', 'Despensa'),
            ('https://supermercadomercar.com/product-category/frutas-y-verduras/', 'Frutas y Verduras'),
            ('https://supermercadomercar.com/product-category/lacteos-huevos-refrigerados/', 'Lácteos y Huevos Refrigerados'),
            ('https://supermercadomercar.com/product-category/pollo-carnes-pescado/', 'Pollo, Carnes y Pescado'),
        ]

        for url, categoria in urls:
            yield scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_timeout', 5000),
                        PageMethod('wait_for_selector', self.PRODUCT_SELECTOR, timeout=20000),
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

        # Mercar: div[data-elementor-type="loop-item"] o div.e-loop-item.product
        productos = response.css('div[data-elementor-type="loop-item"]')
        if not productos:
            productos = response.css('div.e-loop-item.product')

        self.logger.info(f"Productos encontrados en pagina {page}: {len(productos)}")

        if len(productos) == 0:
            if page == 1:
                self.logger.warning('No se encontraron productos en la primera pagina. Guardando HTML...')
                with open('mercar_debug.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                self.logger.warning('HTML guardado en mercar_debug.html')
            else:
                self.logger.info(f"No hay mas productos en pagina {page}. Finalizando paginacion.")
            return

        productos_validos = 0

        for index, product in enumerate(productos, 1):
            try:
                # Nombre: primer h2.elementor-heading-title del producto
                name = product.css('h2.elementor-heading-title::text').get()
                if not name:
                    name = product.css('div.elementor-element-22159c6 h2.elementor-heading-title::text').get()

                # Precio: span.woocommerce-Price-amount.amount (formato: $16,990)
                price_parts = product.css('span.woocommerce-Price-amount.amount *::text').getall()
                price = ''.join(price_parts).strip() if price_parts else None
                if not price:
                    price = product.css('span.woocommerce-Price-amount.amount::text').get()

                image = product.css('img::attr(src)').get()
                if not image:
                    image = product.css('img::attr(data-src)').get()

                product_link = product.css('a[href*="/product/"]::attr(href)').get()
                if not product_link:
                    product_link = product.css('a::attr(href)').get()

                self.logger.info(f"  {index}. {name.strip() if name else 'Sin nombre'} - {price.strip() if price else 'Sin precio'}")

                if name and price:
                    precio_numerico = self.clean_price(price)
                    if precio_numerico:
                        item = {
                            'supermercado': 'Mercar',
                            'nombre': name.strip(),
                            'precio_actual': precio_numerico,
                            'precio_anterior': None,
                            'descuento_porcentaje': None,
                            'marca': None,
                            'presentacion': None,
                            'url': response.urljoin(product_link) if product_link else response.url,
                            'imagen_url': response.urljoin(image) if image else None,
                            'categoria': categoria,
                            'fecha_extraccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        }
                        productos_validos += 1
                        yield item
            except Exception as e:
                self.logger.error(f'Error procesando producto {index}: {e}')
                continue

        self.logger.info(f"Productos validos extraidos en pagina {page}: {productos_validos}")
        
        # CAMBIO CRÍTICO: Verificar si existe botón "siguiente" en el DOM
        next_button = response.css('a.next.page-numbers::attr(href)').get()
        
        if next_button:
            next_page = page + 1
            next_url = response.urljoin(next_button)
            
            self.logger.info(f"Boton 'siguiente' encontrado. Navegando a pagina {next_page}: {next_url}")
            
            yield scrapy.Request(
                next_url,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_timeout', 5000),
                        PageMethod('wait_for_selector', self.PRODUCT_SELECTOR, timeout=20000),
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
            self.logger.info(f"✓ Categoria '{categoria}' completada. Total paginas: {page}")

    def _build_page_url(self, base_url, page_num):
        """Construye URL de paginacion WooCommerce: /page/N/"""
        if page_num <= 1:
            return base_url.rstrip('/')
        parsed = urlparse(base_url)
        path = parsed.path.rstrip('/')
        # Quitar /page/X/ existente si hay
        path = re.sub(r'/page/\d+/?$', '', path)
        new_path = f"{path}/page/{page_num}/"
        return urlunparse(parsed._replace(path=new_path))
    
    def clean_price(self, price_text):
        """Extrae el precio numerico - Formato Colombia: $16,990 (miles) o $1,99 (decimal)"""
        if not price_text:
            return None

        try:
            price_text = price_text.strip()
            price_text = re.sub(r'[^\d.,]', '', price_text)

            if ',' in price_text:
                parts = price_text.rsplit(',', 1)
                if len(parts[1]) <= 2:
                    # Decimal: 1,99 -> 1.99 (no tocar puntos despues)
                    price_text = price_text.replace('.', '').replace(',', '.')
                else:
                    # Miles: 16,990 -> 16990
                    price_text = price_text.replace(',', '').replace('.', '')
            else:
                # Sin coma: puntos son miles (1.500 -> 1500)
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