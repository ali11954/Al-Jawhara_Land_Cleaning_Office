from flask import Blueprint, request, jsonify
from auth import token_required
from db import get_db, fetch_all, fetch_one, execute

regions_bp = Blueprint('regions', __name__)


@regions_bp.route('/api/regions', methods=['GET'])
@token_required
def list_regions(current_user):
    with get_db() as conn:
        rows = fetch_all(conn, "SELECT * FROM regions ORDER BY name")
    return jsonify({'success': True, 'data': rows})


@regions_bp.route('/api/regions', methods=['POST'])
@token_required
def create_region(current_user):
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'success': False, 'message': 'name is required'}), 400
    with get_db() as conn:
        rid = execute(conn, "INSERT INTO regions (name, company_id) VALUES (%s,%s) RETURNING id",
                      (data['name'], data.get('company_id')))
    return jsonify({'success': True, 'data': {'id': rid}, 'message': 'Region created'}), 201


@regions_bp.route('/api/regions/<int:region_id>', methods=['DELETE'])
@token_required
def delete_region(current_user, region_id):
    with get_db() as conn:
        execute(conn, "DELETE FROM regions WHERE id=%s", (region_id,))
    return jsonify({'success': True, 'message': 'Region deleted'})


@regions_bp.route('/api/locations', methods=['GET'])
@token_required
def list_locations(current_user):
    region_id = request.args.get('region_id', type=int)
    with get_db() as conn:
        if region_id:
            rows = fetch_all(conn, "SELECT * FROM locations WHERE region_id=%s ORDER BY name", (region_id,))
        else:
            rows = fetch_all(conn, "SELECT * FROM locations ORDER BY name")
    return jsonify({'success': True, 'data': rows})


@regions_bp.route('/api/locations', methods=['POST'])
@token_required
def create_location(current_user):
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'success': False, 'message': 'name is required'}), 400
    with get_db() as conn:
        lid = execute(conn, "INSERT INTO locations (name, region_id, address) VALUES (%s,%s,%s) RETURNING id",
                      (data['name'], data.get('region_id'), data.get('address', '')))
    return jsonify({'success': True, 'data': {'id': lid}, 'message': 'Location created'}), 201


@regions_bp.route('/api/locations/<int:location_id>', methods=['DELETE'])
@token_required
def delete_location(current_user, location_id):
    with get_db() as conn:
        execute(conn, "DELETE FROM locations WHERE id=%s", (location_id,))
    return jsonify({'success': True, 'message': 'Location deleted'})


@regions_bp.route('/api/regions/<int:region_id>/locations', methods=['GET'])
@token_required
def region_locations(current_user, region_id):
    with get_db() as conn:
        rows = fetch_all(conn, "SELECT * FROM locations WHERE region_id=%s ORDER BY name", (region_id,))
    return jsonify({'success': True, 'data': rows})
