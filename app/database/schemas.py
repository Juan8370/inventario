from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, field_serializer
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import re

# Esquemas base para tipos y estados

class TipoUsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50, description="Nombre del tipo de usuario")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción del tipo de usuario")
    activo: bool = Field(True, description="Estado activo del tipo")

class TipoUsuarioCreate(TipoUsuarioBase):
    pass

class TipoUsuario(TipoUsuarioBase):
    id: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True

class EstadoUsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50, description="Nombre del estado")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción del estado")
    activo: bool = Field(True, description="Estado activo")

class EstadoUsuarioCreate(EstadoUsuarioBase):
    pass

class EstadoUsuario(EstadoUsuarioBase):
    id: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True

class TipoProductoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del tipo de producto")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción del tipo")
    activo: bool = Field(True, description="Estado activo del tipo")

class TipoProductoCreate(TipoProductoBase):
    pass

class TipoProducto(TipoProductoBase):
    id: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True

class EstadoProductoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50, description="Nombre del estado")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción del estado")
    activo: bool = Field(True, description="Estado activo")

class EstadoProductoCreate(EstadoProductoBase):
    pass

class EstadoProducto(EstadoProductoBase):
    id: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True

class EstadoVentaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50, description="Nombre del estado de venta")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción del estado")
    activo: bool = Field(True, description="Estado activo")

class EstadoVentaCreate(EstadoVentaBase):
    pass

class EstadoVenta(EstadoVentaBase):
    id: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True

class TipoEmpresaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del tipo de empresa")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción del tipo")
    activo: bool = Field(True, description="Estado activo del tipo")

class TipoEmpresaCreate(TipoEmpresaBase):
    pass

class TipoEmpresa(TipoEmpresaBase):
    id: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True

class EstadoEmpresaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50, description="Nombre del estado")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción del estado")
    activo: bool = Field(True, description="Estado activo")

class EstadoEmpresaCreate(EstadoEmpresaBase):
    pass

class EstadoEmpresa(EstadoEmpresaBase):
    id: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True

class EstadoEmpleadoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50, description="Nombre del estado del empleado")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción del estado")
    activo: bool = Field(True, description="Estado activo")

class EstadoEmpleadoCreate(EstadoEmpleadoBase):
    pass

class EstadoEmpleado(EstadoEmpleadoBase):
    id: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True

# Esquemas principales

class EmpresaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200, description="Nombre de la empresa")
    ruc: str = Field(..., min_length=8, max_length=20, description="RUC de la empresa")
    direccion: Optional[str] = Field(None, max_length=500, description="Dirección de la empresa")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto")
    email: Optional[EmailStr] = Field(None, description="Email de contacto")
    contacto_principal: Optional[str] = Field(None, max_length=200, description="Nombre del contacto principal")
    tipo_empresa_id: int = Field(..., gt=0, description="ID del tipo de empresa")
    estado_empresa_id: int = Field(..., gt=0, description="ID del estado de la empresa")

    @field_validator('ruc')
    @classmethod
    def validar_ruc(cls, v):
        if not re.match(r'^[0-9-]+$', v):
            raise ValueError('El RUC debe contener solo números y guiones')
        return v

    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, v):
        if v and not re.match(r'^[\+0-9\-\s\(\)]+$', v):
            raise ValueError('Formato de teléfono inválido')
        return v

class EmpresaCreate(EmpresaBase):
    pass

class EmpresaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=200)
    direccion: Optional[str] = Field(None, max_length=500)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    contacto_principal: Optional[str] = Field(None, max_length=200)
    tipo_empresa_id: Optional[int] = Field(None, gt=0)
    estado_empresa_id: Optional[int] = Field(None, gt=0)

class Empresa(EmpresaBase):
    id: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    tipo_empresa: Optional[TipoEmpresa] = None
    estado_empresa: Optional[EstadoEmpresa] = None

    class Config:
        from_attributes = True

class UsuarioBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario")
    email: EmailStr = Field(..., description="Email del usuario")
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del usuario")
    apellido: str = Field(..., min_length=1, max_length=100, description="Apellido del usuario")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono del usuario")
    empresa_id: Optional[int] = Field(None, gt=0, description="ID de la empresa")
    tipo_usuario_id: int = Field(..., gt=0, description="ID del tipo de usuario")
    estado_usuario_id: int = Field(..., gt=0, description="ID del estado del usuario")

    @field_validator('username')
    @classmethod
    def validar_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('El username solo puede contener letras, números y guiones bajos')
        return v

    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, v):
        if v and not re.match(r'^[\+0-9\-\s\(\)]+$', v):
            raise ValueError('Formato de teléfono inválido')
        return v

class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=8, max_length=128, description="Contraseña del usuario")

    @field_validator('password')
    @classmethod
    def validar_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('La contraseña debe contener al menos una letra')
        if not re.search(r'[0-9]', v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v

class UsuarioUpdate(BaseModel):
    email: Optional[EmailStr] = None
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    apellido: Optional[str] = Field(None, min_length=1, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    tipo_usuario_id: Optional[int] = Field(None, gt=0)
    estado_usuario_id: Optional[int] = Field(None, gt=0)

class Usuario(UsuarioBase):
    id: int
    fecha_ultimo_acceso: Optional[datetime] = None
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    empresa: Optional[Empresa] = None
    tipo_usuario: Optional[TipoUsuario] = None
    estado_usuario: Optional[EstadoUsuario] = None

    class Config:
        from_attributes = True

class EmpleadoBase(BaseModel):
    codigo_empleado: str = Field(..., min_length=1, max_length=20, description="Código único del empleado")
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del empleado")
    apellido: str = Field(..., min_length=1, max_length=100, description="Apellido del empleado")
    documento_identidad: str = Field(..., min_length=5, max_length=20, description="Documento de identidad")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono del empleado")
    email: Optional[EmailStr] = Field(None, description="Email del empleado")
    direccion: Optional[str] = Field(None, max_length=500, description="Dirección del empleado")
    cargo: Optional[str] = Field(None, max_length=100, description="Cargo del empleado")
    salario: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Salario del empleado")
    fecha_ingreso: Optional[datetime] = Field(None, description="Fecha de ingreso")
    fecha_salida: Optional[datetime] = Field(None, description="Fecha de salida")
    empresa_id: int = Field(..., gt=0, description="ID de la empresa")
    estado_empleado_id: int = Field(..., gt=0, description="ID del estado del empleado")

    @field_validator('documento_identidad')
    @classmethod
    def validar_documento(cls, v):
        if not re.match(r'^[0-9A-Za-z\-]+$', v):
            raise ValueError('El documento debe contener solo números, letras y guiones')
        return v

    @field_validator('codigo_empleado')
    @classmethod
    def validar_codigo_empleado(cls, v):
        if not re.match(r'^[A-Za-z0-9\-_]+$', v):
            raise ValueError('El código debe contener solo letras, números, guiones y guiones bajos')
        return v

class EmpleadoCreate(EmpleadoBase):
    pass

class EmpleadoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    apellido: Optional[str] = Field(None, min_length=1, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    direccion: Optional[str] = Field(None, max_length=500)
    cargo: Optional[str] = Field(None, max_length=100)
    salario: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    fecha_salida: Optional[datetime] = None
    estado_empleado_id: Optional[int] = Field(None, gt=0)

class Empleado(EmpleadoBase):
    id: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    empresa: Optional[Empresa] = None
    estado_empleado: Optional[EstadoEmpleado] = None

    class Config:
        from_attributes = True

class ProductoBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50, description="Código único del producto")
    nombre: str = Field(..., min_length=1, max_length=200, description="Nombre del producto")
    descripcion: Optional[str] = Field(None, max_length=1000, description="Descripción del producto")
    marca: Optional[str] = Field(None, max_length=100, description="Marca del producto")
    modelo: Optional[str] = Field(None, max_length=100, description="Modelo del producto")
    precio_compra: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Precio de compra")
    precio_venta: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Precio de venta")
    stock_minimo: int = Field(0, ge=0, description="Stock mínimo requerido")
    unidad_medida: Optional[str] = Field(None, max_length=20, description="Unidad de medida")
    tipo_producto_id: int = Field(..., gt=0, description="ID del tipo de producto")
    estado_producto_id: int = Field(..., gt=0, description="ID del estado del producto")

    @field_validator('codigo')
    @classmethod
    def validar_codigo(cls, v):
        if not re.match(r'^[A-Za-z0-9\-_]+$', v):
            raise ValueError('El código debe contener solo letras, números, guiones y guiones bajos')
        return v

    @model_validator(mode='after')
    def validar_precios(self):
        if self.precio_compra and self.precio_venta and self.precio_venta < self.precio_compra:
            raise ValueError('El precio de venta no puede ser menor al precio de compra')
        return self

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=1000)
    marca: Optional[str] = Field(None, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    precio_compra: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    precio_venta: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    stock_minimo: Optional[int] = Field(None, ge=0)
    unidad_medida: Optional[str] = Field(None, max_length=20)
    tipo_producto_id: Optional[int] = Field(None, gt=0)
    estado_producto_id: Optional[int] = Field(None, gt=0)

class Producto(ProductoBase):
    id: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    tipo_producto: Optional[TipoProducto] = None
    estado_producto: Optional[EstadoProducto] = None

    class Config:
        from_attributes = True

    @field_serializer('precio_compra', 'precio_venta')
    def _serialize_decimals(self, v):
        if v is None:
            return v
        try:
            return float(v)
        except Exception:
            return v

class InventarioBase(BaseModel):
    producto_id: int = Field(..., gt=0, description="ID del producto")
    cantidad_actual: int = Field(..., ge=0, description="Cantidad actual en stock")
    cantidad_reservada: int = Field(0, ge=0, description="Cantidad reservada")
    cantidad_disponible: int = Field(0, ge=0, description="Cantidad disponible")
    ubicacion: Optional[str] = Field(None, max_length=100, description="Ubicación en almacén")
    lote: Optional[str] = Field(None, max_length=50, description="Número de lote")
    fecha_vencimiento: Optional[datetime] = Field(None, description="Fecha de vencimiento")
    fecha_ultima_entrada: Optional[datetime] = Field(None, description="Última fecha de entrada")
    fecha_ultima_salida: Optional[datetime] = Field(None, description="Última fecha de salida")

    @model_validator(mode='after')
    def validar_cantidades(self):
        if self.cantidad_reservada > self.cantidad_actual:
            raise ValueError('La cantidad reservada no puede ser mayor a la cantidad actual')
        
        if self.cantidad_disponible != (self.cantidad_actual - self.cantidad_reservada):
            self.cantidad_disponible = self.cantidad_actual - self.cantidad_reservada
        
        return self

class InventarioCreate(InventarioBase):
    pass

class InventarioUpdate(BaseModel):
    cantidad_actual: Optional[int] = Field(None, ge=0)
    cantidad_reservada: Optional[int] = Field(None, ge=0)
    ubicacion: Optional[str] = Field(None, max_length=100)
    lote: Optional[str] = Field(None, max_length=50)
    fecha_vencimiento: Optional[datetime] = None
    fecha_ultima_entrada: Optional[datetime] = None
    fecha_ultima_salida: Optional[datetime] = None

class Inventario(InventarioBase):
    id: int
    fecha_actualizacion: datetime
    producto: Optional[Producto] = None

    class Config:
        from_attributes = True

class DetalleVentaBase(BaseModel):
    producto_id: int = Field(..., gt=0, description="ID del producto")
    cantidad: int = Field(..., gt=0, description="Cantidad vendida")
    precio_unitario: Decimal = Field(..., gt=0, decimal_places=2, description="Precio unitario")
    descuento_unitario: Decimal = Field(0, ge=0, decimal_places=2, description="Descuento por unidad")
    subtotal: Decimal = Field(..., ge=0, decimal_places=2, description="Subtotal del detalle")

    @model_validator(mode='after')
    def validar_subtotal(self):
        if self.cantidad and self.precio_unitario:
            subtotal_calculado = (self.precio_unitario - self.descuento_unitario) * self.cantidad
            self.subtotal = subtotal_calculado
        
        return self

class DetalleVentaCreate(DetalleVentaBase):
    pass

class DetalleVenta(DetalleVentaBase):
    id: int
    venta_id: int
    fecha_creacion: datetime
    producto: Optional[Producto] = None

    class Config:
        from_attributes = True

class VentaBase(BaseModel):
    numero_venta: str = Field(..., min_length=1, max_length=50, description="Número de venta")
    cliente_nombre: str = Field(..., min_length=1, max_length=200, description="Nombre del cliente")
    cliente_documento: Optional[str] = Field(None, max_length=20, description="Documento del cliente")
    cliente_telefono: Optional[str] = Field(None, max_length=20, description="Teléfono del cliente")
    cliente_email: Optional[EmailStr] = Field(None, description="Email del cliente")
    cliente_direccion: Optional[str] = Field(None, max_length=500, description="Dirección del cliente")
    subtotal: Decimal = Field(..., ge=0, decimal_places=2, description="Subtotal de la venta")
    impuesto: Decimal = Field(0, ge=0, decimal_places=2, description="Impuesto aplicado")
    descuento: Decimal = Field(0, ge=0, decimal_places=2, description="Descuento aplicado")
    total: Decimal = Field(..., gt=0, decimal_places=2, description="Total de la venta")
    fecha_venta: datetime = Field(default_factory=datetime.utcnow, description="Fecha de la venta")
    usuario_id: int = Field(..., gt=0, description="ID del usuario que registra la venta")
    estado_venta_id: int = Field(..., gt=0, description="ID del estado de la venta")
    observaciones: Optional[str] = Field(None, max_length=1000, description="Observaciones de la venta")

    @field_validator('numero_venta')
    @classmethod
    def validar_numero_venta(cls, v):
        if not re.match(r'^[A-Za-z0-9\-_]+$', v):
            raise ValueError('El número de venta debe contener solo letras, números, guiones y guiones bajos')
        return v

    @model_validator(mode='after')
    def validar_total(self):
        if self.subtotal:
            total_calculado = self.subtotal + self.impuesto - self.descuento
            if total_calculado < 0:
                raise ValueError('El total no puede ser negativo')
            self.total = total_calculado
        
        return self

class VentaCreate(VentaBase):
    detalle_ventas: List[DetalleVentaCreate] = Field(..., min_items=1, description="Detalles de la venta")

class VentaUpdate(BaseModel):
    cliente_nombre: Optional[str] = Field(None, min_length=1, max_length=200)
    cliente_documento: Optional[str] = Field(None, max_length=20)
    cliente_telefono: Optional[str] = Field(None, max_length=20)
    cliente_email: Optional[EmailStr] = None
    cliente_direccion: Optional[str] = Field(None, max_length=500)
    estado_venta_id: Optional[int] = Field(None, gt=0)
    observaciones: Optional[str] = Field(None, max_length=1000)

class Venta(VentaBase):
    id: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    usuario: Optional[Usuario] = None
    estado_venta: Optional[EstadoVenta] = None
    detalle_ventas: List[DetalleVenta] = []

    class Config:
        from_attributes = True

# Esquemas de respuesta para listas
class ListResponse(BaseModel):
    items: List[BaseModel]
    total: int
    page: int
    size: int
    pages: int