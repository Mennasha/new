from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class GoldPrice(db.Model):
    __tablename__ = 'gold_prices'
    
    id = db.Column(db.Integer, primary_key=True)
    karat = db.Column(db.String(10), nullable=False)  # 18k, 21k, 24k
    price_per_gram = db.Column(db.Float, nullable=False)  # Price in SAR
    currency = db.Column(db.String(10), default='SAR')
    source = db.Column(db.String(100))  # API source or manual
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'karat': self.karat,
            'price_per_gram': self.price_per_gram,
            'currency': self.currency,
            'source': self.source,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'is_active': self.is_active
        }

class SizeGuide(db.Model):
    __tablename__ = 'size_guides'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # ring, bracelet, necklace
    size_name = db.Column(db.String(20), nullable=False)  # XS, S, M, L, XL or numeric
    size_value = db.Column(db.Float)  # Measurement in mm or cm
    description = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'size_name': self.size_name,
            'size_value': self.size_value,
            'description': self.description,
            'is_active': self.is_active
        }

class AIFitting(db.Model):
    __tablename__ = 'ai_fittings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    session_id = db.Column(db.String(100))  # For guest users
    category = db.Column(db.String(50), nullable=False)  # ring, bracelet
    image_url = db.Column(db.String(500))  # Uploaded hand/wrist image
    measurements = db.Column(db.JSON)  # AI-detected measurements
    recommended_size = db.Column(db.String(20))
    confidence_score = db.Column(db.Float)  # AI confidence (0-1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'category': self.category,
            'image_url': self.image_url,
            'measurements': self.measurements,
            'recommended_size': self.recommended_size,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

