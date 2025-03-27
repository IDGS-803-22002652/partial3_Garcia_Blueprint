from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField, SelectMultipleField, DateField
from wtforms.validators import DataRequired
import datetime
 

db = SQLAlchemy()
 
class ClientesForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    apaterno = StringField('Apellido Paterno', validators=[DataRequired()])
    amaterno = StringField('Apellido Materno', validators=[DataRequired()])
    direccion = StringField('Dirección', validators=[DataRequired()])
    telefono = StringField('Teléfono', validators=[DataRequired()])
    fecha = DateField('Fecha de Pedido', format='%Y-%m-%d', default=datetime.date.today, validators=[DataRequired()])

class PizzasForm(FlaskForm):
    tamanio = SelectField('Tamaño', choices=[('chica', 'Chica $40'), ('mediana', 'Mediana $80'), ('grande', 'Grande $120')], validators=[DataRequired()])
    ingredientes = SelectMultipleField('Ingredientes', choices=[('jamon', 'Jamón $10'), ('pina', 'Piña $10'), ('champinones', 'Champiñones $10')], validators=[DataRequired()])
    cantidad = IntegerField('Número de Pizzas', validators=[DataRequired()])
    submit = SubmitField('Agregar pedido')
    


