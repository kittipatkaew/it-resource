"""
Database Migration: Add Channels Column to Projects Table
Run this to add the channels field to existing projects table
"""

from app import app, db
from sqlalchemy import text

def migrate_add_channels():
    """Add channels column to projects table"""
    with app.app_context():
        try:
            # Add channels column using raw SQL with text() wrapper
            db.session.execute(text('''
                ALTER TABLE projects 
                ADD COLUMN IF NOT EXISTS channels TEXT[]
            '''))
            
            # Set default empty array for existing projects
            db.session.execute(text('''
                UPDATE projects 
                SET channels = ARRAY[]::TEXT[]
                WHERE channels IS NULL
            '''))
            
            db.session.commit()
            
            print("✅ Migration successful!")
            print("   - Added 'channels' column to projects table")
            print("   - Set default empty array for existing projects")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {e}")
            print("\nIf the column already exists, this is expected.")

if __name__ == '__main__':
    print("="*60)
    print("Database Migration: Add Channels to Projects")
    print("="*60)
    print()
    
    migrate_add_channels()
    
    print()
    print("="*60)
    print("Migration complete!")
    print("="*60)