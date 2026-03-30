"""
城市管理 API
"""
from flask import Blueprint, request, jsonify
from models import db, City

city_bp = Blueprint('city', __name__)


@city_bp.route('', methods=['GET'])
def list_cities():
    """获取城市列表"""
    cities = City.query.order_by(City.id).all()
    return jsonify([c.to_dict() for c in cities])


@city_bp.route('', methods=['POST'])
def create_city():
    """新增城市"""
    data = request.get_json()
    name = data.get('name', '').strip()
    max_classrooms = data.get('max_classrooms', 99)
    
    if not name:
        return jsonify({'error': '城市名称不能为空'}), 400
    
    if City.query.filter_by(name=name).first():
        return jsonify({'error': f'城市 {name} 已存在'}), 400
    
    city = City(name=name, max_classrooms=max_classrooms)
    db.session.add(city)
    db.session.commit()
    return jsonify(city.to_dict()), 201


@city_bp.route('/<int:city_id>', methods=['PUT'])
def update_city(city_id):
    """修改城市"""
    city = City.query.get_or_404(city_id)
    data = request.get_json()
    
    if 'name' in data:
        new_name = data['name'].strip()
        if new_name and new_name != city.name:
            if City.query.filter_by(name=new_name).first():
                return jsonify({'error': f'城市 {new_name} 已存在'}), 400
            city.name = new_name
    
    if 'max_classrooms' in data:
        city.max_classrooms = data['max_classrooms']
    
    db.session.commit()
    return jsonify(city.to_dict())


@city_bp.route('/<int:city_id>', methods=['DELETE'])
def delete_city(city_id):
    """删除城市"""
    city = City.query.get_or_404(city_id)
    
    # 检查是否还有班级使用该城市
    if city.classes.count() > 0:
        return jsonify({'error': f'城市 {city.name} 下还有班级，无法删除'}), 400
    
    db.session.delete(city)
    db.session.commit()
    return jsonify({'message': f'城市 {city.name} 已删除'})
