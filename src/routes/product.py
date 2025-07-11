from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.product import Product, ProductImage, ProductReview
from sqlalchemy import or_, and_

product_bp = Blueprint('product', __name__)

@product_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products with filtering and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        category = request.args.get('category')
        subcategory = request.args.get('subcategory')
        search = request.args.get('search')
        featured = request.args.get('featured', type=bool)
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        sort_by = request.args.get('sort_by', 'created_at')  # price_asc, price_desc, name, created_at
        
        query = Product.query.filter(Product.is_active == True)
        
        # Apply filters
        if category:
            query = query.filter(Product.category == category)
        if subcategory:
            query = query.filter(Product.subcategory == subcategory)
        if featured:
            query = query.filter(Product.is_featured == True)
        if search:
            query = query.filter(or_(
                Product.name.contains(search),
                Product.name_en.contains(search),
                Product.description.contains(search),
                Product.description_en.contains(search)
            ))
        if min_price:
            query = query.filter(Product.price >= min_price)
        if max_price:
            query = query.filter(Product.price <= max_price)
        
        # Apply sorting
        if sort_by == 'price_asc':
            query = query.order_by(Product.price.asc())
        elif sort_by == 'price_desc':
            query = query.order_by(Product.price.desc())
        elif sort_by == 'name':
            query = query.order_by(Product.name.asc())
        else:
            query = query.order_by(Product.created_at.desc())
        
        products = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'products': [product.to_dict() for product in products.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': products.total,
                'pages': products.pages,
                'has_next': products.has_next,
                'has_prev': products.has_prev
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product by ID"""
    try:
        product = Product.query.get_or_404(product_id)
        if not product.is_active:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        return jsonify({
            'success': True,
            'product': product.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/products', methods=['POST'])
def create_product():
    """Create new product (Admin only)"""
    try:
        data = request.get_json()
        
        product = Product(
            name=data.get('name'),
            name_en=data.get('name_en'),
            description=data.get('description'),
            description_en=data.get('description_en'),
            price=data.get('price'),
            category=data.get('category'),
            subcategory=data.get('subcategory'),
            gold_karat=data.get('gold_karat'),
            weight=data.get('weight'),
            stock_quantity=data.get('stock_quantity', 0),
            is_featured=data.get('is_featured', False)
        )
        
        db.session.add(product)
        db.session.commit()
        
        # Add images if provided
        if 'images' in data:
            for img_data in data['images']:
                image = ProductImage(
                    product_id=product.id,
                    image_url=img_data.get('image_url'),
                    alt_text=img_data.get('alt_text'),
                    is_primary=img_data.get('is_primary', False),
                    sort_order=img_data.get('sort_order', 0)
                )
                db.session.add(image)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'product': product.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update product (Admin only)"""
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        # Update fields
        for field in ['name', 'name_en', 'description', 'description_en', 'price', 
                     'category', 'subcategory', 'gold_karat', 'weight', 'stock_quantity', 
                     'is_featured', 'is_active']:
            if field in data:
                setattr(product, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'product': product.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete product (Admin only)"""
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Product deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/products/<int:product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    """Get reviews for a product"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        reviews = ProductReview.query.filter(
            and_(ProductReview.product_id == product_id, ProductReview.is_approved == True)
        ).order_by(ProductReview.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'reviews': [review.to_dict() for review in reviews.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': reviews.total,
                'pages': reviews.pages
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/products/<int:product_id>/reviews', methods=['POST'])
def create_review(product_id):
    """Create a review for a product"""
    try:
        data = request.get_json()
        
        review = ProductReview(
            product_id=product_id,
            user_id=data.get('user_id'),  # Should come from authentication
            rating=data.get('rating'),
            comment=data.get('comment')
        )
        
        db.session.add(review)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'review': review.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@product_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all product categories"""
    try:
        categories = db.session.query(Product.category).distinct().all()
        subcategories = db.session.query(Product.category, Product.subcategory).distinct().all()
        
        category_data = {}
        for category, subcategory in subcategories:
            if category not in category_data:
                category_data[category] = []
            if subcategory and subcategory not in category_data[category]:
                category_data[category].append(subcategory)
        
        return jsonify({
            'success': True,
            'categories': category_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

