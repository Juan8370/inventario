# 🚀 Puesta en Marcha

Esta guía explica cómo levantar la API, configurar el entorno y ejecutar pruebas.

## Requisitos
- Python 3.11+ (probado con 3.14)
- Windows PowerShell 5.1 (por defecto)

## 1) Crear y activar entorno virtual
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 2) Instalar dependencias
```powershell
pip install -r requirements.txt
# Si usas dependencias de dev
pip install -r requirements-dev.txt
```

Paquetes clave que usamos:
- fastapi, uvicorn
- sqlalchemy
- pydantic (v2)
- python-dotenv
- email-validator (para EmailStr)
- pytest, httpx (testing)

## 3) Variables de entorno
Copia `.env.example` a `.env` y ajusta valores:
```powershell
Copy-Item .env.example .env
```
Ver detalles en `docs/env.md`.

## 4) Ejecutar la API
Puedes correr con el script simple:
```powershell
py run.py
```
Por defecto expone:
- http://localhost:8000/
- http://localhost:8000/docs

## 5) Ejecutar pruebas
```powershell
pytest -v
# o solo endpoints
pytest test/test_endpoints.py -v
```

Si ves bloqueo del archivo SQLite en Windows, cierra procesos que usen `test_inventario.db` o vuelve a correr tests (ya incluimos `engine.dispose()` en teardown).
