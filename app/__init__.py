from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    # For Cloud Run, we might not have a database initially
    # So we skip the connection check
    
    from app.routes import bp
    app.register_blueprint(bp)
    
    # Health check endpoint for Cloud Run
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'flask-app'}, 200
    
    # Root endpoint
    @app.route('/healthz')
    def healthz():
        return 'OK', 200
    
    return app