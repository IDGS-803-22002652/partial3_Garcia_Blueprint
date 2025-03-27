from flask import Flask, flash, render_template, redirect, url_for, request, session
from flask_wtf.csrf import CSRFProtect
from models import Pedidos, Venta, Cliente, User, ModelUser, db
from config import DevelopmentConfig
import os
import forms
from flask_login import LoginManager, login_user, login_required, logout_user, current_user  

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

db.init_app(app)
with app.app_context():
    db.create_all()
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    
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

@app.route('/')
def ind():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        logged_user = ModelUser.login(db, username, password)
        
        if logged_user:
            login_user(logged_user)
            flash("¡Bienvenido!", "login")
            return redirect(url_for('index'))
        else:
            flash("Usuario o contraseña incorrectos", "login")
    
    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada exitosamente', 'login')
    return redirect(url_for('login'))
 
@app.route('/index')
@login_required
def index():
    create_form = forms.ClientesForm(request.form)
    pedidos = cargar_pedidos()
    ventas = Venta.query.all()
    total_ventas = sum(venta.montoTotal for venta in ventas)
    ventas_agrupadas = {}
    
    for venta in ventas:
        cliente_nombre = venta.cliente.nombre
        if cliente_nombre not in ventas_agrupadas:
            ventas_agrupadas[cliente_nombre] = {
                'montoTotal': 0,
                'idCliente': venta.idCliente
            }
        ventas_agrupadas[cliente_nombre]['montoTotal'] += venta.montoTotal
        
    return render_template("index.html", pedidos=pedidos, form=create_form, ventas=ventas_agrupadas, total_ventas=total_ventas)

@app.route('/pedido', methods=['GET', 'POST'])
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
        return redirect(url_for('index'))
    return render_template('index.html')

@app.route('/terminar', methods=['POST'])
def terminar_pedidos():
    """Transfiere los pedidos del archivo a la base de datos y limpia el archivo."""
    pedidos = cargar_pedidos()

    if not pedidos:
        flash("No hay pedidos para transferir.", "index")  
        return redirect(url_for('index'))

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
    return redirect(url_for('index'))

@app.route('/quitar_pedido/<int:index>', methods=['POST'])
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
    return redirect(url_for('index'))  

if __name__ == '__main__':
    app.run(debug=True)