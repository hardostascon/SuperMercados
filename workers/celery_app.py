from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Crear instancia de Celery
celery_app = Celery(
    'precio_comparador',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['workers.tasks']
)

# Configuración
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Bogota',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hora máximo por tarea
    task_soft_time_limit=3000,  # 50 minutos soft limit
)

# Programar tareas periódicas
celery_app.conf.beat_schedule = {
    'scrape-exito-diario': {
        'task': 'workers.tasks.scrape_exito',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM todos los días
    },
    'scrape-carulla-diario': {
        'task': 'workers.tasks.scrape_carulla',
        'schedule': crontab(hour=3, minute=0),  # 3:00 AM todos los días
    },
    'scrape-jumbo-diario': {
        'task': 'workers.tasks.scrape_jumbo',
        'schedule': crontab(hour=4, minute=0),  # 4:00 AM todos los días
    },
    'limpiar-productos-antiguos': {
        'task': 'workers.tasks.limpiar_datos_antiguos',
        'schedule': crontab(hour=1, minute=0, day_of_week=0),  # Domingo 1:00 AM
    },
}

if __name__ == '__main__':
    celery_app.start()