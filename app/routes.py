import json
import os

from flask import Blueprint, jsonify, request, render_template
from app import db
from app.models import (
    User, Post,
    TeamMember, Project, ProjectTeam, ProjectImage, ProjectLink,
    Task, Subtask
)
from datetime import datetime

bp = Blueprint('main', __name__)

# ============= Basic Routes =============

@bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@bp.route('/about')
def about():
    return jsonify({
        'app': 'Flask Docker App',
        'version': '1.0.0',
        'description': 'A Flask application running in Docker'
    })

@bp.route('/api/backup', methods=['GET', 'POST', 'PUT'])
def backup_endpoint():
    """Manage backup data in PostgreSQL database"""
    
    if request.method == 'GET':
        # Read all data from database
        try:

            
            # Get all team members
            team_members = TeamMember.query.all()
            team_members_data = [member.to_dict() for member in team_members]
            
            # Get all projects with tasks, images, links, team
            projects = Project.query.order_by(Project.starred.desc(), Project.created_at.desc()).all()
            projects_data = [project.to_dict(include_tasks=True) for project in projects]
            
            # Return data in backup format
            backup_data = {
                'teamMembers': team_members_data,
                'projects': projects_data,
                'exportDate': datetime.utcnow().isoformat(),
                'version': '2.5.0'
            }
            
            return jsonify(backup_data), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        # Replace entire database with new data (same as import)
        try:

            
            new_data = request.get_json()
            
            if not new_data:
                return jsonify({'error': 'No data provided'}), 400
            
            if 'teamMembers' not in new_data or 'projects' not in new_data:
                return jsonify({'error': 'Invalid data format. Expected teamMembers and projects'}), 400
            
            # Clear existing data
            Subtask.query.delete()
            Task.query.delete()
            ProjectLink.query.delete()
            ProjectImage.query.delete()
            ProjectTeam.query.delete()
            Project.query.delete()
            TeamMember.query.delete()
            
            # Import team members
            for member_data in new_data['teamMembers']:
                member = TeamMember(
                    name=member_data['name'],
                    role=member_data['role'],
                    skills=member_data.get('skills', []),
                    workload=member_data.get('workload', 0)
                )
                db.session.add(member)
            
            db.session.flush()
            
            # Import projects
            for project_data in new_data['projects']:
                project = Project(
                    name=project_data['name'],
                    description=project_data.get('description', ''),
                    status=project_data.get('status', 'planning'),
                    starred=project_data.get('starred', False),
                    meeting_minutes=project_data.get('meetingMinutes', '')
                )
                db.session.add(project)
                db.session.flush()
                
                # Import project team
                for member_name in project_data.get('team', []):
                    pt = ProjectTeam(project_id=project.id, member_name=member_name)
                    db.session.add(pt)
                
                # Import project images
                for image_data in project_data.get('images', []):
                    img = ProjectImage(
                        project_id=project.id,
                        image_data=image_data.get('image_data', image_data) if isinstance(image_data, dict) else image_data
                    )
                    db.session.add(img)
                
                # Import project links
                for link_data in project_data.get('links', []):
                    link = ProjectLink(
                        project_id=project.id,
                        url=link_data['url'],
                        label=link_data.get('label')
                    )
                    db.session.add(link)
                
                # Import tasks
                for task_data in project_data.get('tasks', []):
                    task = Task(
                        project_id=project.id,
                        text=task_data['text'],
                        completed=task_data.get('completed', False),
                        start_date=task_data.get('startDate'),
                        end_date=task_data.get('endDate'),
                        assignee_name=task_data.get('assignee')
                    )
                    db.session.add(task)
                    db.session.flush()
                    
                    # Import subtasks
                    for subtask_data in task_data.get('subtasks', []):
                        subtask = Subtask(
                            task_id=task.id,
                            text=subtask_data['text'],
                            completed=subtask_data.get('completed', False),
                            assignee_name=subtask_data.get('assignee')
                        )
                        db.session.add(subtask)
            
            db.session.commit()
            
            return jsonify({
                'message': 'Backup saved successfully to database',
                'timestamp': datetime.utcnow().isoformat(),
                'teamMembers': len(new_data['teamMembers']),
                'projects': len(new_data['projects'])
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'PUT':
        # Update/merge with existing database data
        try:

            
            new_data = request.get_json()
            
            if not new_data:
                return jsonify({'error': 'No data provided'}), 400
            
            updated_count = 0
            created_count = 0
            
            # Update or create team members
            if 'teamMembers' in new_data:
                for member_data in new_data['teamMembers']:
                    existing_member = TeamMember.query.filter_by(name=member_data['name']).first()
                    
                    if existing_member:
                        # Update existing
                        existing_member.role = member_data.get('role', existing_member.role)
                        existing_member.skills = member_data.get('skills', existing_member.skills)
                        existing_member.workload = member_data.get('workload', existing_member.workload)
                        updated_count += 1
                    else:
                        # Create new
                        new_member = TeamMember(
                            name=member_data['name'],
                            role=member_data['role'],
                            skills=member_data.get('skills', []),
                            workload=member_data.get('workload', 0)
                        )
                        db.session.add(new_member)
                        created_count += 1
            
            db.session.flush()
            
            # Update or create projects
            if 'projects' in new_data:
                for project_data in new_data['projects']:
                    existing_project = Project.query.filter_by(name=project_data['name']).first()
                    
                    if existing_project:
                        # Update existing project
                        existing_project.description = project_data.get('description', existing_project.description)
                        existing_project.status = project_data.get('status', existing_project.status)
                        existing_project.starred = project_data.get('starred', existing_project.starred)
                        existing_project.meeting_minutes = project_data.get('meetingMinutes', existing_project.meeting_minutes)
                        
                        # Update team members
                        ProjectTeam.query.filter_by(project_id=existing_project.id).delete()
                        for member_name in project_data.get('team', []):
                            pt = ProjectTeam(project_id=existing_project.id, member_name=member_name)
                            db.session.add(pt)
                        
                        # Update tasks
                        Task.query.filter_by(project_id=existing_project.id).delete()
                        for task_data in project_data.get('tasks', []):
                            task = Task(
                                project_id=existing_project.id,
                                text=task_data['text'],
                                completed=task_data.get('completed', False),
                                start_date=task_data.get('startDate'),
                                end_date=task_data.get('endDate'),
                                assignee_name=task_data.get('assignee')
                            )
                            db.session.add(task)
                            db.session.flush()
                            
                            # Add subtasks
                            for subtask_data in task_data.get('subtasks', []):
                                subtask = Subtask(
                                    task_id=task.id,
                                    text=subtask_data['text'],
                                    completed=subtask_data.get('completed', False),
                                    assignee_name=subtask_data.get('assignee')
                                )
                                db.session.add(subtask)
                        
                        updated_count += 1
                    else:
                        # Create new project
                        new_project = Project(
                            name=project_data['name'],
                            description=project_data.get('description', ''),
                            status=project_data.get('status', 'planning'),
                            starred=project_data.get('starred', False),
                            meeting_minutes=project_data.get('meetingMinutes', '')
                        )
                        db.session.add(new_project)
                        db.session.flush()
                        
                        # Add team
                        for member_name in project_data.get('team', []):
                            pt = ProjectTeam(project_id=new_project.id, member_name=member_name)
                            db.session.add(pt)
                        
                        # Add images
                        for image_data in project_data.get('images', []):
                            img = ProjectImage(
                                project_id=new_project.id,
                                image_data=image_data.get('image_data', image_data) if isinstance(image_data, dict) else image_data
                            )
                            db.session.add(img)
                        
                        # Add links
                        for link_data in project_data.get('links', []):
                            link = ProjectLink(
                                project_id=new_project.id,
                                url=link_data['url'],
                                label=link_data.get('label')
                            )
                            db.session.add(link)
                        
                        # Add tasks
                        for task_data in project_data.get('tasks', []):
                            task = Task(
                                project_id=new_project.id,
                                text=task_data['text'],
                                completed=task_data.get('completed', False),
                                start_date=task_data.get('startDate'),
                                end_date=task_data.get('endDate'),
                                assignee_name=task_data.get('assignee')
                            )
                            db.session.add(task)
                            db.session.flush()
                            
                            # Add subtasks
                            for subtask_data in task_data.get('subtasks', []):
                                subtask = Subtask(
                                    task_id=task.id,
                                    text=subtask_data['text'],
                                    completed=subtask_data.get('completed', False),
                                    assignee_name=subtask_data.get('assignee')
                                )
                                db.session.add(subtask)
                        
                        created_count += 1
            
            db.session.commit()
            
            return jsonify({
                'message': 'Backup merged successfully with database',
                'timestamp': datetime.utcnow().isoformat(),
                'updated': updated_count,
                'created': created_count
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@bp.route('/api/data', methods=['GET'])
def get_json_data():
    """Get data from PostgreSQL database (IT Resource Manager format)"""
    try:

        
        # Get all team members with their projects
        team_members = TeamMember.query.all()
        team_members_data = []
        
        for member in team_members:
            member_dict = member.to_dict()
            team_members_data.append(member_dict)
        
        # Get all projects with tasks, images, links, team
        projects = Project.query.order_by(Project.starred.desc(), Project.created_at.desc()).all()
        projects_data = []
        
        for project in projects:
            project_dict = project.to_dict(include_tasks=True)
            projects_data.append(project_dict)
        
        # Return data in the same format as the JSON file
        return jsonify({
            'teamMembers': team_members_data,
            'projects': projects_data,
            'exportDate': datetime.utcnow().isoformat(),
            'version': '2.5.0'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============= User Routes (CRUD) =============

@bp.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    try:
        users = User.query.all()
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user"""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200

@bp.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        
        # Validation
        if not data or not data.get('username') or not data.get('email'):
            return jsonify({'error': 'Username and email are required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        user = User(
            username=data['username'],
            email=data['email']
        )
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update a user"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    try:
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============= Post Routes (CRUD) =============

@bp.route('/api/posts', methods=['GET'])
def get_posts():
    """Get all posts with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pagination = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'posts': [post.to_dict() for post in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@bp.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """Get a specific post"""
    post = Post.query.get_or_404(post_id)
    return jsonify(post.to_dict()), 200

@bp.route('/api/posts', methods=['POST'])
def create_post():
    """Create a new post"""
    try:
        data = request.get_json()
        
        if not data or not data.get('title') or not data.get('content'):
            return jsonify({'error': 'Title and content are required'}), 400
        
        post = Post(
            title=data['title'],
            content=data['content'],
            user_id=data.get('user_id')
        )
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'message': 'Post created successfully',
            'post': post.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    """Update a post"""
    try:
        post = Post.query.get_or_404(post_id)
        data = request.get_json()
        
        if 'title' in data:
            post.title = data['title']
        if 'content' in data:
            post.content = data['content']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Post updated successfully',
            'post': post.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """Delete a post"""
    try:
        post = Post.query.get_or_404(post_id)
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': 'Post deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============= Search & Filter Routes =============

@bp.route('/api/search', methods=['GET'])
def search():
    """Search posts by title or content"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    
    posts = Post.query.filter(
        (Post.title.ilike(f'%{query}%')) | 
        (Post.content.ilike(f'%{query}%'))
    ).all()
    
    return jsonify({
        'query': query,
        'results': [post.to_dict() for post in posts],
        'count': len(posts)
    }), 200

@bp.route('/api/users/<int:user_id>/posts', methods=['GET'])
def get_user_posts(user_id):
    """Get all posts by a specific user"""
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user_id).all()
    
    return jsonify({
        'user': user.to_dict(),
        'posts': [post.to_dict() for post in posts],
        'count': len(posts)
    }), 200

# ============= File Upload Route =============

@bp.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload a file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save file (you should add proper validation and security checks)
    filename = file.filename
    # file.save(os.path.join('uploads', filename))
    
    return jsonify({
        'message': 'File uploaded successfully',
        'filename': filename
    }), 201

# ============= Stats & Analytics Routes =============

@bp.route('/api/stats', methods=['GET'])
def get_stats():
    """Get application statistics"""
    total_users = User.query.count()
    total_posts = Post.query.count()
    
    return jsonify({
        'total_users': total_users,
        'total_posts': total_posts,
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# ============= IT Resource Manager API Routes =============

# Team Members Routes
@bp.route('/api/team-members', methods=['GET'])
def get_team_members():
    """Get all team members with their projects"""
    try:

        team_members = TeamMember.query.all()
        return jsonify([member.to_dict() for member in team_members]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/team-members', methods=['POST'])
def create_team_member():
    """Create a new team member"""
    try:

        data = request.get_json()
        
        if not data or not data.get('name') or not data.get('role'):
            return jsonify({'error': 'Name and role are required'}), 400
        
        # Check if member already exists
        if TeamMember.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Team member with this name already exists'}), 409
        
        member = TeamMember(
            name=data['name'],
            role=data['role'],
            skills=data.get('skills', []),
            workload=data.get('workload', 0)
        )
        
        db.session.add(member)
        db.session.commit()
        
        return jsonify(member.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/team-members/<int:member_id>', methods=['PUT'])
def update_team_member(member_id):
    """Update a team member"""
    try:

        member = TeamMember.query.get_or_404(member_id)
        data = request.get_json()
        
        if 'name' in data:
            member.name = data['name']
        if 'role' in data:
            member.role = data['role']
        if 'skills' in data:
            member.skills = data['skills']
        if 'workload' in data:
            member.workload = data['workload']
        
        db.session.commit()
        return jsonify(member.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/team-members/<int:member_id>', methods=['DELETE'])
def delete_team_member(member_id):
    """Delete a team member"""
    try:

        member = TeamMember.query.get_or_404(member_id)
        db.session.delete(member)
        db.session.commit()
        return jsonify({'message': 'Team member deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Projects Routes
@bp.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects with tasks, images, links, and team"""
    try:

        projects = Project.query.order_by(Project.starred.desc(), Project.created_at.desc()).all()
        return jsonify([project.to_dict() for project in projects]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    try:

        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'error': 'Project name is required'}), 400
        
        if Project.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Project with this name already exists'}), 409
        
        # Parse delivery date if provided
        delivery_date = None
        if data.get('deliveryDate'):
            try:
                from datetime import datetime as dt
                delivery_date = dt.fromisoformat(data['deliveryDate'].replace('Z', '+00:00')).date()
            except:
                pass
        
        project = Project(
            name=data['name'],
            description=data.get('description', ''),
            status=data.get('status', 'planning'),
            starred=data.get('starred', False),
            meeting_minutes=data.get('meetingMinutes', ''),
            channels=data.get('channels', []),  # Support channels on creation
            applications=data.get('applications', []),  # New: support applications on creation
            delivery_date=delivery_date  # New: support delivery date on creation
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify(project.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Update a project"""
    try:

        project = Project.query.get_or_404(project_id)
        data = request.get_json()
        
        if 'name' in data:
            project.name = data['name']
        if 'description' in data:
            project.description = data['description']
        if 'status' in data:
            project.status = data['status']
        if 'starred' in data:
            project.starred = data['starred']
        if 'meetingMinutes' in data:
            project.meeting_minutes = data['meetingMinutes']
        if 'channels' in data:
            project.channels = data['channels']  # Handle channels
        if 'applications' in data:
            project.applications = data['applications']  # New: handle applications
        if 'deliveryDate' in data:
            # Parse delivery date
            if data['deliveryDate']:
                try:
                    from datetime import datetime as dt
                    project.delivery_date = dt.fromisoformat(data['deliveryDate'].replace('Z', '+00:00')).date()
                except:
                    project.delivery_date = None
            else:
                project.delivery_date = None
        
        # Handle tasks if provided (full replacement)
        if 'tasks' in data:
            # Remove all existing tasks for this project
            Task.query.filter_by(project_id=project_id).delete()
            
            # Add new tasks from data
            for task_data in data['tasks']:
                task = Task(
                    project_id=project_id,
                    text=task_data.get('text', ''),
                    completed=task_data.get('completed', False),
                    start_date=task_data.get('startDate'),
                    end_date=task_data.get('endDate'),
                    assignee_name=task_data.get('assignee')
                )
                db.session.add(task)
                db.session.flush()  # Get task ID
                
                # Handle subtasks if present
                if 'subtasks' in task_data and task_data['subtasks']:
                    for subtask_data in task_data['subtasks']:
                        subtask = Subtask(
                            task_id=task.id,
                            text=subtask_data.get('text', ''),
                            completed=subtask_data.get('completed', False),
                            assignee_name=subtask_data.get('assignee')
                        )
                        db.session.add(subtask)
        
        db.session.commit()
        return jsonify(project.to_dict(include_tasks=True)), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project (cascades to tasks, images, links)"""
    try:

        project = Project.query.get_or_404(project_id)
        db.session.delete(project)
        db.session.commit()
        return jsonify({'message': 'Project deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Project Team Routes
@bp.route('/api/projects/<int:project_id>/team', methods=['POST'])
def add_team_member_to_project(project_id):
    """Add a team member to a project"""
    try:

        project = Project.query.get_or_404(project_id)
        data = request.get_json()
        
        member_name = data.get('member_name')
        if not member_name:
            return jsonify({'error': 'member_name is required'}), 400
        
        # Check if member exists
        member = TeamMember.query.filter_by(name=member_name).first()
        if not member:
            return jsonify({'error': 'Team member not found'}), 404
        
        # Add to project team (will be ignored if already exists due to unique constraint)
        project_team = ProjectTeam(project_id=project_id, member_name=member_name)
        db.session.add(project_team)
        db.session.commit()
        
        # Update member workload
        member.workload = min(len(member.project_teams) * 25, 100)
        db.session.commit()
        
        return jsonify({'message': 'Team member added to project'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/projects/<int:project_id>/team/<string:member_name>', methods=['DELETE'])
def remove_team_member_from_project(project_id, member_name):
    """Remove a team member from a project"""
    try:

        
        ProjectTeam.query.filter_by(
            project_id=project_id,
            member_name=member_name
        ).delete()
        
        db.session.commit()
        
        # Update member workload
        member = TeamMember.query.filter_by(name=member_name).first()
        if member:
            member.workload = min(len(member.project_teams) * 25, 100)
            db.session.commit()
        
        return jsonify({'message': 'Team member removed from project'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Project Images Routes
@bp.route('/api/projects/<int:project_id>/images', methods=['POST'])
def add_project_image(project_id):
    """Add an image to a project"""
    try:

        project = Project.query.get_or_404(project_id)
        data = request.get_json()
        
        if not data or not data.get('image_data'):
            return jsonify({'error': 'image_data is required'}), 400
        
        image = ProjectImage(
            project_id=project_id,
            image_data=data['image_data']
        )
        
        db.session.add(image)
        db.session.commit()
        
        return jsonify(image.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/projects/<int:project_id>/images/<int:image_id>', methods=['DELETE'])
def delete_project_image(project_id, image_id):
    """Delete a project image"""
    try:

        image = ProjectImage.query.filter_by(id=image_id, project_id=project_id).first_or_404()
        db.session.delete(image)
        db.session.commit()
        return jsonify({'message': 'Image deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Tasks Routes
@bp.route('/api/projects/<int:project_id>/tasks', methods=['POST'])
def create_task(project_id):
    """Create a new task"""
    try:

        project = Project.query.get_or_404(project_id)
        data = request.get_json()
        
        if not data or not data.get('text'):
            return jsonify({'error': 'Task text is required'}), 400
        
        task = Task(
            project_id=project_id,
            text=data['text'],
            completed=data.get('completed', False),
            start_date=data.get('startDate'),
            end_date=data.get('endDate'),
            assignee_name=data.get('assignee')
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify(task.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task"""
    try:

        task = Task.query.get_or_404(task_id)
        data = request.get_json()
        
        if 'text' in data:
            task.text = data['text']
        if 'completed' in data:
            task.completed = data['completed']
        if 'startDate' in data:
            task.start_date = data['startDate']
        if 'endDate' in data:
            task.end_date = data['endDate']
        if 'assignee' in data:
            task.assignee_name = data['assignee']
        
        db.session.commit()
        return jsonify(task.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    try:

        task = Task.query.get_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Subtasks Routes
@bp.route('/api/tasks/<int:task_id>/subtasks', methods=['POST'])
def create_subtask(task_id):
    """Create a new subtask"""
    try:

        task = Task.query.get_or_404(task_id)
        data = request.get_json()
        
        if not data or not data.get('text'):
            return jsonify({'error': 'Subtask text is required'}), 400
        
        subtask = Subtask(
            task_id=task_id,
            text=data['text'],
            completed=data.get('completed', False),
            assignee_name=data.get('assignee')
        )
        
        db.session.add(subtask)
        db.session.commit()
        
        return jsonify(subtask.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/subtasks/<int:subtask_id>', methods=['PUT'])
def update_subtask(subtask_id):
    """Update a subtask"""
    try:

        subtask = Subtask.query.get_or_404(subtask_id)
        data = request.get_json()
        
        if 'text' in data:
            subtask.text = data['text']
        if 'completed' in data:
            subtask.completed = data['completed']
        if 'assignee' in data:
            subtask.assignee_name = data['assignee']
        
        db.session.commit()
        return jsonify(subtask.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/subtasks/<int:subtask_id>', methods=['DELETE'])
def delete_subtask(subtask_id):
    """Delete a subtask"""
    try:

        subtask = Subtask.query.get_or_404(subtask_id)
        db.session.delete(subtask)
        db.session.commit()
        return jsonify({'message': 'Subtask deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Data Import Route
@bp.route('/api/import', methods=['POST'])
def import_data():
    """Import data from JSON export to PostgreSQL"""
    try:

        
        data = request.get_json()
        
        if not data or 'teamMembers' not in data or 'projects' not in data:
            return jsonify({'error': 'Invalid data format'}), 400
        
        # Clear existing data
        Subtask.query.delete()
        Task.query.delete()
        ProjectLink.query.delete()
        ProjectImage.query.delete()
        ProjectTeam.query.delete()
        Project.query.delete()
        TeamMember.query.delete()
        
        # Import team members
        for member_data in data['teamMembers']:
            member = TeamMember(
                name=member_data['name'],
                role=member_data['role'],
                skills=member_data.get('skills', []),
                workload=member_data.get('workload', 0)
            )
            db.session.add(member)
        
        db.session.flush()
        
        # Import projects
        for project_data in data['projects']:
            project = Project(
                name=project_data['name'],
                description=project_data.get('description', ''),
                status=project_data.get('status', 'planning'),
                starred=project_data.get('starred', False),
                meeting_minutes=project_data.get('meetingMinutes', '')
            )
            db.session.add(project)
            db.session.flush()
            
            # Import project team
            for member_name in project_data.get('team', []):
                pt = ProjectTeam(project_id=project.id, member_name=member_name)
                db.session.add(pt)
            
            # Import project images
            for image_data in project_data.get('images', []):
                img = ProjectImage(
                    project_id=project.id,
                    image_data=image_data.get('image_data', image_data) if isinstance(image_data, dict) else image_data
                )
                db.session.add(img)
            
            # Import project links
            for link_data in project_data.get('links', []):
                link = ProjectLink(
                    project_id=project.id,
                    url=link_data['url'],
                    label=link_data.get('label')
                )
                db.session.add(link)
            
            # Import tasks
            for task_data in project_data.get('tasks', []):
                task = Task(
                    project_id=project.id,
                    text=task_data['text'],
                    completed=task_data.get('completed', False),
                    start_date=task_data.get('startDate'),
                    end_date=task_data.get('endDate'),
                    assignee_name=task_data.get('assignee')
                )
                db.session.add(task)
                db.session.flush()
                
                # Import subtasks
                for subtask_data in task_data.get('subtasks', []):
                    subtask = Subtask(
                        task_id=task.id,
                        text=subtask_data['text'],
                        completed=subtask_data.get('completed', False),
                        assignee_name=subtask_data.get('assignee')
                    )
                    db.session.add(subtask)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Data imported successfully',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============= Error Handlers =============

@bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500