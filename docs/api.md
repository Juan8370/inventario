# 📡 API - Endpoints Principales

Todos los endpoints devuelven códigos de estado HTTP correctos (200/201/400/404/422/503).

Base URL por defecto: `<http://localhost:8000>`

## Salud y Meta

- `GET /` (200)
  - Bienvenida y metadatos (version, docs)

- `GET /health` (200 | 503)
  - Verifica conexión a la BD (`SELECT 1`)
  - 503 si falla conexión

- `GET /db/info` (200)
  - `database_url` (sin credenciales)
  - `tables` (lista de tablas)
  - `total_tables`

- `GET /stats` (200)
  - `total_productos`, `total_empresas`, `total_usuarios`

## Productos

- `GET /productos?skip=0&limit=10` (200)
  - Paginación con `skip >= 0`, `limit >= 1` (422 si inválido)

- `GET /productos/{id}` (200 | 404)

- `POST /productos` (201 | 400/422)
  
```json
{
  "codigo": "PROD-001",
  "nombre": "Laptop Test",
  "descripcion": "...",
  "marca": "TestBrand",
  "modelo": "X-100",
  "precio_compra": 800.0,
  "precio_venta": 1000.0,
  "stock_minimo": 5,
  "unidad_medida": "pza",
  "tipo_producto_id": 1,
  "estado_producto_id": 1
}
```
  
  - 400 si `codigo` duplicado

- `PUT /productos/{id}` (200 | 404)
  
```json
{
  "nombre": "Producto Actualizado",
  "precio_venta": 175.0
}
```

- `DELETE /productos/{id}` (200 | 404)

- `GET /productos/buscar/{termino}?skip=0&limit=10` (200)
  - Busca por `nombre`, `codigo`, `descripcion`, `marca`

## Empresas

- `GET /empresas?skip=0&limit=10` (200)
- `POST /empresas` (201 | 400/422)
  
```json
{
  "nombre": "Empresa Test S.A.",
  "ruc": "20123456789",
  "direccion": "Av. Test 123",
  "telefono": "555-1234",
  "email": "contacto@empresatest.com",
  "contacto_principal": "Juan Pérez",
  "tipo_empresa_id": 1,
  "estado_empresa_id": 1
}
```
  
  - 400 si `ruc` duplicado

## Notas

- Serialización de precios (`precio_compra`, `precio_venta`) como números (no strings).
- Tablas se crean automáticamente en `startup`.
- CORS configurado con `ALLOWED_ORIGINS`.
