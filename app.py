from flask import Flask, send_from_directory, jsonify, request, make_response
import os
import json
from typing import Tuple

app = Flask(__name__, static_folder='public')


def data_path() -> str:
    return os.path.join(app.static_folder, 'it-resource-manager-backup.json')


def load_data() -> dict:
    path = data_path()
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            return {'teamMembers': [], 'projects': []}
    return {'teamMembers': [], 'projects': []}


def save_data(data: dict) -> None:
    path = data_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def find_project(data: dict, project_name: str) -> Tuple[dict, int]:
    for i, p in enumerate(data.get('projects', [])):
        if p.get('name') == project_name:
            return p, i
    return None, -1


def find_member(data: dict, member_name: str) -> Tuple[dict, int]:
    for i, m in enumerate(data.get('teamMembers', [])):
        if m.get('name') == member_name:
            return m, i
    return None, -1


# Serve the main page
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


# Serve static files (JS/CSS/images)
@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)


# Allow simple CORS for local development
@app.after_request
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp


@app.route('/api/data', methods=['GET'])
def api_get_data():
    return jsonify(load_data())


@app.route('/api/backup', methods=['POST'])
def api_save_backup():
    payload = request.get_json()
    if not isinstance(payload, dict):
        return jsonify({'error': 'Invalid JSON payload'}), 400
    save_data(payload)
    return jsonify({'status': 'saved'})


### Team endpoints
@app.route('/api/teams', methods=['GET'])
def api_get_teams():
    return jsonify(load_data().get('teamMembers', []))


@app.route('/api/teams', methods=['POST'])
def api_create_team():
    payload = request.get_json() or {}
    if 'name' not in payload:
        return jsonify({'error': 'name is required'}), 400
    data = load_data()
    member, _ = find_member(data, payload['name'])
    if member:
        return jsonify({'error': 'member already exists'}), 409
    # set defaults
    member_obj = {
        'name': payload['name'],
        'role': payload.get('role', ''),
        'skills': payload.get('skills', []),
        'workload': payload.get('workload', 0),
        'projects': payload.get('projects', [])
    }
    data.setdefault('teamMembers', []).append(member_obj)
    save_data(data)
    return jsonify(member_obj), 201


@app.route('/api/teams/<string:name>', methods=['PUT'])
def api_update_team(name):
    payload = request.get_json() or {}
    data = load_data()
    member, idx = find_member(data, name)
    if not member:
        return jsonify({'error': 'member not found'}), 404
    # Update fields
    for k in ['name', 'role', 'skills', 'workload', 'projects']:
        if k in payload:
            member[k] = payload[k]

    # If name changed, update references in projects
    if payload.get('name') and payload.get('name') != name:
        old_name = name
        new_name = payload['name']
        for project in data.get('projects', []):
            project['team'] = [new_name if m == old_name else m for m in project.get('team', [])]
            for task in project.get('tasks', []):
                if task.get('assignee') == old_name:
                    task['assignee'] = new_name

    save_data(data)
    return jsonify(member)


@app.route('/api/teams/<string:name>', methods=['DELETE'])
def api_delete_team(name):
    data = load_data()
    member, idx = find_member(data, name)
    if not member:
        return jsonify({'error': 'member not found'}), 404
    # Remove from projects
    for project in data.get('projects', []):
        if name in project.get('team', []):
            project['team'] = [m for m in project.get('team', []) if m != name]
        for task in project.get('tasks', []):
            if task.get('assignee') == name:
                task['assignee'] = None

    data['teamMembers'] = [m for m in data.get('teamMembers', []) if m.get('name') != name]
    save_data(data)
    return jsonify({'status': 'deleted'})


### Project endpoints
@app.route('/api/projects', methods=['GET'])
def api_get_projects():
    return jsonify(load_data().get('projects', []))


