from flask import Blueprint, request, jsonify
from auth import token_required
from db import get_db, fetch_all, execute
from datetime import datetime

work_plans_bp = Blueprint('work_plans', __name__)


TYPE_NAMES = {'daily': 'يومي', 'monthly': 'شهري', 'yearly': 'سنوي'}
STATUS_NAMES = {'pending': 'قيد الانتظار', 'in_progress': 'قيد التنفيذ', 'completed': 'مكتملة', 'cancelled': 'ملغاة'}

@work_plans_bp.route('/api/work-plans', methods=['GET'])
@token_required
def list_plans(current_user):
    with get_db() as conn:
        plans = fetch_all(conn, "SELECT * FROM work_plans ORDER BY created_at DESC")
        for p in plans:
            tasks = fetch_all(conn, "SELECT * FROM work_plan_tasks WHERE plan_id=%s", (p['id'],))
            p['tasks'] = tasks
            total = len(tasks)
            completed = sum(1 for t in tasks if t.get('is_completed'))
            p['tasks_count'] = total
            p['completed_tasks'] = completed
            p['progress'] = round((completed / total * 100)) if total > 0 else 0
            p['plan_type_name'] = TYPE_NAMES.get(p.get('plan_type', ''), p.get('plan_type', ''))
            p['status_name'] = STATUS_NAMES.get(p.get('status', ''), p.get('status', ''))
    return jsonify({'success': True, 'data': plans})


@work_plans_bp.route('/api/work-plans', methods=['POST'])
@token_required
def create_plan(current_user):
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'success': False, 'message': 'title is required'}), 400
    with get_db() as conn:
        pid = execute(conn,
            "INSERT INTO work_plans (title, description, plan_type, plan_date, company_id, region_id, location_id, assigned_to, status, created_by) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (data['title'], data.get('description', ''), data.get('plan_type', 'daily'), data.get('plan_date'),
             data.get('company_id'), data.get('region_id'),
             data.get('location_id'), data.get('assigned_to'), data.get('status', 'pending'), current_user.id))
        if pid and data.get('tasks'):
            for t in data['tasks']:
                if t.get('title'):
                    execute(conn,
                        "INSERT INTO work_plan_tasks (plan_id, title, description, assigned_to, priority) VALUES (%s,%s,%s,%s,%s)",
                        (pid, t['title'], t.get('description', ''), t.get('assigned_to'), t.get('priority', 'normal')))
    return jsonify({'success': True, 'data': {'id': pid}, 'message': 'Work plan created'}), 201


@work_plans_bp.route('/api/work-plans/<int:plan_id>', methods=['PUT'])
@token_required
def update_plan(current_user, plan_id):
    data = request.get_json()
    with get_db() as conn:
        fields, vals = [], []
        for f in ['title', 'description', 'company_id', 'region_id', 'location_id', 'assigned_to', 'status']:
            if f in data:
                fields.append(f'{f}=%s')
                vals.append(data[f])
        if fields:
            vals.append(plan_id)
            execute(conn, f"UPDATE work_plans SET {','.join(fields)} WHERE id=%s", vals)
    return jsonify({'success': True, 'message': 'Work plan updated'})


@work_plans_bp.route('/api/work-plans/<int:plan_id>', methods=['DELETE'])
@token_required
def delete_plan(current_user, plan_id):
    with get_db() as conn:
        execute(conn, "DELETE FROM work_plan_tasks WHERE plan_id=%s", (plan_id,))
        execute(conn, "DELETE FROM work_plans WHERE id=%s", (plan_id,))
    return jsonify({'success': True, 'message': 'Work plan deleted'})


@work_plans_bp.route('/api/work-plans/<int:plan_id>/tasks', methods=['POST'])
@token_required
def add_task(current_user, plan_id):
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'success': False, 'message': 'title is required'}), 400
    with get_db() as conn:
        tid = execute(conn, "INSERT INTO work_plan_tasks (plan_id, title, description, assigned_to, status) VALUES (%s,%s,%s,%s,%s) RETURNING id",
                      (plan_id, data['title'], data.get('description', ''), data.get('assigned_to'), data.get('status', 'pending')))
    return jsonify({'success': True, 'data': {'id': tid}, 'message': 'Task added'}), 201


@work_plans_bp.route('/api/work-plans/tasks/<int:task_id>', methods=['PUT'])
@token_required
def update_task(current_user, task_id):
    data = request.get_json()
    with get_db() as conn:
        fields, vals = [], []
        for f in ['title', 'description', 'assigned_to', 'status']:
            if f in data:
                fields.append(f'{f}=%s')
                vals.append(data[f])
        if fields:
            vals.append(task_id)
            execute(conn, f"UPDATE work_plan_tasks SET {','.join(fields)} WHERE id=%s", vals)
    return jsonify({'success': True, 'message': 'Task updated'})


@work_plans_bp.route('/api/work-plans/tasks/<int:task_id>', methods=['DELETE'])
@token_required
def delete_task(current_user, task_id):
    with get_db() as conn:
        execute(conn, "DELETE FROM work_plan_tasks WHERE id=%s", (task_id,))
    return jsonify({'success': True, 'message': 'Task deleted'})


@work_plans_bp.route('/api/work-plans/tasks/<int:task_id>/complete', methods=['POST'])
@token_required
def complete_task(current_user, task_id):
    data = request.get_json() or {}
    with get_db() as conn:
        cur = conn.cursor()
        execute(conn,
            "UPDATE work_plan_tasks SET is_completed=true, completed_at=%s, completed_by=%s, evaluation_score=%s, evaluation_notes=%s WHERE id=%s",
            (datetime.utcnow().isoformat(), current_user.id, data.get('evaluation_score'), data.get('evaluation_notes', ''), task_id))
        cur.execute("SELECT plan_id FROM work_plan_tasks WHERE id=%s", (task_id,))
        row = cur.fetchone()
        if row:
            plan_id = row[0]
            cur.execute("SELECT COUNT(*) FROM work_plan_tasks WHERE plan_id=%s", (plan_id,))
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM work_plan_tasks WHERE plan_id=%s AND is_completed=true", (plan_id,))
            done = cur.fetchone()[0]
            progress = round(done / total * 100) if total > 0 else 0
            execute(conn, "UPDATE work_plans SET progress=%s, status=%s WHERE id=%s",
                    (progress, 'completed' if done == total else 'in_progress' if done > 0 else 'pending', plan_id))
    return jsonify({'success': True, 'message': 'Task completed'})
