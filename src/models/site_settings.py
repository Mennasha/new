from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class SiteSettings(db.Model):
    __tablename__ = 'site_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic Site Information
    site_name = db.Column(db.String(200), default='مجوهرات بلسان')
    site_title = db.Column(db.String(200), default='مجوهرات بلسان - أفضل المجوهرات في المملكة')
    site_description = db.Column(db.Text, default='متجر مجوهرات بلسان يقدم أفضل المجوهرات والذهب والفضة بأعلى جودة وأفضل الأسعار في المملكة العربية السعودية')
    site_keywords = db.Column(db.Text, default='مجوهرات, ذهب, فضة, خواتم, أساور, عقود, أقراط, ساعات, مجوهرات نسائية, مجوهرات رجالية')
    site_logo = db.Column(db.String(500))
    site_favicon = db.Column(db.String(500))
    
    # Contact Information
    contact_email = db.Column(db.String(120), default='info@bilsanjewelry.com')
    contact_phone = db.Column(db.String(20), default='+966500000000')
    contact_whatsapp = db.Column(db.String(20), default='+966500000000')
    contact_address = db.Column(db.Text, default='الرياض، المملكة العربية السعودية')
    
    # Social Media Links
    facebook_url = db.Column(db.String(500))
    instagram_url = db.Column(db.String(500))
    twitter_url = db.Column(db.String(500))
    youtube_url = db.Column(db.String(500))
    tiktok_url = db.Column(db.String(500))
    
    # SEO Settings
    meta_author = db.Column(db.String(200), default='مجوهرات بلسان')
    meta_robots = db.Column(db.String(100), default='index, follow')
    canonical_url = db.Column(db.String(500))
    og_image = db.Column(db.String(500))
    og_type = db.Column(db.String(50), default='website')
    twitter_card = db.Column(db.String(50), default='summary_large_image')
    
    # Analytics and Tracking
    google_analytics_id = db.Column(db.String(50))
    google_tag_manager_id = db.Column(db.String(50))
    facebook_pixel_id = db.Column(db.String(50))
    google_site_verification = db.Column(db.String(100))
    bing_site_verification = db.Column(db.String(100))
    
    # Business Information
    business_hours = db.Column(db.Text, default='السبت - الخميس: 9:00 ص - 10:00 م')
    currency = db.Column(db.String(10), default='SAR')
    language = db.Column(db.String(10), default='ar')
    timezone = db.Column(db.String(50), default='Asia/Riyadh')
    
    # E-commerce Settings
    shipping_policy = db.Column(db.Text)
    return_policy = db.Column(db.Text)
    privacy_policy = db.Column(db.Text)
    terms_of_service = db.Column(db.Text)
    
    # Maintenance Mode
    maintenance_mode = db.Column(db.Boolean, default=False)
    maintenance_message = db.Column(db.Text, default='الموقع تحت الصيانة، سنعود قريباً')
    
    # Newsletter and Marketing
    newsletter_enabled = db.Column(db.Boolean, default=True)
    newsletter_title = db.Column(db.String(200), default='اشترك في نشرتنا الإخبارية')
    newsletter_description = db.Column(db.Text, default='احصل على آخر العروض والمنتجات الجديدة')
    
    # Custom CSS and JavaScript
    custom_css = db.Column(db.Text)
    custom_js = db.Column(db.Text)
    header_scripts = db.Column(db.Text)
    footer_scripts = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'site_name': self.site_name,
            'site_title': self.site_title,
            'site_description': self.site_description,
            'site_keywords': self.site_keywords,
            'site_logo': self.site_logo,
            'site_favicon': self.site_favicon,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'contact_whatsapp': self.contact_whatsapp,
            'contact_address': self.contact_address,
            'facebook_url': self.facebook_url,
            'instagram_url': self.instagram_url,
            'twitter_url': self.twitter_url,
            'youtube_url': self.youtube_url,
            'tiktok_url': self.tiktok_url,
            'meta_author': self.meta_author,
            'meta_robots': self.meta_robots,
            'canonical_url': self.canonical_url,
            'og_image': self.og_image,
            'og_type': self.og_type,
            'twitter_card': self.twitter_card,
            'google_analytics_id': self.google_analytics_id,
            'google_tag_manager_id': self.google_tag_manager_id,
            'facebook_pixel_id': self.facebook_pixel_id,
            'google_site_verification': self.google_site_verification,
            'bing_site_verification': self.bing_site_verification,
            'business_hours': self.business_hours,
            'currency': self.currency,
            'language': self.language,
            'timezone': self.timezone,
            'shipping_policy': self.shipping_policy,
            'return_policy': self.return_policy,
            'privacy_policy': self.privacy_policy,
            'terms_of_service': self.terms_of_service,
            'maintenance_mode': self.maintenance_mode,
            'maintenance_message': self.maintenance_message,
            'newsletter_enabled': self.newsletter_enabled,
            'newsletter_title': self.newsletter_title,
            'newsletter_description': self.newsletter_description,
            'custom_css': self.custom_css,
            'custom_js': self.custom_js,
            'header_scripts': self.header_scripts,
            'footer_scripts': self.footer_scripts,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by
        }
    
    @staticmethod
    def get_settings():
        """Get current site settings or create default if none exist"""
        settings = SiteSettings.query.first()
        if not settings:
            settings = SiteSettings()
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def update_settings(self, data, user_id):
        """Update site settings with new data"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_by = user_id
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self

