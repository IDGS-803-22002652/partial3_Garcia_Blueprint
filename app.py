from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from models.models import db, User
from config import DevelopmentConfig

from controllers.auth import auth_bp
from controllers.pizzas import pizzas_bp
from controllers.provedores import provedores_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)
    
    csrf = CSRFProtect(app)
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(pizzas_bp)
    app.register_blueprint(provedores_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)