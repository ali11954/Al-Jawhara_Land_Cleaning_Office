from flask import Blueprint, request, jsonify
from auth import token_required
from models import db, Region, Location, Company

regions_bp = Blueprint('regions', __name__)


@regions_bp.route('/api/regions', methods=['GET'])
@token_required
def list_regions(current_user):
    regions = Region.query.all()
    return jsonify({'success': True, 'data': [r.to_dict() for r in regions]})


@regions_bp.route('/api/regions', methods=['POST'])
@token_required
def create_region(current_user):
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'success': False, 'message': 'name is required'}), 400
    r = Region(name=data['name'], company_id=data.get('company_id'))
    db.session.add(r)
    db.session.commit()
    return jsonify({'success': True, 'data': r.to_dict(), 'message': 'Region created'}), 201


@regions_bp.route('/api/regions/<int:region_id>', methods=['DELETE'])
@token_required
def delete_region(current_user, region_id):
    r = Region.query.get_or_404(region_id)
    db.session.delete(r)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Region deleted'})


@regions_bp.route('/api/locations', methods=['GET'])
@token_required
def list_locations(current_user):
    region_id = request.args.get('region_id', type=int)
    query = Location.query
    if region_id:
        query = query.filter_by(region_id=region_id)
    locations = query.all()
    return jsonify({'success': True, 'data': [l.to_dict() for l in locations]})


@regions_bp.route('/api/locations', methods=['POST'])
@token_required
def create_location(current_user):
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'success': False, 'message': 'name is required'}), 400
    l = Location(name=data['name'], region_id=data.get('region_id'), address=data.get('address', ''))
    db.session.add(l)
    db.session.commit()
    return jsonify({'success': True, 'data': l.to_dict(), 'message': 'Location created'}), 201


@regions_bp.route('/api/locations/<int:location_id>', methods=['DELETE'])
@token_required
def delete_location(current_user, location_id):
    l = Location.query.get_or_404(location_id)
    db.session.delete(l)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Location deleted'})
