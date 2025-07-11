from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.cart import Cart, CartItem
from src.models.product import Product

cart_bp = Blueprint('cart', __name__)

def get_or_create_cart(user_id=None, session_id=None):
    """Get existing cart or create new one"""
    if user_id:
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.session.add(cart)
            db.session.commit()
    else:
        cart = Cart.query.filter_by(session_id=session_id).first()
        if not cart:
            cart = Cart(session_id=session_id)
            db.session.add(cart)
            db.session.commit()
    return cart

@cart_bp.route('/cart', methods=['GET'])
def get_cart():
    """Get user's cart"""
    try:
        user_id = request.args.get('user_id', type=int)
        session_id = request.args.get('session_id')
        
        if not user_id and not session_id:
            return jsonify({'success': False, 'error': 'User ID or Session ID required'}), 400
        
        cart = get_or_create_cart(user_id, session_id)
        
        return jsonify({
            'success': True,
            'cart': cart.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@cart_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Add item to cart"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        size = data.get('size')
        custom_engraving = data.get('custom_engraving')
        
        if not product_id:
            return jsonify({'success': False, 'error': 'Product ID required'}), 400
        
        if not user_id and not session_id:
            return jsonify({'success': False, 'error': 'User ID or Session ID required'}), 400
        
        # Check if product exists and is active
        product = Product.query.get(product_id)
        if not product or not product.is_active:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Check stock
        if product.stock_quantity < quantity:
            return jsonify({'success': False, 'error': 'Insufficient stock'}), 400
        
        cart = get_or_create_cart(user_id, session_id)
        
        # Check if item already exists in cart
        existing_item = CartItem.query.filter_by(
            cart_id=cart.id,
            product_id=product_id,
            size=size,
            custom_engraving=custom_engraving
        ).first()
        
        if existing_item:
            # Update quantity
            new_quantity = existing_item.quantity + quantity
            if product.stock_quantity < new_quantity:
                return jsonify({'success': False, 'error': 'Insufficient stock'}), 400
            existing_item.quantity = new_quantity
        else:
            # Create new cart item
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity,
                size=size,
                custom_engraving=custom_engraving
            )
            db.session.add(cart_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Item added to cart',
            'cart': cart.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@cart_bp.route('/cart/update', methods=['PUT'])
def update_cart_item():
    """Update cart item quantity"""
    try:
        data = request.get_json()
        cart_item_id = data.get('cart_item_id')
        quantity = data.get('quantity')
        
        if not cart_item_id or quantity is None:
            return jsonify({'success': False, 'error': 'Cart item ID and quantity required'}), 400
        
        cart_item = CartItem.query.get_or_404(cart_item_id)
        
        if quantity <= 0:
            # Remove item if quantity is 0 or negative
            db.session.delete(cart_item)
        else:
            # Check stock
            if cart_item.product.stock_quantity < quantity:
                return jsonify({'success': False, 'error': 'Insufficient stock'}), 400
            cart_item.quantity = quantity
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cart updated',
            'cart': cart_item.cart.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@cart_bp.route('/cart/remove', methods=['DELETE'])
def remove_from_cart():
    """Remove item from cart"""
    try:
        cart_item_id = request.args.get('cart_item_id', type=int)
        
        if not cart_item_id:
            return jsonify({'success': False, 'error': 'Cart item ID required'}), 400
        
        cart_item = CartItem.query.get_or_404(cart_item_id)
        cart = cart_item.cart
        
        db.session.delete(cart_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Item removed from cart',
            'cart': cart.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@cart_bp.route('/cart/clear', methods=['DELETE'])
def clear_cart():
    """Clear all items from cart"""
    try:
        user_id = request.args.get('user_id', type=int)
        session_id = request.args.get('session_id')
        
        if not user_id and not session_id:
            return jsonify({'success': False, 'error': 'User ID or Session ID required'}), 400
        
        if user_id:
            cart = Cart.query.filter_by(user_id=user_id).first()
        else:
            cart = Cart.query.filter_by(session_id=session_id).first()
        
        if cart:
            CartItem.query.filter_by(cart_id=cart.id).delete()
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cart cleared'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@cart_bp.route('/cart/count', methods=['GET'])
def get_cart_count():
    """Get total items count in cart"""
    try:
        user_id = request.args.get('user_id', type=int)
        session_id = request.args.get('session_id')
        
        if not user_id and not session_id:
            return jsonify({'success': True, 'count': 0})
        
        if user_id:
            cart = Cart.query.filter_by(user_id=user_id).first()
        else:
            cart = Cart.query.filter_by(session_id=session_id).first()
        
        count = 0
        if cart:
            count = sum(item.quantity for item in cart.items)
        
        return jsonify({
            'success': True,
            'count': count
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

