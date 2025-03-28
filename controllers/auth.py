from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, current_user
from models.models import User, ModelUser, db
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def rol_required(rol_necesario):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.rol != rol_necesario:
                abort(404)  
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.rol == 2:
            return redirect(url_for('provedores.index'))
        return redirect(url_for('pizzas.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash("Usuario y contraseña son requeridos", "login")
            return redirect(url_for('auth.login'))
            
        logged_user = ModelUser.login(username, password)
        
        if logged_user:
            login_user(logged_user)
            flash("¡Bienvenido!", "login")
            if logged_user.rol == 2:
                return redirect(url_for('provedores.index'))
            return redirect(url_for('pizzas.index'))
        else:
            flash("Usuario o contraseña incorrectos", "login")
    
    return render_template("login.html")

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Sesión cerrada exitosamente', 'login')
    return redirect(url_for('auth.login'))

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        if current_user.rol == 2:
            return redirect(url_for('provedores.index'))
        return redirect(url_for('pizzas.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash("Todos los campos son requeridos", "registro")
            return redirect(url_for('auth.registro'))
            
        user = User.create_user(username, password, rol=1)
        if user:
            flash("Usuario registrado exitosamente. Por favor inicia sesión.", "registro")
            return redirect(url_for('auth.login'))
        else:
            flash("El nombre de usuario ya existe", "registro")
    
    return render_template('registro.html')