from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from models.models import Pedidos, Venta, Cliente, db
from forms import ClientesForm, PizzasForm
from datetime import datetime, timedelta
from sqlalchemy import extract, func
import os
from controllers.auth import rol_required

pizzas_bp = Blueprint('pizzas', __name__)

PEDIDOS_FILE = "pedidos.txt"

def guardar_pedido(pedido):
    with open(PEDIDOS_FILE, "a") as f:
        f.write(f"{pedido['nombre']}|{pedido['direccion']}|{pedido['telefono']}|{pedido['size']}|{','.join(pedido['ingredientes'])}|{pedido['num_pizzas']}|{pedido['subtotal']}\n")

def cargar_pedidos():
    pedidos = []
    if os.path.exists(PEDIDOS_FILE):
        with open(PEDIDOS_FILE, "r") as f:
            for linea in f:
                datos = linea.strip().split("|")
                if len(datos) != 7:
                    print(f"Error: Línea mal formada en pedidos.txt -> {linea.strip()}")
                    continue  
                try:
                    pedidos.append({
                        "nombre": datos[0],
                        "direccion": datos[1],
                        "telefono": datos[2],
                        "size": datos[3],
                        "ingredientes": datos[4].split(",") if datos[4] else [],
                        "num_pizzas": int(datos[5]),
                        "subtotal": float(datos[6])
                    })
                except ValueError as e:
                    print(f"Error al convertir datos: {e}, en línea: {linea.strip()}")
                    continue  
    return pedidos

@pizzas_bp.route('/')
@pizzas_bp.route('/index')
@login_required
@rol_required(1)
def index():
    create_form = ClientesForm(request.form)
    pedidos = cargar_pedidos()
    
    filter_type = request.args.get('filter_type', 'day')
    specific_date = request.args.get('specific_date')
    
    sales_query = db.session.query(
        Cliente.nombre,
        func.sum(Venta.montoTotal).label('total')
    ).join(Venta.cliente)
    
    if filter_type == 'day':
        if specific_date:
            date_obj = datetime.strptime(specific_date, '%Y-%m-%d').date()
            sales_query = sales_query.filter(func.date(Venta.fechaVenta) == date_obj)
        else:
            sales_query = sales_query.filter(func.date(Venta.fechaVenta) == datetime.today().date())
    elif filter_type == 'month':
        if specific_date:
            year, month = map(int, specific_date.split('-'))
            sales_query = sales_query.filter(
                extract('year', Venta.fechaVenta) == year,
                extract('month', Venta.fechaVenta) == month
            )
        else:
            today = datetime.today()
            sales_query = sales_query.filter(
                extract('year', Venta.fechaVenta) == today.year,
                extract('month', Venta.fechaVenta) == today.month
            )
    
    sales_data = sales_query.group_by(Cliente.nombre).all()
    
    ventas_agrupadas = {
        cliente: {'montoTotal': total, 'idCliente': None}  
        for cliente, total in sales_data
    }
    
    total_ventas = sum(total for _, total in sales_data)
    
    return render_template(
        "index.html", 
        pedidos=pedidos, 
        form=create_form, 
        ventas=ventas_agrupadas, 
        total_ventas=total_ventas,
        current_filter=filter_type,
        selected_date=specific_date 
    )

@pizzas_bp.route('/pedido', methods=['GET', 'POST'])
@login_required
@rol_required(1)
def pedido():
    if request.method == 'POST':
        nombre = request.form['nombre']
        direccion = request.form['direccion']
        telefono = request.form['telefono']
        size = request.form['size']
        ingredientes = request.form.getlist('ingredientes')
        num_pizzas = int(request.form['num_pizzas'])
        session['cliente'] = {
            'nombre': nombre,
            'direccion': direccion,
            'telefono': telefono
        }
        precios = {"chica": 40, "mediana": 80, "grande": 120}
        precio_unitario = precios.get(size, 40)
        precio_ingrediente = 10
        subtotal = (precio_unitario + (precio_ingrediente * len(ingredientes))) * num_pizzas
        pedido = {
            "nombre": nombre,
            "direccion": direccion,
            "telefono": telefono,
            "size": size,
            "ingredientes": ingredientes,
            "num_pizzas": num_pizzas,
            "subtotal": subtotal
        }
        guardar_pedido(pedido)
        return redirect(url_for('pizzas.index'))
    return render_template('index.html')

@pizzas_bp.route('/terminar', methods=['POST'])
@login_required
@rol_required(1)
def terminar_pedidos():
    """Transfiere los pedidos del archivo a la base de datos y limpia el archivo."""
    pedidos = cargar_pedidos()

    if not pedidos:
        flash("No hay pedidos para transferir.", "index")  
        return redirect(url_for('pizzas.index'))

    last_venta = Venta.query.order_by(Venta.idVenta.desc()).first()
    next_id_venta = (last_venta.idVenta + 1) if last_venta else 1  

    for pedido in pedidos:
        cliente = Cliente.query.filter_by(nombre=pedido["nombre"], telefono=pedido["telefono"]).first()
        if not cliente:
            cliente = Cliente(nombre=pedido["nombre"], direccion=pedido["direccion"], telefono=pedido["telefono"])
            db.session.add(cliente)
            db.session.commit()

        nuevo_pedido = Pedidos(
            tamanio=pedido["size"],
            ingredientes=", ".join(pedido["ingredientes"]),
            cantidad=pedido["num_pizzas"]
        )
        db.session.add(nuevo_pedido)
        db.session.commit()

        precios = {"chica": 40, "mediana": 80, "grande": 120}
        precio_unitario = precios.get(pedido["size"], 40)
        precio_ingrediente = 10
        subtotal = (precio_unitario + (precio_ingrediente * len(pedido["ingredientes"]))) * pedido["num_pizzas"]

        venta_existente = Venta.query.filter_by(idCliente=cliente.id).first()
        if venta_existente:
            venta_existente.montoTotal += subtotal
            db.session.commit()  
        else:
            nueva_venta = Venta(
                idVenta=next_id_venta,  
                idPedido=nuevo_pedido.id,
                idCliente=cliente.id,
                montoTotal=subtotal,
                size=pedido["size"],
                ingredientes=", ".join(pedido["ingredientes"]),
                num_pizzas=pedido["num_pizzas"],
                subtotal=subtotal
            )
            db.session.add(nueva_venta)
            next_id_venta += 1  

    db.session.commit()
    session.pop('cliente', None)

    open(PEDIDOS_FILE, "w").close() 
    flash("Pedidos guardados.", "success") 
    return redirect(url_for('pizzas.index'))

@pizzas_bp.route('/quitar_pedido/<int:index>', methods=['POST'])
@login_required
@rol_required(1)
def quitar_pedido(index):
    with open("pedidos.txt", "r") as file:
        pedidos = file.readlines()
    if 0 <= index < len(pedidos):
        del pedidos[index] 
        with open("pedidos.txt", "w") as file:
            file.writelines(pedidos)  
        flash("Pedido eliminado correctamente.", "success")
    else:
        flash("No se pudo eliminar el pedido.", "error") 
    return redirect(url_for('pizzas.index'))