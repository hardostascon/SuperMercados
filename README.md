# 🛒 SuperMercados — Price Scraper

> Sistema automatizado de scraping, procesamiento y análisis de precios de supermercados colombianos.

---

## 📋 Descripción

**SuperMercados** es una plataforma de extracción y análisis de precios que permite rastrear, comparar y almacenar los precios de productos de múltiples cadenas de supermercados en Colombia. El sistema utiliza **Scrapy** para el scraping, **Celery** para la orquestación de tareas asíncronas y **Docker** para el despliegue del entorno.

Los supermercados actualmente soportados incluyen:

- 🏪 Carulla
- 🏪 Mercar
- 🏪 Surtifamiliar
- 🏪 Ara
- 🏪 Canaveral
- 🏪 Éxito

---

## 🏗️ Arquitectura del Proyecto

```
SuperMercados/
├── app/                        # API REST con FastAPI
│   ├── routers/                # Endpoints organizados por dominio
│   ├── models/                 # Modelos Pydantic / ORM
│   ├── database.py             # Conexión a base de datos
│   └── main.py                 # Instancia FastAPI y registro de routers
├── Depurador_datos/            # Módulo de limpieza y normalización de datos
│   ├── config/
│   └── src/
├── scrappers/                  # Módulo de scraping (Scrapy)
│   ├── precio_scrapers/        # Proyecto Scrapy principal
│   │   ├── spiders/            # Spiders por supermercado
│   │   ├── middlewares.py
│   │   ├── pipelines.py
│   │   └── settings.py
│   └── workers/                # Tareas asíncronas con Celery
│       ├── celery_app.py
│       └── tasks.py
├── tests/                      # Suite de pruebas
├── Dockerfile
├── docker-compose.yml
├── main.py
└── requirements.txt
```

---

## ⚙️ Tecnologías Utilizadas

| Tecnología | Uso |
|---|---|
| **Python 3.x** | Lenguaje principal |
| **Scrapy** | Framework de scraping |
| **FastAPI** | API REST para consulta de precios y gestión de scrapers |
| **Celery** | Orquestación de tareas asíncronas |
| **Docker / Docker Compose** | Contenedorización del entorno |
| **pytest** | Framework de pruebas |

---

## 🚀 Instalación y Configuración

### Prerrequisitos

- Python 3.9+
- Docker y Docker Compose
- Redis (broker para Celery)

### 1. Clonar el repositorio

```bash
git clone https://github.com/hardostascon/SuperMercados.git
cd SuperMercados
```

### 2. Configurar variables de entorno

Copia el archivo `.env` de ejemplo y configura tus variables:

```bash
cp .env .env.local
```

Edita el archivo `.env` con tus credenciales de base de datos y configuración de broker.

### 3. Opción A — Instalación con Docker (recomendado)

```bash
docker-compose up --build
```

### 3. Opción B — Instalación local

```bash
# Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

---

## 🕷️ Uso del Scraper

### Ejecutar un spider específico

```bash
cd scrappers
scrapy crawl carulla_spider
scrapy crawl mercar_spider
scrapy crawl surtifamiliar_spider
```

### Ejecutar el sistema completo vía main

```bash
python main.py
```

### Ejecutar con Celery (modo asíncrono)

```bash
# Iniciar el worker de Celery
celery -A workers.celery_app worker --loglevel=info

# Disparar tareas
python -c "from workers.tasks import run_scrapers; run_scrapers.delay()"
```

---

## 🧪 Pruebas

```bash
pytest
```

Para ejecutar un módulo de pruebas específico:

```bash
pytest tests/test_carulla.py
pytest tests/test_mercar.py
pytest tests/test_db.py
pytest tests/test_surtifamiliar.py
```

---

## 🔄 Pipeline de Datos

El flujo de datos del sistema sigue estos pasos:

```
Spider (scraping) → Pipeline (validación) → Depurador_datos (limpieza) → Base de datos ← FastAPI (consulta)
                                                                                          ↑
                                                                                    Celery (tareas)
```

1. **Scraping:** Los spiders extraen los datos de precios de cada supermercado.
2. **Validación:** El pipeline de Scrapy filtra y valida los ítems extraídos.
3. **Limpieza:** El módulo `Depurador_datos` normaliza los datos (unidades, nombres, precios).
4. **Almacenamiento:** Los datos procesados se persisten en la base de datos o se exportan a JSON.

---

## 🌐 API REST con FastAPI

El módulo `app/` expone una API REST construida con **FastAPI** que permite consultar los precios scrapeados y disparar scrapers bajo demanda.

### Levantar la API

```bash
# Modo desarrollo (con auto-reload)
uvicorn app.main:app --reload --port 8000

# Modo producción
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Documentación interactiva

Una vez levantada la API, FastAPI genera automáticamente la documentación en:

| Interfaz | URL |
|---|---|
| **Swagger UI** | `http://localhost:8000/docs` |
| **ReDoc** | `http://localhost:8000/redoc` |

### Endpoints principales

#### 📦 Precios

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/productos` | Lista todos los productos con sus precios |
| `GET` | `/productos/{id}` | Consulta un producto específico |
| `GET` | `/productos?supermercado=carulla` | Filtra productos por supermercado |
| `GET` | `/productos?nombre=leche` | Busca productos por nombre |

#### 🕷️ Scrapers

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/scrapers/run` | Dispara todos los scrapers |
| `POST` | `/scrapers/run/{supermercado}` | Dispara el scraper de un supermercado |
| `GET` | `/scrapers/status` | Consulta el estado de los scrapers en ejecución |

#### 🔐 Autenticación

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/auth/login` | Obtiene un token JWT |
| `POST` | `/auth/refresh` | Renueva el token JWT |

> Los endpoints de scrapers y gestión requieren autenticación mediante **Bearer Token JWT** en el header `Authorization`.

### Ejemplo de uso

```bash
# Obtener token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "tu_password"}'

# Consultar precios de leche
curl http://localhost:8000/productos?nombre=leche \
  -H "Authorization: Bearer <tu_token>"

# Disparar scraper de Carulla
curl -X POST http://localhost:8000/scrapers/run/carulla \
  -H "Authorization: Bearer <tu_token>"
```

---

## 🐳 Docker

El proyecto incluye un `Dockerfile` y `docker-compose.yml` para levantar todos los servicios necesarios:

```bash
# Construir y levantar todos los servicios
docker-compose up --build

# Ejecutar en segundo plano
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down
```

---

## 📁 Variables de Entorno

El archivo `.env` debe contener las siguientes variables (ajusta los valores según tu entorno):

```env
# Base de datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=supermercados
DB_USER=your_user
DB_PASSWORD=your_password

# Celery / Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

> ⚠️ **Nunca subas el archivo `.env` con credenciales reales al repositorio.**

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor sigue estos pasos:

1. Haz un fork del repositorio
2. Crea una rama para tu feature: `git checkout -b feature/nombre-feature`
3. Realiza tus cambios y haz commit: `git commit -m "feat: descripción del cambio"`
4. Sube tu rama: `git push origin feature/nombre-feature`
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.

---

## 👤 Autor

**Hardostascon**  
[GitHub](https://github.com/hardostascon)
