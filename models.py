from flask_sqlalchemy import SQLAlchemy
import datetime
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


db = SQLAlchemy()

class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))
    direccion = db.Column(db.String(50))
    telefono = db.Column(db.String(50))
    created_date = db.Column(db.DateTime, default=datetime.datetime.now)

class Pedidos(db.Model):
    __tablename__ = 'pizza'
    id = db.Column(db.Integer, primary_key=True)
    tamanio = db.Column(db.String(50))
    ingredientes = db.Column(db.String(50))
    cantidad = db.Column(db.Integer)
    created_date = db.Column(db.DateTime, default=datetime.datetime.now)

class Venta(db.Model):
    __tablename__ = 'ventas'
    idVenta = db.Column(db.Integer, primary_key=True)
    idPedido = db.Column(db.Integer, db.ForeignKey('pizza.id'), nullable=False)
    idCliente = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    fechaVenta = db.Column(db.DateTime, default=datetime.datetime.now)
    montoTotal = db.Column(db.Float, nullable=False)
    size = db.Column(db.String(20), nullable=False)
    ingredientes = db.Column(db.String(200), nullable=False)
    num_pizzas = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    cliente = db.relationship('Cliente', backref='ventas')
    pedido = db.relationship('Pedidos', backref='ventas')
    
class User(db.Model, UserMixin):  
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __init__(self, username, password=None, password_hash=None):
        self.username = username
        if password_hash:
            self.password = password_hash
        elif password:
            self.set_password(password)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password, password)

class ModelUser:
    @classmethod
    def login(cls, db, username, password):
        try:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                return user
            return None
        except SQLAlchemyError as e:
            print(f"Error en la conexión a la base de datos: {str(e)}")
            return None