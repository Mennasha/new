#!/usr/bin/env python3
"""
Seed data script for Bilsan Jewelry Backend
This script populates the database with sample data for testing
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.user import db, User
from src.models.product import Product, ProductImage
from src.models.gold_price import GoldPrice, SizeGuide
from src.main import app

def seed_users():
    """Create sample users"""
    users = [
        {
            'name': 'أحمد محمد',
            'email': 'ahmed@example.com',
            'phone': '+966501234567',
            'is_admin': True,
            'city': 'الرياض',
            'country': 'المملكة العربية السعودية'
        },
        {
            'name': 'فاطمة علي',
            'email': 'fatima@example.com',
            'phone': '+966507654321',
            'city': 'جدة',
            'country': 'المملكة العربية السعودية'
        },
        {
            'name': 'محمد السعيد',
            'email': 'mohammed@example.com',
            'phone': '+966509876543',
            'city': 'الدمام',
            'country': 'المملكة العربية السعودية'
        }
    ]
    
    for user_data in users:
        user = User(**user_data)
        user.set_password('password123')
        db.session.add(user)
    
    print("✓ Users seeded")

def seed_gold_prices():
    """Create gold price data"""
    prices = [
        {'karat': '18k', 'price_per_gram': 185.50, 'source': 'manual'},
        {'karat': '21k', 'price_per_gram': 216.25, 'source': 'manual'},
        {'karat': '24k', 'price_per_gram': 247.00, 'source': 'manual'}
    ]
    
    for price_data in prices:
        price = GoldPrice(**price_data)
        db.session.add(price)
    
    print("✓ Gold prices seeded")

def seed_size_guides():
    """Create size guide data"""
    sizes = [
        # Ring sizes
        {'category': 'ring', 'size_name': 'XS', 'size_value': 14.0, 'description': 'محيط 44 مم'},
        {'category': 'ring', 'size_name': 'S', 'size_value': 15.7, 'description': 'محيط 49 مم'},
        {'category': 'ring', 'size_name': 'M', 'size_value': 17.3, 'description': 'محيط 54 مم'},
        {'category': 'ring', 'size_name': 'L', 'size_value': 18.9, 'description': 'محيط 59 مم'},
        {'category': 'ring', 'size_name': 'XL', 'size_value': 20.6, 'description': 'محيط 65 مم'},
        
        # Bracelet sizes
        {'category': 'bracelet', 'size_name': 'S', 'size_value': 16.0, 'description': 'محيط المعصم 16 سم'},
        {'category': 'bracelet', 'size_name': 'M', 'size_value': 18.0, 'description': 'محيط المعصم 18 سم'},
        {'category': 'bracelet', 'size_name': 'L', 'size_value': 20.0, 'description': 'محيط المعصم 20 سم'},
        
        # Necklace sizes
        {'category': 'necklace', 'size_name': 'قصير', 'size_value': 40.0, 'description': 'طول 40 سم'},
        {'category': 'necklace', 'size_name': 'متوسط', 'size_value': 50.0, 'description': 'طول 50 سم'},
        {'category': 'necklace', 'size_name': 'طويل', 'size_value': 60.0, 'description': 'طول 60 سم'}
    ]
    
    for size_data in sizes:
        size = SizeGuide(**size_data)
        db.session.add(size)
    
    print("✓ Size guides seeded")

def seed_products():
    """Create sample products"""
    products = [
        # Women's Jewelry
        {
            'name': 'خاتم الماس كلاسيكي',
            'name_en': 'Classic Diamond Ring',
            'description': 'خاتم ذهب أبيض عيار 18 قيراط مرصع بالماس الطبيعي',
            'description_en': '18k white gold ring set with natural diamonds',
            'price': 2500.00,
            'category': 'women',
            'subcategory': 'rings',
            'gold_karat': '18k',
            'weight': 3.5,
            'stock_quantity': 10,
            'is_featured': True,
            'images': [
                {'image_url': '/images/products/diamond-ring-1.jpg', 'alt_text': 'خاتم الماس كلاسيكي', 'is_primary': True, 'sort_order': 1},
                {'image_url': '/images/products/diamond-ring-2.jpg', 'alt_text': 'خاتم الماس كلاسيكي - منظر جانبي', 'is_primary': False, 'sort_order': 2}
            ]
        },
        {
            'name': 'عقد لؤلؤ طبيعي',
            'name_en': 'Natural Pearl Necklace',
            'description': 'عقد من اللؤلؤ الطبيعي مع إغلاق ذهبي عيار 21 قيراط',
            'description_en': 'Natural pearl necklace with 21k gold clasp',
            'price': 1800.00,
            'category': 'women',
            'subcategory': 'necklaces',
            'gold_karat': '21k',
            'weight': 15.2,
            'stock_quantity': 5,
            'is_featured': True,
            'images': [
                {'image_url': '/images/products/pearl-necklace-1.jpg', 'alt_text': 'عقد لؤلؤ طبيعي', 'is_primary': True, 'sort_order': 1}
            ]
        },
        {
            'name': 'أسورة ذهبية مزخرفة',
            'name_en': 'Ornate Gold Bracelet',
            'description': 'أسورة ذهب أصفر عيار 21 قيراط بتصميم عربي تقليدي',
            'description_en': '21k yellow gold bracelet with traditional Arabic design',
            'price': 3200.00,
            'category': 'women',
            'subcategory': 'bracelets',
            'gold_karat': '21k',
            'weight': 12.8,
            'stock_quantity': 8,
            'is_featured': False,
            'images': [
                {'image_url': '/images/products/gold-bracelet-1.jpg', 'alt_text': 'أسورة ذهبية مزخرفة', 'is_primary': True, 'sort_order': 1}
            ]
        },
        {
            'name': 'أقراط الزمرد الفاخرة',
            'name_en': 'Luxury Emerald Earrings',
            'description': 'أقراط ذهب أبيض عيار 18 قيراط مرصعة بالزمرد والماس',
            'description_en': '18k white gold earrings set with emerald and diamonds',
            'price': 4500.00,
            'category': 'women',
            'subcategory': 'earrings',
            'gold_karat': '18k',
            'weight': 6.2,
            'stock_quantity': 3,
            'is_featured': True,
            'images': [
                {'image_url': '/images/products/emerald-earrings-1.jpg', 'alt_text': 'أقراط الزمرد الفاخرة', 'is_primary': True, 'sort_order': 1}
            ]
        },
        
        # Men's Jewelry
        {
            'name': 'خاتم رجالي كلاسيكي',
            'name_en': 'Classic Men\'s Ring',
            'description': 'خاتم ذهب أصفر عيار 21 قيراط للرجال بتصميم كلاسيكي',
            'description_en': '21k yellow gold men\'s ring with classic design',
            'price': 1200.00,
            'category': 'men',
            'subcategory': 'rings',
            'gold_karat': '21k',
            'weight': 8.5,
            'stock_quantity': 15,
            'is_featured': False,
            'images': [
                {'image_url': '/images/products/mens-ring-1.jpg', 'alt_text': 'خاتم رجالي كلاسيكي', 'is_primary': True, 'sort_order': 1}
            ]
        },
        {
            'name': 'سلسلة رجالية فاخرة',
            'name_en': 'Luxury Men\'s Chain',
            'description': 'سلسلة ذهب أصفر عيار 21 قيراط للرجال بوزن 25 جرام',
            'description_en': '21k yellow gold men\'s chain weighing 25 grams',
            'price': 5500.00,
            'category': 'men',
            'subcategory': 'chains',
            'gold_karat': '21k',
            'weight': 25.0,
            'stock_quantity': 6,
            'is_featured': True,
            'images': [
                {'image_url': '/images/products/mens-chain-1.jpg', 'alt_text': 'سلسلة رجالية فاخرة', 'is_primary': True, 'sort_order': 1}
            ]
        },
        
        # Watches
        {
            'name': 'ساعة ذهبية كلاسيكية',
            'name_en': 'Classic Gold Watch',
            'description': 'ساعة يد ذهبية فاخرة مع حركة سويسرية',
            'description_en': 'Luxury gold wristwatch with Swiss movement',
            'price': 8500.00,
            'category': 'watches',
            'subcategory': 'luxury',
            'gold_karat': '18k',
            'weight': 45.0,
            'stock_quantity': 2,
            'is_featured': True,
            'images': [
                {'image_url': '/images/products/gold-watch-1.jpg', 'alt_text': 'ساعة ذهبية كلاسيكية', 'is_primary': True, 'sort_order': 1}
            ]
        },
        
        # Gifts
        {
            'name': 'طقم مجوهرات للعروس',
            'name_en': 'Bridal Jewelry Set',
            'description': 'طقم كامل للعروس يشمل عقد وأقراط وخاتم وأسورة',
            'description_en': 'Complete bridal set including necklace, earrings, ring and bracelet',
            'price': 12000.00,
            'category': 'gifts',
            'subcategory': 'bridal',
            'gold_karat': '21k',
            'weight': 35.5,
            'stock_quantity': 1,
            'is_featured': True,
            'images': [
                {'image_url': '/images/products/bridal-set-1.jpg', 'alt_text': 'طقم مجوهرات للعروس', 'is_primary': True, 'sort_order': 1}
            ]
        }
    ]
    
    for product_data in products:
        images_data = product_data.pop('images', [])
        product = Product(**product_data)
        db.session.add(product)
        db.session.flush()  # Get product ID
        
        # Add images
        for img_data in images_data:
            image = ProductImage(product_id=product.id, **img_data)
            db.session.add(image)
    
    print("✓ Products seeded")

def main():
    """Main seeding function"""
    with app.app_context():
        print("🌱 Starting database seeding...")
        
        # Clear existing data (optional)
        # db.drop_all()
        # db.create_all()
        
        try:
            seed_users()
            seed_gold_prices()
            seed_size_guides()
            seed_products()
            
            db.session.commit()
            print("✅ Database seeding completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during seeding: {str(e)}")
            raise

if __name__ == '__main__':
    main()

