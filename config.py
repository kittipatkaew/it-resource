import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # For Cloud Run, use Cloud SQL or external database
    # Format: postgresql://user:password@/dbname?host=/cloudsql/project:region:instance
    
    #DATABASE_URL = os.environ.get('DATABASE_URL')

    # Get these from Environment Variables (Best Practice)
    DB_USER = os.environ.get("DB_USER") or 'postgres'
    DB_PASS = os.environ.get("DB_PASS") or 'nott5036673'
    DB_NAME = os.environ.get("DB_NAME") or 'it_resource_manager'
    # This is the "Connection Name" from the Cloud SQL Overview page
    INSTANCE_CONNECTION_NAME = os.environ.get("INSTANCE_CONNECTION_NAME") or 'project-9b468cf0-2a93-45dc-860:europe-west1:free-trial-first-project'

    # The format for Unix Sockets with Psycopg2:
    DATABASE_URL = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@/{DB_NAME}?"
        f"host=/cloudsql/{INSTANCE_CONNECTION_NAME}"
    )
    
    if DATABASE_URL:
        # Handle Cloud SQL Unix socket connection
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Fallback to SQLite for development
        SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'connect_args': {}
    }

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False