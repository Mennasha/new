from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.site_settings import SiteSettings, db
from src.models.user import User
from src.security import admin_required, sanitize_input, log_security_event, limiter

site_settings_bp = Blueprint('site_settings', __name__)

@site_settings_bp.route('/settings', methods=['GET'])
def get_site_settings():
    """Get current site settings (public endpoint for frontend)"""
    try:
        settings = SiteSettings.get_settings()
        
        # Return only public settings for frontend
        public_settings = {
            'site_name': settings.site_name,
            'site_title': settings.site_title,
            'site_description': settings.site_description,
            'site_keywords': settings.site_keywords,
            'site_logo': settings.site_logo,
            'site_favicon': settings.site_favicon,
            'contact_email': settings.contact_email,
            'contact_phone': settings.contact_phone,
            'contact_whatsapp': settings.contact_whatsapp,
            'contact_address': settings.contact_address,
            'facebook_url': settings.facebook_url,
            'instagram_url': settings.instagram_url,
            'twitter_url': settings.twitter_url,
            'youtube_url': settings.youtube_url,
            'tiktok_url': settings.tiktok_url,
            'business_hours': settings.business_hours,
            'currency': settings.currency,
            'language': settings.language,
            'newsletter_enabled': settings.newsletter_enabled,
            'newsletter_title': settings.newsletter_title,
            'newsletter_description': settings.newsletter_description,
            'maintenance_mode': settings.maintenance_mode,
            'maintenance_message': settings.maintenance_message
        }
        
        return jsonify(public_settings), 200
        
    except Exception as e:
        log_security_event('settings_error', details={'error': str(e)})
        return jsonify({'error': 'حدث خطأ أثناء جلب الإعدادات'}), 500

@site_settings_bp.route('/admin/settings', methods=['GET'])
@admin_required
def get_admin_settings():
    """Get all site settings for admin panel"""
    try:
        settings = SiteSettings.get_settings()
        return jsonify(settings.to_dict()), 200
        
    except Exception as e:
        log_security_event('admin_settings_error', details={'error': str(e)})
        return jsonify({'error': 'حدث خطأ أثناء جلب الإعدادات'}), 500

@site_settings_bp.route('/admin/settings', methods=['PUT'])
@admin_required
@limiter.limit("10 per minute")
def update_site_settings():
    """Update site settings (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'بيانات غير صالحة'}), 400
        
        # Sanitize input
        data = sanitize_input(data)
        
        # Get current settings
        settings = SiteSettings.get_settings()
        
        # Update settings
        settings.update_settings(data, current_user_id)
        
        # Log the update
        log_security_event('settings_updated', user_id=current_user_id, details={'updated_fields': list(data.keys())})
        
        return jsonify({
            'message': 'تم تحديث الإعدادات بنجاح',
            'settings': settings.to_dict()
        }), 200
        
    except Exception as e:
        log_security_event('settings_update_error', details={'error': str(e)})
        return jsonify({'error': 'حدث خطأ أثناء تحديث الإعدادات'}), 500

@site_settings_bp.route('/admin/settings/seo', methods=['PUT'])
@admin_required
@limiter.limit("5 per minute")
def update_seo_settings():
    """Update SEO specific settings"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'بيانات غير صالحة'}), 400
        
        # Sanitize input
        data = sanitize_input(data)
        
        # Validate SEO fields
        seo_fields = [
            'site_title', 'site_description', 'site_keywords', 'meta_author',
            'meta_robots', 'canonical_url', 'og_image', 'og_type', 'twitter_card',
            'google_analytics_id', 'google_tag_manager_id', 'facebook_pixel_id',
            'google_site_verification', 'bing_site_verification'
        ]
        
        # Filter only SEO related fields
        seo_data = {key: value for key, value in data.items() if key in seo_fields}
        
        if not seo_data:
            return jsonify({'error': 'لا توجد حقول SEO صالحة للتحديث'}), 400
        
        # Get current settings
        settings = SiteSettings.get_settings()
        
        # Update SEO settings
        settings.update_settings(seo_data, current_user_id)
        
        # Log the update
        log_security_event('seo_settings_updated', user_id=current_user_id, details={'updated_fields': list(seo_data.keys())})
        
        return jsonify({
            'message': 'تم تحديث إعدادات SEO بنجاح',
            'seo_settings': {key: getattr(settings, key) for key in seo_fields}
        }), 200
        
    except Exception as e:
        log_security_event('seo_settings_error', details={'error': str(e)})
        return jsonify({'error': 'حدث خطأ أثناء تحديث إعدادات SEO'}), 500

