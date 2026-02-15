import json
import os

from flask import Blueprint, jsonify, request, render_template
from app import db
from app.models import User, Post  # We'll create these models next
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
    """Manage backup data in JSON file"""
    json_file_path = os.path.join(os.path.dirname(__file__), '..', 'it-resource-manager-backup.json')
    
    if not os.path.exists(json_file_path):
        json_file_path = '/app/it-resource-manager-backup.json'
    
    if request.method == 'GET':
        # Read data
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)
            return jsonify(data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        # Replace entire file with new data
        try:
            new_data = request.get_json()
            
            if not new_data:
                return jsonify({'error': 'No data provided'}), 400
            
            with open(json_file_path, 'w') as file:
                json.dump(new_data, file, indent=2)
            
            return jsonify({
                'message': 'Backup saved successfully',
                'timestamp': datetime.utcnow().isoformat()
            }), 201
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'PUT':
        # Update/merge with existing data
        try:
            new_data = request.get_json()
            
            if not new_data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Read existing data
            try:
                with open(json_file_path, 'r') as file:
                    existing_data = json.load(file)
            except FileNotFoundError:
                existing_data = {}
            
            # Merge new data with existing
            existing_data.update(new_data)
            
            # Write merged data back
            with open(json_file_path, 'w') as file:
                json.dump(existing_data, file, indent=2)
            
            return jsonify({
                'message': 'Backup updated successfully',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@bp.route('/api/data', methods=['GET'])
def get_json_data():
    """Get data from JSON file"""
    try:
        # Path to your JSON file
        json_file_path = os.path.join(os.path.dirname(__file__), '..', 'it-resource-manager-backup.json')
        
        # Read the JSON file
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        
        return jsonify(data), 200
    except FileNotFoundError:
        return jsonify({'error': 'Data file not found'}), 404
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON format'}), 400
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

# ============= Error Handlers =============

@bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500