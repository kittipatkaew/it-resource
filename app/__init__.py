from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
import time
import sys

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Wait for database to be ready
    with app.app_context():
        max_retries = 5
        retry_count = 0
        while retry_count < max_retries:
            try:
                db.engine.connect()
                print("Database connection successful!")
                break
            except Exception as e:
                retry_count += 1
                print(f"Database connection attempt {retry_count}/{max_retries} failed: {e}")
                if retry_count < max_retries:
                    time.sleep(2)
                else:
                    print("Could not connect to database after multiple attempts")
                    sys.exit(1)
    
    from app.routes import bp
    app.register_blueprint(bp)
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200
    
    return app