"""
Flask Application Runner
Run this file to start the IT Resource Manager server
"""

from app import app, db
import os

if __name__ == '__main__':
    # Create tables if they don't exist
    with app.app_context():
        try:
            print("Initializing database...")
            db.create_all()
            print("✓ Database initialized!")
        except Exception as e:
            print(f"⚠ Warning: Database initialization issue - {e}")
            print("Server will start anyway...")
    
    print("\n" + "="*50)
    print("IT Resource Manager Server")
    print("="*50)
    print("Server starting on:")
    print("  - http://localhost:5001")
    print("  - http://127.0.0.1:5001")
    print("\nAPI endpoints:")
    print("  - http://localhost:5001/api/data")
    print("  - http://localhost:5001/api/team-members")
    print("  - http://localhost:5001/api/projects")
    print("\nPress CTRL+C to stop")
    print("="*50 + "\n")
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 8080))
    
    # Run the application
    # Use 0.0.0.0 to allow external connections
    # Use debug=True for development
    app.run(
        host='0.0.0.0',  # Allow connections from any IP
        port=port,
        debug=True,
        use_reloader=True,
        threaded=True
    )