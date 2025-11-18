from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Numeric
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# Tablas de tipos y estados

class TipoUsuario(Base):
    __tablename__ = "tipos_usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    usuarios = relationship("Usuario", back_populates="tipo_usuario")

class EstadoUsuario(Base):
    __tablename__ = "estados_usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    usuarios = relationship("Usuario", back_populates="estado_usuario")

class TipoProducto(Base):
    __tablename__ = "tipos_producto"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    productos = relationship("Producto", back_populates="tipo_producto")

class EstadoProducto(Base):
    __tablename__ = "estados_producto"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    productos = relationship("Producto", back_populates="estado_producto")

class EstadoVenta(Base):
    __tablename__ = "estados_venta"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    ventas = relationship("Venta", back_populates="estado_venta")

class TipoEmpresa(Base):
    __tablename__ = "tipos_empresa"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    empresas = relationship("Empresa", back_populates="tipo_empresa")

class EstadoEmpresa(Base):
    __tablename__ = "estados_empresa"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    empresas = relationship("Empresa", back_populates="estado_empresa")

class EstadoEmpleado(Base):
    __tablename__ = "estados_empleado"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    empleados = relationship("Empleado", back_populates="estado_empleado")

class TipoLog(Base):
    __tablename__ = "tipos_log"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    logs = relationship("Log", back_populates="tipo_log")

# Tablas principales

class Empresa(Base):
    __tablename__ = "empresas"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    ruc = Column(String(20), unique=True, nullable=False)
    direccion = Column(Text)
    telefono = Column(String(20))
    email = Column(String(100))
    contacto_principal = Column(String(200))
    tipo_empresa_id = Column(Integer, ForeignKey("tipos_empresa.id"))
    estado_empresa_id = Column(Integer, ForeignKey("estados_empresa.id"))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    tipo_empresa = relationship("TipoEmpresa", back_populates="empresas")
    estado_empresa = relationship("EstadoEmpresa", back_populates="empresas")
    empleados = relationship("Empleado", back_populates="empresa")
    usuarios = relationship("Usuario", back_populates="empresa")

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    telefono = Column(String(20))
    fecha_ultimo_acceso = Column(DateTime)
    empresa_id = Column(Integer, ForeignKey("empresas.id"))
    tipo_usuario_id = Column(Integer, ForeignKey("tipos_usuario.id"))
    estado_usuario_id = Column(Integer, ForeignKey("estados_usuario.id"))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    empresa = relationship("Empresa", back_populates="usuarios")
    tipo_usuario = relationship("TipoUsuario", back_populates="usuarios")
    estado_usuario = relationship("EstadoUsuario", back_populates="usuarios")
    ventas = relationship("Venta", back_populates="usuario")
    logs = relationship("Log", back_populates="usuario")

class Empleado(Base):
    __tablename__ = "empleados"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo_empleado = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    documento_identidad = Column(String(20), unique=True, nullable=False)
    telefono = Column(String(20))
    email = Column(String(100))
    direccion = Column(Text)
    cargo = Column(String(100))
    salario = Column(Numeric(10, 2))
    fecha_ingreso = Column(DateTime)
    fecha_salida = Column(DateTime)
    empresa_id = Column(Integer, ForeignKey("empresas.id"))
    estado_empleado_id = Column(Integer, ForeignKey("estados_empleado.id"))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    empresa = relationship("Empresa", back_populates="empleados")
    estado_empleado = relationship("EstadoEmpleado", back_populates="empleados")

class Producto(Base):
    __tablename__ = "productos"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(200), nullable=False, index=True)
    descripcion = Column(Text)
    marca = Column(String(100))
    modelo = Column(String(100))
    precio_compra = Column(Numeric(10, 2))
    precio_venta = Column(Numeric(10, 2))
    stock_minimo = Column(Integer, default=0)
    unidad_medida = Column(String(20))
    tipo_producto_id = Column(Integer, ForeignKey("tipos_producto.id"))
    estado_producto_id = Column(Integer, ForeignKey("estados_producto.id"))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    tipo_producto = relationship("TipoProducto", back_populates="productos")
    estado_producto = relationship("EstadoProducto", back_populates="productos")
    inventarios = relationship("Inventario", back_populates="producto")
    detalle_ventas = relationship("DetalleVenta", back_populates="producto")

class Inventario(Base):
    __tablename__ = "inventario"
    
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad_actual = Column(Integer, nullable=False, default=0)
    cantidad_reservada = Column(Integer, default=0)
    cantidad_disponible = Column(Integer, default=0)
    ubicacion = Column(String(100))
    lote = Column(String(50))
    fecha_vencimiento = Column(DateTime)
    fecha_ultima_entrada = Column(DateTime)
    fecha_ultima_salida = Column(DateTime)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    producto = relationship("Producto", back_populates="inventarios")

class Venta(Base):
    __tablename__ = "ventas"
    
    id = Column(Integer, primary_key=True, index=True)
    numero_venta = Column(String(50), unique=True, nullable=False, index=True)
    cliente_nombre = Column(String(200), nullable=False)
    cliente_documento = Column(String(20))
    cliente_telefono = Column(String(20))
    cliente_email = Column(String(100))
    cliente_direccion = Column(Text)
    subtotal = Column(Numeric(10, 2), nullable=False)
    impuesto = Column(Numeric(10, 2), default=0)
    descuento = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), nullable=False)
    fecha_venta = Column(DateTime, default=datetime.utcnow)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    estado_venta_id = Column(Integer, ForeignKey("estados_venta.id"))
    observaciones = Column(Text)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="ventas")
    estado_venta = relationship("EstadoVenta", back_populates="ventas")
    detalle_ventas = relationship("DetalleVenta", back_populates="venta")

class DetalleVenta(Base):
    __tablename__ = "detalle_ventas"
    
    id = Column(Integer, primary_key=True, index=True)
    venta_id = Column(Integer, ForeignKey("ventas.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    descuento_unitario = Column(Numeric(10, 2), default=0)
    subtotal = Column(Numeric(10, 2), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    venta = relationship("Venta", back_populates="detalle_ventas")
    producto = relationship("Producto", back_populates="detalle_ventas")

class Log(Base):
    """
    Tabla de logs del sistema - INMUTABLE
    Registra todas las acciones realizadas en el sistema
    Los registros NO pueden ser modificados ni eliminados una vez creados
    """
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(Text, nullable=False)
    usuario_tipo = Column(String(20), nullable=False)  # SYSTEM o USUARIO
    tipo_log_id = Column(Integer, ForeignKey("tipos_log.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)  # NULL para logs de SYSTEM
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relaciones
    tipo_log = relationship("TipoLog", back_populates="logs")
    usuario = relationship("Usuario", back_populates="logs")