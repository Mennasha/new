import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.product import product_bp
from src.routes.cart import cart_bp
from src.routes.order import order_bp
from src.routes.gold_price import gold_price_bp
from src.security import init_security, log_security_event, secure_headers
from src.config import config

app = Flask(__name__)

# Load configuration
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

# Initialize security
init_security(app)

# Enable CORS for all routes with security considerations
CORS(app, 
     origins=["http://localhost:5176", "http://localhost:3000"],  # Restrict origins in production
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(product_bp, url_prefix='/api')
app.register_blueprint(cart_bp, url_prefix='/api')
app.register_blueprint(order_bp, url_prefix='/api')
app.register_blueprint(gold_price_bp, url_prefix='/api')

# Import and register auth blueprint
from src.routes.auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/api/auth')

# Import and register site settings blueprint
from src.routes.site_settings import site_settings_bp
app.register_blueprint(site_settings_bp, url_prefix='/api')

# Initialize database
db.init_app(app)

# Import all models to ensure they are registered
from src.models.product import Product, ProductImage, ProductReview
from src.models.cart import Cart, CartItem
from src.models.order import Order, OrderItem
from src.models.gold_price import GoldPrice, SizeGuide, AIFitting
from src.models.site_settings import SiteSettings

with app.app_context():
    db.create_all()




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