@app.route('/api/projects', methods=['POST'])
def api_create_project():
    payload = request.get_json() or {}
    if 'name' not in payload:
        return jsonify({'error': 'name is required'}), 400
    data = load_data()
    project, _ = find_project(data, payload['name'])
    if project:
        return jsonify({'error': 'project already exists'}), 409
    project_obj = {
        'name': payload['name'],
        'status': payload.get('status', 'planning'),
        'description': payload.get('description', ''),
        'team': payload.get('team', []),
        'tasks': payload.get('tasks', []),
        'images': payload.get('images', []),
        'starred': payload.get('starred', False)
    }
    data.setdefault('projects', []).append(project_obj)
    # add project to members' project list if team provided
    for member_name in project_obj['team']:
        member, _ = find_member(data, member_name)
        if member and project_obj['name'] not in member.get('projects', []):
            member.setdefault('projects', []).append(project_obj['name'])

    save_data(data)
    return jsonify(project_obj), 201


@app.route('/api/projects/<string:name>', methods=['PUT'])
def api_update_project(name):
    payload = request.get_json() or {}
    data = load_data()
    project, idx = find_project(data, name)
    if not project:
        return jsonify({'error': 'project not found'}), 404
    old_name = project.get('name')
    for k in ['name', 'status', 'description', 'team', 'tasks', 'images', 'starred']:
        if k in payload:
            project[k] = payload[k]

    # if project renamed, update members
    if payload.get('name') and payload.get('name') != old_name:
        new_name = payload['name']
        for member in data.get('teamMembers', []):
            member['projects'] = [new_name if p == old_name else p for p in member.get('projects', [])]

    save_data(data)
    return jsonify(project)


@app.route('/api/projects/<string:name>', methods=['DELETE'])
def api_delete_project(name):
    data = load_data()
    project, idx = find_project(data, name)
    if not project:
        return jsonify({'error': 'project not found'}), 404
    # remove project from members
    for member in data.get('teamMembers', []):
        member['projects'] = [p for p in member.get('projects', []) if p != name]

    data['projects'] = [p for p in data.get('projects', []) if p.get('name') != name]
    save_data(data)
    return jsonify({'status': 'deleted'})


### Task endpoints
@app.route('/api/projects/<string:project_name>/tasks', methods=['POST'])
def api_add_task(project_name):
    payload = request.get_json() or {}
    data = load_data()
    project, _ = find_project(data, project_name)
    if not project:
        return jsonify({'error': 'project not found'}), 404
    task = {
        'id': payload.get('id') or int(json.dumps(payload, sort_keys=True).__hash__() & 0xffffffff),
        'text': payload.get('text', ''),
        'completed': payload.get('completed', False),
        'assignee': payload.get('assignee'),
        'startDate': payload.get('startDate'),
        'endDate': payload.get('endDate')
    }
    project.setdefault('tasks', []).append(task)
    save_data(data)
    return jsonify(task), 201


@app.route('/api/projects/<string:project_name>/tasks/<int:task_id>', methods=['PUT'])
def api_update_task(project_name, task_id):
    payload = request.get_json() or {}
    data = load_data()
    project, _ = find_project(data, project_name)
    if not project:
        return jsonify({'error': 'project not found'}), 404
    for t in project.get('tasks', []):
        if int(t.get('id')) == task_id:
            t.update(payload)
            save_data(data)
            return jsonify(t)
    return jsonify({'error': 'task not found'}), 404


@app.route('/api/projects/<string:project_name>/tasks/<int:task_id>', methods=['DELETE'])
def api_delete_task(project_name, task_id):
    data = load_data()
    project, _ = find_project(data, project_name)
    if not project:
        return jsonify({'error': 'project not found'}), 404
    tasks = project.get('tasks', [])
    new_tasks = [t for t in tasks if int(t.get('id')) != task_id]
    if len(new_tasks) == len(tasks):
        return jsonify({'error': 'task not found'}), 404
    project['tasks'] = new_tasks
    save_data(data)
    return jsonify({'status': 'deleted'})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
