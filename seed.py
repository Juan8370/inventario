import sys
import os

# Agregar el directorio actual al path para poder importar app
sys.path.append(os.getcwd())

from app.src.database.database import SessionLocal, create_tables
from app.src.database.fake_data import create_fake_data
from app.src.database.init_data import inicializar_datos_desarrollo

def main():
    print("Inicializando base de datos...")
    create_tables()
    print("Conectando a la base de datos...")
    db = SessionLocal()
    try:
        print("Cargando datos iniciales...")
        inicializar_datos_desarrollo(db)
        print("Cargando datos de prueba...")
        create_fake_data(db)
        print("¡Datos de prueba cargados exitosamente!")
    except Exception as e:
        print(f"Error al cargar datos: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
