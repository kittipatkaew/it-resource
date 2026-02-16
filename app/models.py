from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY, JSON

class TeamMember(db.Model):
    """Team Member model"""
    __tablename__ = 'team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    role = db.Column(db.String(100), nullable=False)
    skills = db.Column(ARRAY(db.String), default=[], nullable=False)
    workload = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project_teams = db.relationship('ProjectTeam', back_populates='member', cascade='all, delete-orphan')
    tasks = db.relationship('Task', foreign_keys='Task.assignee_name', back_populates='assignee')
    subtasks = db.relationship('Subtask', foreign_keys='Subtask.assignee_name', back_populates='assignee')
    
    def to_dict(self):
        # Get all projects this member is assigned to
        projects = [pt.project.name for pt in self.project_teams]
        
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'skills': self.skills,
            'workload': self.workload,
            'projects': projects,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Project(db.Model):
    """Project model"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='planning', nullable=False)
    starred = db.Column(db.Boolean, default=False)
    meeting_minutes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = db.relationship('ProjectImage', back_populates='project', cascade='all, delete-orphan')
    links = db.relationship('ProjectLink', back_populates='project', cascade='all, delete-orphan')
    project_teams = db.relationship('ProjectTeam', back_populates='project', cascade='all, delete-orphan')
    tasks = db.relationship('Task', back_populates='project', cascade='all, delete-orphan')
    
    def to_dict(self, include_tasks=True):
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'starred': self.starred,
            'meetingMinutes': self.meeting_minutes,
            'images': [img.to_dict() for img in self.images],
            'links': [link.to_dict() for link in self.links],
            'team': [pt.member.name for pt in self.project_teams],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_tasks:
            result['tasks'] = [task.to_dict() for task in self.tasks]
        
        return result

class ProjectImage(db.Model):
    """Project Image model"""
    __tablename__ = 'project_images'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    image_data = db.Column(db.Text, nullable=False)  # Base64 encoded
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', back_populates='images')
    
    def to_dict(self):
        return {
            'id': self.id,
            'image_data': self.image_data,
            'display_order': self.display_order
        }

class ProjectLink(db.Model):
    """Project Link model"""
    __tablename__ = 'project_links'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    url = db.Column(db.Text, nullable=False)
    label = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', back_populates='links')
    
    def to_dict(self):
        return {
            'url': self.url,
            'label': self.label
        }

class ProjectTeam(db.Model):
    """Project Team (Many-to-Many between Projects and Team Members)"""
    __tablename__ = 'project_team'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    member_name = db.Column(db.String(255), db.ForeignKey('team_members.name', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', back_populates='project_teams')
    member = db.relationship('TeamMember', back_populates='project_teams')
    
    __table_args__ = (
        db.UniqueConstraint('project_id', 'member_name', name='unique_project_member'),
    )

class Task(db.Model):
    """Task model"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    assignee_name = db.Column(db.String(255), db.ForeignKey('team_members.name', ondelete='SET NULL', onupdate='CASCADE'))
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', back_populates='tasks')
    assignee = db.relationship('TeamMember', foreign_keys=[assignee_name], back_populates='tasks')
    subtasks = db.relationship('Subtask', back_populates='task', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'completed': self.completed,
            'startDate': self.start_date.isoformat() if self.start_date else None,
            'endDate': self.end_date.isoformat() if self.end_date else None,
            'assignee': self.assignee_name,
            'subtasks': [subtask.to_dict() for subtask in self.subtasks]
        }

class Subtask(db.Model):
    """Subtask model"""
    __tablename__ = 'subtasks'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    assignee_name = db.Column(db.String(255), db.ForeignKey('team_members.name', ondelete='SET NULL', onupdate='CASCADE'))
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    task = db.relationship('Task', back_populates='subtasks')
    assignee = db.relationship('TeamMember', foreign_keys=[assignee_name], back_populates='subtasks')
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'completed': self.completed,
            'assignee': self.assignee_name
        }

# Keep existing User and Post models
class User(db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    posts = db.relationship('Post', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Post(db.Model):
    """Post model"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'user_id': self.user_id,
            'author': self.author.username if self.author else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }