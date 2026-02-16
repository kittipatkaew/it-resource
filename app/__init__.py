from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database Configuration
    # Check if SQLALCHEMY_DATABASE_URI is set directly (supports SQLite or PostgreSQL)
    database_url = os.environ.get('SQLALCHEMY_DATABASE_URI')
    
    if database_url:
        # Use the direct connection string (works for SQLite or PostgreSQL)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Build PostgreSQL connection string from components
        db_user = os.environ.get('DB_USER', 'postgres')
        db_password = os.environ.get('DB_PASSWORD', '')
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '5432')
        db_name = os.environ.get('DB_NAME', 'it_resource_manager')
        
        # Check if we should use SQLite as fallback
        if not db_password and db_host == 'localhost':
            print("⚠ No database password set, using SQLite as fallback")
            database_url = 'sqlite:///it_resource_manager.db'
        else:
            database_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
        
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)  # Enable CORS for all routes
    
    # Register blueprints
    from app.routes import bp
    app.register_blueprint(bp)
    
    # Create tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
            print(f"✓ Database initialized: {database_url.split('@')[0]}@...")
        except Exception as e:
            print(f"⚠ Warning: Could not create tables - {e}")
            print("Please run: python setup_database.py")
    
    return app

# Create app instance (for backwards compatibility)
app = create_app()