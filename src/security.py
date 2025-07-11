import os
import re
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import redis

# Initialize security components
bcrypt = Bcrypt()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Redis for blacklisted tokens (in production, use actual Redis server)
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
except:
    # Fallback to in-memory storage for development
    redis_client = None
    blacklisted_tokens = set()

def init_security(app):
    """Initialize all security components"""
    
    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', secrets.token_urlsafe(32))
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_BLACKLIST_ENABLED'] = True
    app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access']
    
    # Initialize components
    bcrypt.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    
    # Security headers with Talisman
    Talisman(app, 
        force_https=False,  # Set to True in production
        strict_transport_security=True,
        content_security_policy={
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline' 'unsafe-eval'",
            'style-src': "'self' 'unsafe-inline'",
            'img-src': "'self' data: https:",
            'font-src': "'self' https:",
            'connect-src': "'self' https:",
        }
    )
    
    # JWT token blacklist checker
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        if redis_client:
            return redis_client.get(f"blacklist:{jti}") is not None
        else:
            return jti in blacklisted_tokens

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.generate_password_hash(password).decode('utf-8')

def check_password(password, hashed):
    """Check if password matches hash"""
    return bcrypt.check_password_hash(hashed, password)

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "كلمة المرور يجب أن تكون 8 أحرف على الأقل"
    
    if not re.search(r"[A-Z]", password):
        return False, "كلمة المرور يجب أن تحتوي على حرف كبير واحد على الأقل"
    
    if not re.search(r"[a-z]", password):
        return False, "كلمة المرور يجب أن تحتوي على حرف صغير واحد على الأقل"
    
    if not re.search(r"\d", password):
        return False, "كلمة المرور يجب أن تحتوي على رقم واحد على الأقل"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "كلمة المرور يجب أن تحتوي على رمز خاص واحد على الأقل"
    
    return True, "كلمة مرور قوية"

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_input(data):
    """Sanitize user input to prevent XSS"""
    if isinstance(data, str):
        # Remove potentially dangerous characters
        data = re.sub(r'[<>"\']', '', data)
        # Remove script tags
        data = re.sub(r'<script.*?</script>', '', data, flags=re.IGNORECASE | re.DOTALL)
        return data.strip()
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data

def generate_csrf_token():
    """Generate CSRF token"""
    return secrets.token_urlsafe(32)

def validate_csrf_token(token, session_token):
    """Validate CSRF token"""
    return secrets.compare_digest(token, session_token)

def rate_limit_by_user():
    """Rate limiting decorator for authenticated users"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        @limiter.limit("10 per minute")
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        # Check if user is admin (implement based on your user model)
        from src.models.user import User
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            return jsonify({'error': 'صلاحيات المدير مطلوبة'}), 403
        return f(*args, **kwargs)
    return decorated_function

def log_security_event(event_type, user_id=None, ip_address=None, details=None):
    """Log security events"""
    timestamp = datetime.utcnow().isoformat()
    log_entry = {
        'timestamp': timestamp,
        'event_type': event_type,
        'user_id': user_id,
        'ip_address': ip_address or request.remote_addr,
        'user_agent': request.headers.get('User-Agent'),
        'details': details
    }
    
    # In production, send to proper logging system
    print(f"SECURITY EVENT: {log_entry}")

def revoke_token(jti):
    """Revoke a JWT token"""
    if redis_client:
        # Store in Redis with expiration
        redis_client.setex(f"blacklist:{jti}", timedelta(days=1), "revoked")
    else:
        blacklisted_tokens.add(jti)

def check_suspicious_activity(user_id, action):
    """Check for suspicious user activity"""
    # Implement rate limiting and anomaly detection
    key = f"user_activity:{user_id}:{action}"
    
    if redis_client:
        current_count = redis_client.get(key)
        if current_count is None:
            redis_client.setex(key, 3600, 1)  # 1 hour window
            return False
        else:
            count = int(current_count)
            if count > 10:  # Threshold for suspicious activity
                log_security_event('suspicious_activity', user_id=user_id, details={'action': action, 'count': count})
                return True
            redis_client.incr(key)
    
    return False

def secure_headers():
    """Add security headers to response"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['X-Frame-Options'] = 'DENY'
                response.headers['X-XSS-Protection'] = '1; mode=block'
                response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            return response
        return decorated_function
    return decorator

def validate_file_upload(file):
    """Validate uploaded files"""
    if not file:
        return False, "لم يتم اختيار ملف"
    
    # Check file size (max 5MB)
    if len(file.read()) > 5 * 1024 * 1024:
        return False, "حجم الملف كبير جداً (الحد الأقصى 5 ميجابايت)"
    
    file.seek(0)  # Reset file pointer
    
    # Check file extension
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        return False, "نوع الملف غير مدعوم"
    
    # Check file content (basic magic number check)
    file_header = file.read(8)
    file.seek(0)
    
    # JPEG
    if file_header.startswith(b'\xff\xd8\xff'):
        return True, "ملف صالح"
    # PNG
    elif file_header.startswith(b'\x89PNG\r\n\x1a\n'):
        return True, "ملف صالح"
    # GIF
    elif file_header.startswith(b'GIF87a') or file_header.startswith(b'GIF89a'):
        return True, "ملف صالح"
    # WebP
    elif b'WEBP' in file_header:
        return True, "ملف صالح"
    else:
        return False, "محتوى الملف غير صالح"

def encrypt_sensitive_data(data, key=None):
    """Encrypt sensitive data (basic implementation)"""
    if key is None:
        key = current_app.config.get('SECRET_KEY', 'default_key')
    
    # Simple encryption for demo (use proper encryption in production)
    import base64
    encoded = base64.b64encode(data.encode()).decode()
    return encoded

def decrypt_sensitive_data(encrypted_data, key=None):
    """Decrypt sensitive data"""
    if key is None:
        key = current_app.config.get('SECRET_KEY', 'default_key')
    
    try:
        import base64
        decoded = base64.b64decode(encrypted_data.encode()).decode()
        return decoded
    except:
        return None

# SQL Injection prevention helpers
def escape_sql_string(value):
    """Escape SQL string to prevent injection"""
    if isinstance(value, str):
        return value.replace("'", "''").replace(";", "").replace("--", "")
    return value

def validate_sql_params(params):
    """Validate SQL parameters"""
    if isinstance(params, dict):
        return {key: escape_sql_string(value) for key, value in params.items()}
    elif isinstance(params, (list, tuple)):
        return [escape_sql_string(value) for value in params]
    return escape_sql_string(params)

