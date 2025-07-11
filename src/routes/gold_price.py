from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.gold_price import GoldPrice, SizeGuide, AIFitting
from src.gold_price_service import gold_service
from datetime import datetime
import requests

gold_price_bp = Blueprint('gold_price', __name__)

@gold_price_bp.route('/gold-prices', methods=['GET'])
def get_gold_prices():
    """Get current gold prices"""
    try:
        # الحصول على الأسعار من الخدمة التلقائية
        live_prices = gold_service.get_current_prices()
        
        # محاولة الحصول على الأسعار من قاعدة البيانات أيضاً
        db_prices = GoldPrice.query.filter_by(is_active=True).all()
        
        return jsonify({
            'success': True,
            'live_prices': live_prices,
            'db_prices': [price.to_dict() for price in db_prices]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@gold_price_bp.route('/gold-prices/update', methods=['POST'])
def update_gold_prices():
    """Update gold prices (Admin only or automated)"""
    try:
        data = request.get_json()
        
        for price_data in data.get('prices', []):
            karat = price_data.get('karat')
            price_per_gram = price_data.get('price_per_gram')
            source = price_data.get('source', 'manual')
            
            # Find existing price or create new one
            gold_price = GoldPrice.query.filter_by(karat=karat).first()
            if gold_price:
                gold_price.price_per_gram = price_per_gram
                gold_price.source = source
                gold_price.last_updated = datetime.utcnow()
            else:
                gold_price = GoldPrice(
                    karat=karat,
                    price_per_gram=price_per_gram,
                    source=source
                )
                db.session.add(gold_price)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Gold prices updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@gold_price_bp.route('/gold-prices/fetch', methods=['POST'])
def fetch_gold_prices():
    """Fetch gold prices from external API (Admin only)"""
    try:
        # استخدام الخدمة التلقائية لجلب الأسعار
        updated_prices = gold_service.update_prices()
        
        # تحديث قاعدة البيانات بالأسعار الجديدة
        for karat, price in [('18k', updated_prices['karat18']), 
                            ('21k', updated_prices['karat21']), 
                            ('24k', updated_prices['karat24'])]:
            
            gold_price = GoldPrice.query.filter_by(karat=karat).first()
            if gold_price:
                gold_price.price_per_gram = price
                gold_price.source = 'api_auto'
                gold_price.last_updated = datetime.utcnow()
            else:
                gold_price = GoldPrice(
                    karat=karat,
                    price_per_gram=price,
                    source='api_auto'
                )
                db.session.add(gold_price)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Gold prices fetched and updated successfully',
            'prices': updated_prices
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@gold_price_bp.route('/gold-prices/auto-update/start', methods=['POST'])
def start_auto_update():
    """Start automatic gold price updates"""
    try:
        data = request.get_json()
        interval_minutes = data.get('interval_minutes', 30)  # افتراضي 30 دقيقة
        
        gold_service.start_auto_update(interval_minutes)
        
        return jsonify({
            'success': True,
            'message': f'Auto-update started with {interval_minutes} minutes interval'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@gold_price_bp.route('/gold-prices/live', methods=['GET'])
def get_live_prices():
    """Get live gold prices without database storage"""
    try:
        live_prices = gold_service.get_current_prices()
        
        return jsonify({
            'success': True,
            'prices': live_prices
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@gold_price_bp.route('/size-guide', methods=['GET'])
def get_size_guide():
    """Get size guide for jewelry"""
    try:
        category = request.args.get('category')
        
        query = SizeGuide.query.filter_by(is_active=True)
        if category:
            query = query.filter_by(category=category)
        
        sizes = query.order_by(SizeGuide.size_value.asc()).all()
        
        return jsonify({
            'success': True,
            'sizes': [size.to_dict() for size in sizes]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@gold_price_bp.route('/size-guide', methods=['POST'])
def create_size_guide():
    """Create size guide entry (Admin only)"""
    try:
        data = request.get_json()
        
        size_guide = SizeGuide(
            category=data.get('category'),
            size_name=data.get('size_name'),
            size_value=data.get('size_value'),
            description=data.get('description')
        )
        
        db.session.add(size_guide)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'size_guide': size_guide.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@gold_price_bp.route('/ai-fitting', methods=['POST'])
def ai_fitting():
    """AI-powered size fitting"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        category = data.get('category')  # ring, bracelet
        image_data = data.get('image_data')  # Base64 encoded image
        
        if not category or not image_data:
            return jsonify({'success': False, 'error': 'Category and image data required'}), 400
        
        # This is a placeholder for AI processing
        # In a real implementation, you would:
        # 1. Process the image using computer vision
        # 2. Detect hand/wrist measurements
        # 3. Calculate recommended size
        
        # Mock AI processing result
        mock_measurements = {
            'width': 18.5 if category == 'ring' else 16.2,
            'length': 20.1 if category == 'ring' else 18.8,
            'circumference': 58.2 if category == 'ring' else 165.4
        }
        
        if category == 'ring':
            recommended_size = 'M' if mock_measurements['circumference'] < 60 else 'L'
        else:  # bracelet
            recommended_size = 'S' if mock_measurements['circumference'] < 160 else 'M'
        
        confidence_score = 0.85  # Mock confidence
        
        # Save AI fitting result
        ai_fitting = AIFitting(
            user_id=user_id,
            session_id=session_id,
            category=category,
            measurements=mock_measurements,
            recommended_size=recommended_size,
            confidence_score=confidence_score
        )
        
        db.session.add(ai_fitting)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'fitting': ai_fitting.to_dict(),
            'message': f'Recommended size: {recommended_size} (Confidence: {int(confidence_score * 100)}%)'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@gold_price_bp.route('/ai-fitting/history', methods=['GET'])
def get_ai_fitting_history():
    """Get AI fitting history for user"""
    try:
        user_id = request.args.get('user_id', type=int)
        session_id = request.args.get('session_id')
        
        if not user_id and not session_id:
            return jsonify({'success': False, 'error': 'User ID or Session ID required'}), 400
        
        query = AIFitting.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        else:
            query = query.filter_by(session_id=session_id)
        
        fittings = query.order_by(AIFitting.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'fittings': [fitting.to_dict() for fitting in fittings]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

