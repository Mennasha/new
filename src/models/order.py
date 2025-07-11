from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, processing, shipped, delivered, cancelled
    total_amount = db.Column(db.Float, nullable=False)
    shipping_cost = db.Column(db.Float, default=0)
    tax_amount = db.Column(db.Float, default=0)
    discount_amount = db.Column(db.Float, default=0)
    payment_method = db.Column(db.String(50))  # credit_card, bank_transfer, cash_on_delivery
    payment_status = db.Column(db.String(50), default='pending')  # pending, paid, failed, refunded
    
    # Shipping Information
    shipping_name = db.Column(db.String(100), nullable=False)
    shipping_phone = db.Column(db.String(20), nullable=False)
    shipping_email = db.Column(db.String(100))
    shipping_address = db.Column(db.Text, nullable=False)
    shipping_city = db.Column(db.String(100), nullable=False)
    shipping_country = db.Column(db.String(100), nullable=False)
    shipping_postal_code = db.Column(db.String(20))
    
    # Tracking
    tracking_number = db.Column(db.String(100))
    estimated_delivery = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'user_id': self.user_id,
            'status': self.status,
            'total_amount': self.total_amount,
            'shipping_cost': self.shipping_cost,
            'tax_amount': self.tax_amount,
            'discount_amount': self.discount_amount,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'shipping_name': self.shipping_name,
            'shipping_phone': self.shipping_phone,
            'shipping_email': self.shipping_email,
            'shipping_address': self.shipping_address,
            'shipping_city': self.shipping_city,
            'shipping_country': self.shipping_country,
            'shipping_postal_code': self.shipping_postal_code,
            'tracking_number': self.tracking_number,
            'estimated_delivery': self.estimated_delivery.isoformat() if self.estimated_delivery else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items],
            'user_name': self.user.name if self.user else None
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)  # Price at time of order
    size = db.Column(db.String(10))
    custom_engraving = db.Column(db.String(200))
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'size': self.size,
            'custom_engraving': self.custom_engraving,
            'subtotal': self.quantity * self.unit_price,
            'product': self.product.to_dict() if self.product else None
        }

