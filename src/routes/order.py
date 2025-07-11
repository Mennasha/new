from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.order import Order, OrderItem
from src.models.cart import Cart, CartItem
from src.models.product import Product
from datetime import datetime
import uuid

order_bp = Blueprint('order', __name__)

def generate_order_number():
    """Generate unique order number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = str(uuid.uuid4())[:8].upper()
    return f"ORD-{timestamp}-{random_suffix}"

@order_bp.route('/orders', methods=['POST'])
def create_order():
    """Create new order from cart"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        
        if not user_id and not session_id:
            return jsonify({'success': False, 'error': 'User ID or Session ID required'}), 400
        
        # Get cart
        if user_id:
            cart = Cart.query.filter_by(user_id=user_id).first()
        else:
            cart = Cart.query.filter_by(session_id=session_id).first()
        
        if not cart or not cart.items:
            return jsonify({'success': False, 'error': 'Cart is empty'}), 400
        
        # Validate stock for all items
        for item in cart.items:
            if item.product.stock_quantity < item.quantity:
                return jsonify({
                    'success': False, 
                    'error': f'Insufficient stock for {item.product.name}'
                }), 400
        
        # Calculate totals
        subtotal = sum(item.quantity * item.product.price for item in cart.items)
        shipping_cost = data.get('shipping_cost', 0)
        tax_amount = data.get('tax_amount', 0)
        discount_amount = data.get('discount_amount', 0)
        total_amount = subtotal + shipping_cost + tax_amount - discount_amount
        
        # Create order
        order = Order(
            order_number=generate_order_number(),
            user_id=user_id,
            total_amount=total_amount,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            payment_method=data.get('payment_method'),
            shipping_name=data.get('shipping_name'),
            shipping_phone=data.get('shipping_phone'),
            shipping_email=data.get('shipping_email'),
            shipping_address=data.get('shipping_address'),
            shipping_city=data.get('shipping_city'),
            shipping_country=data.get('shipping_country'),
            shipping_postal_code=data.get('shipping_postal_code')
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for cart_item in cart.items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.price,
                size=cart_item.size,
                custom_engraving=cart_item.custom_engraving
            )
            db.session.add(order_item)
            
            # Update product stock
            cart_item.product.stock_quantity -= cart_item.quantity
        
        # Clear cart
        CartItem.query.filter_by(cart_id=cart.id).delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order': order.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@order_bp.route('/orders', methods=['GET'])
def get_orders():
    """Get orders (with pagination)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        user_id = request.args.get('user_id', type=int)
        status = request.args.get('status')
        
        query = Order.query
        
        if user_id:
            query = query.filter(Order.user_id == user_id)
        if status:
            query = query.filter(Order.status == status)
        
        orders = query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'orders': [order.to_dict() for order in orders.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': orders.total,
                'pages': orders.pages,
                'has_next': orders.has_next,
                'has_prev': orders.has_prev
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@order_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get single order by ID"""
    try:
        order = Order.query.get_or_404(order_id)
        
        return jsonify({
            'success': True,
            'order': order.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@order_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status (Admin only)"""
    try:
        order = Order.query.get_or_404(order_id)
        data = request.get_json()
        
        new_status = data.get('status')
        if new_status not in ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
        
        order.status = new_status
        
        # Update tracking info if provided
        if 'tracking_number' in data:
            order.tracking_number = data['tracking_number']
        if 'estimated_delivery' in data:
            order.estimated_delivery = datetime.fromisoformat(data['estimated_delivery'])
        
        # Set delivered timestamp if status is delivered
        if new_status == 'delivered':
            order.delivered_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order': order.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@order_bp.route('/orders/<int:order_id>/payment', methods=['PUT'])
def update_payment_status(order_id):
    """Update payment status"""
    try:
        order = Order.query.get_or_404(order_id)
        data = request.get_json()
        
        new_payment_status = data.get('payment_status')
        if new_payment_status not in ['pending', 'paid', 'failed', 'refunded']:
            return jsonify({'success': False, 'error': 'Invalid payment status'}), 400
        
        order.payment_status = new_payment_status
        
        # If payment is confirmed, update order status
        if new_payment_status == 'paid' and order.status == 'pending':
            order.status = 'confirmed'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order': order.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@order_bp.route('/orders/<order_number>/track', methods=['GET'])
def track_order(order_number):
    """Track order by order number"""
    try:
        order = Order.query.filter_by(order_number=order_number).first_or_404()
        
        return jsonify({
            'success': True,
            'order': {
                'order_number': order.order_number,
                'status': order.status,
                'payment_status': order.payment_status,
                'tracking_number': order.tracking_number,
                'estimated_delivery': order.estimated_delivery.isoformat() if order.estimated_delivery else None,
                'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
                'created_at': order.created_at.isoformat() if order.created_at else None
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@order_bp.route('/orders/stats', methods=['GET'])
def get_order_stats():
    """Get order statistics (Admin only)"""
    try:
        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status='pending').count()
        confirmed_orders = Order.query.filter_by(status='confirmed').count()
        processing_orders = Order.query.filter_by(status='processing').count()
        shipped_orders = Order.query.filter_by(status='shipped').count()
        delivered_orders = Order.query.filter_by(status='delivered').count()
        cancelled_orders = Order.query.filter_by(status='cancelled').count()
        
        total_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(
            Order.payment_status == 'paid'
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'confirmed_orders': confirmed_orders,
                'processing_orders': processing_orders,
                'shipped_orders': shipped_orders,
                'delivered_orders': delivered_orders,
                'cancelled_orders': cancelled_orders,
                'total_revenue': total_revenue
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

