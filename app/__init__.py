
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)  
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    

    with app.app_context():
        from .models import User,Product
        from .routes import register_routes
        register_routes(app)
        
    return app