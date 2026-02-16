"""
Flask PostgreSQL Migration Script
Creates all necessary tables for IT Resource Manager
"""

from app import app, db

def init_database():
    """Initialize database with all tables"""
    with app.app_context():
        print("Creating database tables...")
        
        # Import all models to ensure they're registered
        from app.models import (
            TeamMember, Project, ProjectImage, ProjectLink,
            ProjectTeam, Task, Subtask, User, Post
        )
        
        # Create all tables
        db.create_all()
        
        print("✓ Tables created successfully!")
        print("\nCreated tables:")
        print("  - team_members")
        print("  - projects")
        print("  - project_images")
        print("  - project_links")
        print("  - project_team")
        print("  - tasks")
        print("  - subtasks")
        print("  - users")
        print("  - posts")

if __name__ == '__main__':
    init_database()
