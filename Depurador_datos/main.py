# python -m venv venv  -> Crear entorno virtual
# venv\Scripts\activate -> Activar entorno virtual
# pip install -r requirements.txt -> Instalar dependencias
# python main.py -> Ejecutar programa

from config.database import DatabaseConfig
#from src.extractors.db_extractor import DataExtractor
#from src.cleaners.data_cleaner import DataCleaner
#from src.loaders.db_loader import DataLoader

def main():
    print("="*60)
    print("DEPURADOR DE BASE DE DATOS - precio_comparador")
    print("="*60)
    
    print("\nConectando a SQL Server...")
    try:
        engine = DatabaseConfig.get_engine()
        print("Engine creado exitosamente")
        
        # Probar conexión
        if not DatabaseConfig.test_connection(engine):
            print("No se pudo conectar. Verifica tus credenciales.")
            return
        else: 
            print("Conexión exitosa!")
            return
    except Exception as e:
        print(f"Error: {e}")
        return

if __name__ == "__main__":
    main()