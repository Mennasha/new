from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from src.models.user import User, db
from src.security import (
    hash_password, check_password, validate_password_strength, 
    validate_email, sanitize_input, rate_limit_by_user, 
    log_security_event, check_suspicious_activity, revoke_token,
    limiter
)
from datetime import datetime, timedelta
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """User registration with enhanced security"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'بيانات غير صالحة'}), 400
        
        # Sanitize input
        data = sanitize_input(data)
        
        # Validate required fields
        required_fields = ['name', 'email', 'password', 'phone']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'حقل {field} مطلوب'}), 400
        
        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        phone = data['phone'].strip()
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'صيغة البريد الإلكتروني غير صحيحة'}), 400
        
        # Validate password strength
        is_strong, message = validate_password_strength(password)
        if not is_strong:
            return jsonify({'error': message}), 400
        
        # Validate phone number (Saudi format)
        phone_pattern = r'^(\+966|966|0)?[5][0-9]{8}$'
        if not re.match(phone_pattern, phone):
            return jsonify({'error': 'رقم الهاتف غير صحيح'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            log_security_event('registration_attempt', details={'email': email, 'reason': 'email_exists'})
            return jsonify({'error': 'البريد الإلكتروني مستخدم بالفعل'}), 409
        
        if User.query.filter_by(phone=phone).first():
            return jsonify({'error': 'رقم الهاتف مستخدم بالفعل'}), 409
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Create new user
        user = User(
            name=name,
            email=email,
            password_hash=hashed_password,
            phone=phone,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Log successful registration
        log_security_event('user_registered', user_id=user.id, details={'email': email})
        
        # Create access token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'message': 'تم إنشاء الحساب بنجاح',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone
            }
        }), 201
        
    except Exception as e:
        log_security_event('registration_error', details={'error': str(e)})
        return jsonify({'error': 'حدث خطأ أثناء إنشاء الحساب'}), 500

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """User login with enhanced security"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'بيانات غير صالحة'}), 400
        
        # Sanitize input
        data = sanitize_input(data)
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'البريد الإلكتروني وكلمة المرور مطلوبان'}), 400
        
        # Check for suspicious activity
        if check_suspicious_activity(email, 'login_attempt'):
            log_security_event('suspicious_login', details={'email': email})
            return jsonify({'error': 'تم حظر الحساب مؤقتاً بسبب نشاط مشبوه'}), 429
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            log_security_event('login_failed', details={'email': email, 'reason': 'user_not_found'})
            return jsonify({'error': 'البريد الإلكتروني أو كلمة المرور غير صحيحة'}), 401
        
        # Check if user is active
        if not user.is_active:
            log_security_event('login_failed', user_id=user.id, details={'reason': 'account_disabled'})
            return jsonify({'error': 'الحساب معطل'}), 401
        
        # Verify password
        if not check_password(password, user.password_hash):
            log_security_event('login_failed', user_id=user.id, details={'reason': 'wrong_password'})
            return jsonify({'error': 'البريد الإلكتروني أو كلمة المرور غير صحيحة'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Log successful login
        log_security_event('user_login', user_id=user.id)
        
        # Create access token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'message': 'تم تسجيل الدخول بنجاح',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'is_admin': user.is_admin
            }
        }), 200
        
    except Exception as e:
        log_security_event('login_error', details={'error': str(e)})
        return jsonify({'error': 'حدث خطأ أثناء تسجيل الدخول'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout with token revocation"""
    try:
        current_user_id = get_jwt_identity()
        jti = get_jwt()['jti']
        
        # Revoke the token
        revoke_token(jti)
        
        # Log logout
        log_security_event('user_logout', user_id=current_user_id)
        
        return jsonify({'message': 'تم تسجيل الخروج بنجاح'}), 200
        
    except Exception as e:
        log_security_event('logout_error', details={'error': str(e)})
        return jsonify({'error': 'حدث خطأ أثناء تسجيل الخروج'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@limiter.limit("3 per minute")
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'بيانات غير صالحة'}), 400
        
        # Sanitize input
        data = sanitize_input(data)
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'error': 'كلمة المرور الحالية والجديدة مطلوبتان'}), 400
        
        # Get user
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'المستخدم غير موجود'}), 404
        
        # Verify current password
        if not check_password(current_password, user.password_hash):
            log_security_event('password_change_failed', user_id=current_user_id, details={'reason': 'wrong_current_password'})
            return jsonify({'error': 'كلمة المرور الحالية غير صحيحة'}), 401
        
        # Validate new password strength
        is_strong, message = validate_password_strength(new_password)
        if not is_strong:
            return jsonify({'error': message}), 400
        
        # Update password
        user.password_hash = hash_password(new_password)
        user.password_changed_at = datetime.utcnow()
        db.session.commit()
        
        # Log password change
        log_security_event('password_changed', user_id=current_user_id)
        
        return jsonify({'message': 'تم تغيير كلمة المرور بنجاح'}), 200
        
    except Exception as e:
        log_security_event('password_change_error', details={'error': str(e)})
        return jsonify({'error': 'حدث خطأ أثناء تغيير كلمة المرور'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'المستخدم غير موجود'}), 404
        
        return jsonify({
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'is_admin': user.is_admin,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        }), 200
        
    except Exception as e:
        log_security_event('profile_error', details={'error': str(e)})
        return jsonify({'error': 'حدث خطأ أثناء جلب البيانات'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
@limiter.limit("5 per minute")
def update_profile():
    """Update user profile"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'بيانات غير صالحة'}), 400
        
        # Sanitize input
        data = sanitize_input(data)
        
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'المستخدم غير موجود'}), 404
        
        # Update allowed fields
        if 'name' in data:
            user.name = data['name'].strip()
        
        if 'phone' in data:
            phone = data['phone'].strip()
            phone_pattern = r'^(\+966|966|0)?[5][0-9]{8}$'
            if not re.match(phone_pattern, phone):
                return jsonify({'error': 'رقم الهاتف غير صحيح'}), 400
            
            # Check if phone is already used by another user
            existing_user = User.query.filter_by(phone=phone).filter(User.id != current_user_id).first()
            if existing_user:
                return jsonify({'error': 'رقم الهاتف مستخدم بالفعل'}), 409
            
            user.phone = phone
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log profile update
        log_security_event('profile_updated', user_id=current_user_id)
        
        return jsonify({
            'message': 'تم تحديث البيانات بنجاح',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone
            }
        }), 200
        
    except Exception as e:
        log_security_event('profile_update_error', details={'error': str(e)})
        return jsonify({'error': 'حدث خطأ أثناء تحديث البيانات'}), 500

@auth_bp.route('/verify-token', methods=['POST'])
@jwt_required()
def verify_token():
    """Verify JWT token validity"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'valid': False}), 401
        
        return jsonify({
            'valid': True,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'is_admin': user.is_admin
            }
        }), 200
        
    except Exception as e:
        return jsonify({'valid': False}), 401

