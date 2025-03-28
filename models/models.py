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
    ROLES = {
        1: 'Usuario',
        2: 'Administrador'
    }
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.Integer, nullable=False, default=1)
    
    def __init__(self, username, password=None, password_hash=None, rol=1):
        self.username = username
        self.rol = rol
        if password_hash:
            self.password = password_hash
        elif password:
            self.set_password(password)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def get_role_name(self):
        return self.ROLES.get(self.rol, 'Desconocido')
    
    @classmethod
    def create_user(cls, username, password, rol=1):
        if User.query.filter_by(username=username).first():
            return None
            
        try:
            user = cls(username=username, rol=rol)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            print(f"Error al crear usuario: {str(e)}")
            return None
        
class ModelUser:
    @classmethod
    def login(cls, username, password):
        try:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                return user
            return None
        except Exception as e:
            print(f"Error de autenticación: {str(e)}")
            return None
        
class Proveedor(db.Model):
    __tablename__ = 'proveedor'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    empresa = db.Column(db.String(100))
    telefono = db.Column(db.String(50))
