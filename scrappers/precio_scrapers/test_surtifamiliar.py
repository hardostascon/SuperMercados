import scrapy
from scrapy.http import HtmlResponse

# Leer el HTML guardado
with open('surtifamiliar_page.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Crear un objeto response de Scrapy
response = HtmlResponse(
    url='https://surtifamiliar.com',
    body=html_content.encode('utf-8'),
    encoding='utf-8'
)

print("=" * 60)
print("ANÁLISIS DE SELECTORES")
print("=" * 60)

# 1. Buscar posibles contenedores de productos
selectors_to_test = [
    'article',
    '[class*="product"]',
    '[class*="Product"]',
    '[class*="card"]',
    '[class*="item"]',
    '[data-product]',
    '.product-card',
    '.card-product',
]

print("\n1. CONTENEDORES DE PRODUCTOS:")
for selector in selectors_to_test:
    elements = response.css(selector)
    if len(elements) > 0:
        print(f"✅ {selector:30} → {len(elements)} elementos")
        # Mostrar clases del primer elemento
        first_class = elements[0].attrib.get('class', 'sin clase')
        print(f"   Primera clase encontrada: {first_class}")
    else:
        print(f"❌ {selector:30} → 0 elementos")

# 2. Buscar títulos/nombres
print("\n2. NOMBRES DE PRODUCTOS:")
title_selectors = [
    'h1', 'h2', 'h3', 'h4',
    '[class*="title"]',
    '[class*="name"]',
    '[class*="Title"]',
    '[class*="Name"]',
]

for selector in title_selectors:
    elements = response.css(selector)
    if len(elements) > 0:
        first_text = elements[0].css('::text').get()
        print(f"✅ {selector:30} → {len(elements)} elementos")
        print(f"   Ejemplo: {first_text[:50] if first_text else 'vacío'}...")

# 3. Buscar precios
print("\n3. PRECIOS:")
price_selectors = [
    '[class*="price"]',
    '[class*="Price"]',
    '[class*="valor"]',
    'span[class*="price"]',
    'div[class*="price"]',
]

for selector in price_selectors:
    elements = response.css(selector)
    if len(elements) > 0:
        first_text = elements[0].css('::text').get()
        print(f"✅ {selector:30} → {len(elements)} elementos")
        print(f"   Ejemplo: {first_text[:30] if first_text else 'vacío'}...")

# 4. Buscar imágenes
print("\n4. IMÁGENES:")
images = response.css('img')
print(f"Total de imágenes: {len(images)}")
if len(images) > 0:
    for i, img in enumerate(images[:3]):  # Primeras 3
        src = img.attrib.get('src', img.attrib.get('data-src', 'sin src'))
        alt = img.attrib.get('alt', 'sin alt')
        print(f"  {i+1}. src: {src[:60]}...")
        print(f"     alt: {alt[:60]}")

# 5. Buscar links
print("\n5. LINKS DE PRODUCTOS:")
links = response.css('a[href*="product"], a[href*="producto"]')
print(f"Links con 'product/producto': {len(links)}")
if len(links) > 0:
    for i, link in enumerate(links[:3]):
        href = link.attrib.get('href', '')
        print(f"  {i+1}. {href}")

print("\n" + "=" * 60)