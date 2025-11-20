import random
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.src.database import models, crud, schemas
from app.src.auth.password import PasswordHandler

def create_fake_data(db: Session):
    """
    Poblar la base de datos con datos de prueba
    """
    print("Iniciando generación de datos de prueba...")

    # 1. Asegurar tipos y estados básicos (ya deberían estar por init_data, pero por si acaso)
    # Tipos de Producto
    tipos_producto = ["Electrónica", "Ropa", "Hogar", "Juguetes", "Deportes"]
    db_tipos_prod = []
    for nombre in tipos_producto:
        tipo = db.query(models.TipoProducto).filter_by(nombre=nombre).first()
        if not tipo:
            tipo = models.TipoProducto(nombre=nombre, descripcion=f"Productos de {nombre}")
            db.add(tipo)
            db.commit()
            db.refresh(tipo)
        db_tipos_prod.append(tipo)

    # Estados de Producto
    estado_prod_activo = db.query(models.EstadoProducto).filter_by(nombre="Activo").first()
    if not estado_prod_activo:
        estado_prod_activo = models.EstadoProducto(nombre="Activo", descripcion="Producto disponible")
        db.add(estado_prod_activo)
        db.commit()
        db.refresh(estado_prod_activo)

    # Estados de Venta
    estados_venta = ["Completada", "Pendiente", "Cancelada"]
    db_estados_venta = []
    for nombre in estados_venta:
        estado = db.query(models.EstadoVenta).filter_by(nombre=nombre).first()
        if not estado:
            estado = models.EstadoVenta(nombre=nombre, descripcion=f"Venta {nombre}")
            db.add(estado)
            db.commit()
            db.refresh(estado)
        db_estados_venta.append(estado)

    # Tipos de Transacción
    tipo_entrada = db.query(models.TipoTransaccion).filter_by(nombre="ENTRADA").first()
    if not tipo_entrada:
        tipo_entrada = models.TipoTransaccion(nombre="ENTRADA", descripcion="Entrada de inventario")
        db.add(tipo_entrada)
        db.commit()
        db.refresh(tipo_entrada)
    
    tipo_salida = db.query(models.TipoTransaccion).filter_by(nombre="SALIDA").first()
    if not tipo_salida:
        tipo_salida = models.TipoTransaccion(nombre="SALIDA", descripcion="Salida de inventario")
        db.add(tipo_salida)
        db.commit()
        db.refresh(tipo_salida)

    # 2. Crear Clientes
    nombres = ["Juan", "Maria", "Pedro", "Ana", "Luis", "Carmen", "Jose", "Laura", "Carlos", "Sofia"]
    apellidos = ["Perez", "Gomez", "Rodriguez", "Lopez", "Garcia", "Martinez", "Sanchez", "Diaz", "Torres", "Ruiz"]
    
    clientes = []
    for i in range(20):
        nombre = random.choice(nombres)
        apellido = random.choice(apellidos)
        identidad = f"{random.randint(10000000, 99999999)}"
        
        # Verificar si ya existe
        if db.query(models.Cliente).filter_by(identidad=identidad).first():
            continue

        cliente = models.Cliente(
            nombre=nombre,
            apellido=apellido,
            identidad=identidad,
            telefono=f"555-{random.randint(1000, 9999)}",
            email=f"{nombre.lower()}.{apellido.lower()}{i}@example.com",
            direccion=f"Calle {random.randint(1, 100)}, Ciudad",
            descripcion="Cliente generado automáticamente"
        )
        db.add(cliente)
        clientes.append(cliente)
    
    db.commit()
    for c in clientes: db.refresh(c)
    print(f"Creados {len(clientes)} clientes.")

    # 3. Crear Productos e Inventario
    productos_data = [
        ("Laptop Gamer", 1200.00, 1500.00, "Electrónica"),
        ("Mouse Inalámbrico", 15.00, 25.00, "Electrónica"),
        ("Teclado Mecánico", 45.00, 80.00, "Electrónica"),
        ("Monitor 24 pulgadas", 120.00, 180.00, "Electrónica"),
        ("Camiseta Algodón", 5.00, 15.00, "Ropa"),
        ("Jeans Clásicos", 15.00, 35.00, "Ropa"),
        ("Zapatillas Deportivas", 30.00, 60.00, "Ropa"),
        ("Juego de Sábanas", 20.00, 40.00, "Hogar"),
        ("Lámpara de Escritorio", 10.00, 25.00, "Hogar"),
        ("Balón de Fútbol", 12.00, 25.00, "Deportes"),
    ]

    productos = []
    for nombre, p_compra, p_venta, tipo_nombre in productos_data:
        codigo = f"PROD-{random.randint(1000, 9999)}"
        
        # Buscar tipo
        tipo_obj = next((t for t in db_tipos_prod if t.nombre == tipo_nombre), db_tipos_prod[0])
        
        if db.query(models.Producto).filter_by(nombre=nombre).first():
            continue

        producto = models.Producto(
            codigo=codigo,
            nombre=nombre,
            descripcion=f"Descripción de {nombre}",
            precio_compra=Decimal(p_compra),
            precio_venta=Decimal(p_venta),
            stock_minimo=5,
            tipo_producto_id=tipo_obj.id,
            estado_producto_id=estado_prod_activo.id
        )
        db.add(producto)
        db.commit()
        db.refresh(producto)
        productos.append(producto)

        # Inventario inicial
        cantidad = random.randint(10, 100)
        inventario = models.Inventario(
            producto_id=producto.id,
            cantidad_actual=cantidad,
            cantidad_disponible=cantidad,
            cantidad_reservada=0,
            ubicacion=f"Estante {random.choice(['A', 'B', 'C'])}-{random.randint(1, 5)}"
        )
        db.add(inventario)
        
        # Registrar transacción de entrada inicial
        transaccion = models.Transaccion(
            tipo_transaccion_id=tipo_entrada.id,
            producto_id=producto.id,
            cantidad=cantidad,
            fecha=datetime.utcnow(),
            observaciones="Inventario inicial (Seed)",
            usuario_id=1 # Asumiendo admin id 1
        )
        db.add(transaccion)

    db.commit()
    print(f"Creados {len(productos)} productos con inventario.")

    # 4. Crear Ventas Históricas
    # Necesitamos un vendedor (usuario)
    vendedor = db.query(models.Usuario).first()
    if not vendedor:
        print("No se encontró usuario vendedor. Saltando creación de ventas.")
        return

    estado_completada = next((e for e in db_estados_venta if e.nombre == "Completada"), None)
    
    if not clientes:
        clientes = db.query(models.Cliente).all()
    
    if not productos:
        productos = db.query(models.Producto).all()

    if clientes and productos and estado_completada:
        for _ in range(30): # 30 ventas aleatorias
            cliente = random.choice(clientes)
            fecha_venta = datetime.utcnow() - timedelta(days=random.randint(0, 60))
            
            # Detalles de venta
            num_items = random.randint(1, 5)
            detalles = []
            total_venta = Decimal(0)
            
            items_seleccionados = random.sample(productos, min(len(productos), num_items))
            
            venta = models.Venta(
                factura_id=f"F-{random.randint(10000, 99999)}",
                cliente_id=cliente.id,
                vendedor_id=vendedor.id,
                estado_venta_id=estado_completada.id,
                fecha=fecha_venta,
                valor_total=0, # Se actualiza luego
                observaciones="Venta generada automáticamente"
            )
            db.add(venta)
            db.commit()
            db.refresh(venta)

            for prod in items_seleccionados:
                cantidad = random.randint(1, 3)
                precio = prod.precio_venta
                subtotal = precio * cantidad
                total_venta += subtotal
                
                detalle = models.DetalleVenta(
                    venta_id=venta.id,
                    producto_id=prod.id,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    descuento_unitario=0,
                    subtotal=subtotal
                )
                db.add(detalle)
                
                # Transacción de salida
                transaccion = models.Transaccion(
                    tipo_transaccion_id=tipo_salida.id,
                    producto_id=prod.id,
                    cantidad=cantidad,
                    fecha=fecha_venta,
                    venta_id=venta.id,
                    usuario_id=vendedor.id,
                    observaciones=f"Venta #{venta.factura_id}"
                )
                db.add(transaccion)
                
                # Actualizar inventario
                inv = db.query(models.Inventario).filter_by(producto_id=prod.id).first()
                if inv:
                    inv.cantidad_actual -= cantidad
                    inv.cantidad_disponible -= cantidad
                    inv.fecha_ultima_salida = fecha_venta

            venta.valor_total = total_venta
            db.add(venta)
        
        db.commit()
        print("Creadas 30 ventas aleatorias.")

    print("Generación de datos completada.")

if __name__ == "__main__":
    from app.src.database.database import SessionLocal
    db = SessionLocal()
    try:
        create_fake_data(db)
    finally:
        db.close()