@site_settings_bp.route('/admin/settings/social', methods=['PUT'])
@admin_required
@limiter.limit("5 per minute")
def update_social_settings():
    """Update social media settings"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'بيانات غير صالحة'}), 400
        
        # Sanitize input
        data = sanitize_input(data)
        
        # Validate social media fields
        social_fields = [
            'facebook_url', 'instagram_url', 'twitter_url', 
            'youtube_url', 'tiktok_url'
        ]
        
        # Filter only social media related fields
        social_data = {key: value for key, value in data.items() if key in social_fields}
        
        if not social_data:
            return jsonify({'error': 'لا توجد حقول وسائل التواصل الاجتماعي صالحة للتحديث'}), 400
        
        # Validate URLs
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        for key, value in social_data.items():
            if value and not url_pattern.match(value):
                return jsonify({'error': f'رابط {key} غير صالح'}), 400
        
        # Get current settings
        settings = SiteSettings.get_settings()
        
        # Update social settings
        settings.update_settings(social_data, current_user_id)
        
        # Log the update
        log_security_event('social_settings_updated', user_id=current_user_id, details={'updated_fields': list(social_data.keys())})
        
        return jsonify({
            'message': 'تم تحديث إعدادات وسائل التواصل الاجتماعي بنجاح',
            'social_settings': {key: getattr(settings, key) for key in social_fields}
        }), 200
        
    except Exception as e:
        log_security_event('social_settings_error', details={'error': str(e)})
        return jsonify({'error': 'حدث خطأ أثناء تحديث إعدادات وسائل التواصل الاجتماعي'}), 500

@site_settings_bp.route('/admin/settings/maintenance', methods=['POST'])
@admin_required
@limiter.limit("3 per minute")
def toggle_maintenance_mode():
    """Toggle maintenance mode"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'maintenance_mode' not in data:
            return jsonify({'error': 'حالة الصيانة مطلوبة'}), 400
        
        maintenance_mode = bool(data['maintenance_mode'])
        maintenance_message = data.get('maintenance_message', 'الموقع تحت الصيانة، سنعود قريباً')
        
        # Get current settings
        settings = SiteSettings.get_settings()
        
        # Update maintenance settings
        settings.update_settings({
            'maintenance_mode': maintenance_mode,
            'maintenance_message': maintenance_message
        }, current_user_id)
        
        # Log the change
        log_security_event('maintenance_mode_changed', user_id=current_user_id, details={
            'maintenance_mode': maintenance_mode,
            'message': maintenance_message
        })
        
        return jsonify({
            'message': f'تم {"تفعيل" if maintenance_mode else "إلغاء"} وضع الصيانة',
            'maintenance_mode': maintenance_mode,
            'maintenance_message': maintenance_message
        }), 200
        
    except Exception as e:
        log_security_event('maintenance_mode_error', details={'error': str(e)})
        return jsonify({'error': 'حدث خطأ أثناء تغيير وضع الصيانة'}), 500

@site_settings_bp.route('/admin/settings/backup', methods=['GET'])
@admin_required
def backup_settings():
    """Create a backup of current settings"""
    try:
        current_user_id = get_jwt_identity()
        settings = SiteSettings.get_settings()
        
        # Log the backup
        log_security_event('settings_backup_created', user_id=current_user_id)
        
        return jsonify({
            'message': 'تم إنشاء نسخة احتياطية من الإعدادات',
            'backup_data': settings.to_dict(),
            'backup_timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        log_security_event('settings_backup_error', details={'error': str(e)})
        return jsonify({'error': 'حدث خطأ أثناء إنشاء النسخة الاحتياطية'}), 500

@site_settings_bp.route('/admin/settings/restore', methods=['POST'])
@admin_required
@limiter.limit("1 per minute")
def restore_settings():
    """Restore settings from backup"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'backup_data' not in data:
            return jsonify({'error': 'بيانات النسخة الاحتياطية مطلوبة'}), 400
        
        backup_data = data['backup_data']
        
        # Sanitize input
        backup_data = sanitize_input(backup_data)
        
        # Remove system fields that shouldn't be restored
        system_fields = ['id', 'created_at', 'updated_at', 'updated_by']
        for field in system_fields:
            backup_data.pop(field, None)
        
        # Get current settings
        settings = SiteSettings.get_settings()
        
        # Restore settings
        settings.update_settings(backup_data, current_user_id)
        
        # Log the restore
        log_security_event('settings_restored', user_id=current_user_id, details={'restored_fields': list(backup_data.keys())})
        
        return jsonify({
            'message': 'تم استعادة الإعدادات من النسخة الاحتياطية بنجاح',
            'settings': settings.to_dict()
        }), 200
        
    except Exception as e:
        log_security_event('settings_restore_error', details={'error': str(e)})
        return jsonify({'error': 'حدث خطأ أثناء استعادة الإعدادات'}), 500

