import requests
import json
from datetime import datetime
import time
import threading

class GoldPriceService:
    def __init__(self):
        # يمكن الحصول على API key مجاني من metals-api.com
        self.api_key = "YOUR_API_KEY_HERE"  # يجب استبدالها بـ API key حقيقي
        self.base_url = "https://metals-api.com/api"
        self.current_prices = {
            'karat18': 185.50,
            'karat21': 216.25,
            'karat24': 247.00,
            'last_updated': datetime.now().isoformat()
        }
        self.usd_to_sar = 3.75  # سعر تحويل الدولار للريال السعودي
        
    def get_live_gold_price(self):
        """جلب أسعار الذهب الحية من API"""
        try:
            # استخدام API مجاني للحصول على أسعار الذهب
            url = "https://api.metals.live/v1/spot/gold"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                gold_usd_per_ounce = data[0]["price"]
                    
                # تحويل إلى ريال سعودي لكل جرام
                gold_sar_per_gram = (gold_usd_per_ounce / 31.1035) * self.usd_to_sar
                    
                # حساب أسعار العيارات المختلفة
                karat24_price = gold_sar_per_gram
                karat21_price = gold_sar_per_gram * (21/24)
                karat18_price = gold_sar_per_gram * (18/24)
                    
                self.current_prices = {
                    'karat18': round(karat18_price, 2),
                    'karat21': round(karat21_price, 2),
                    'karat24': round(karat24_price, 2),
                    'last_updated': datetime.now().isoformat()
                }
                    
                print(f"تم تحديث أسعار الذهب: {self.current_prices}")
                return True
            else:
                print(f"خطأ في الاتصال: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"خطأ في الشبكة: {e}")
            return False
        except Exception as e:
            print(f"خطأ عام: {e}")
            return False
    
    def get_fallback_prices(self):
        """الحصول على أسعار احتياطية في حالة فشل API"""
        try:
            # يمكن استخدام API بديل مجاني
            url = "https://api.metals.live/v1/spot/gold"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                gold_usd_per_ounce = data[0]['price']
                
                # تحويل إلى ريال سعودي لكل جرام
                gold_sar_per_gram = (gold_usd_per_ounce / 31.1035) * self.usd_to_sar
                
                # حساب أسعار العيارات المختلفة
                karat24_price = gold_sar_per_gram
                karat21_price = gold_sar_per_gram * (21/24)
                karat18_price = gold_sar_per_gram * (18/24)
                
                self.current_prices = {
                    'karat18': round(karat18_price, 2),
                    'karat21': round(karat21_price, 2),
                    'karat24': round(karat24_price, 2),
                    'last_updated': datetime.now().isoformat()
                }
                
                print(f"تم تحديث أسعار الذهب من المصدر البديل: {self.current_prices}")
                return True
        except:
            pass
        
        return False
    
    def update_prices(self):
        """تحديث أسعار الذهب"""
        success = self.get_live_gold_price()
        
        if not success:
            # محاولة استخدام مصدر بديل
            success = self.get_fallback_prices()
        
        if not success:
            # استخدام أسعار افتراضية محدثة يدوياً
            print("فشل في جلب الأسعار من جميع المصادر، استخدام الأسعار الافتراضية")
            
        return self.current_prices
    
    def get_current_prices(self):
        """الحصول على الأسعار الحالية"""
        return self.current_prices
    
    def start_auto_update(self, interval_minutes=30):
        """بدء التحديث التلقائي للأسعار"""
        def update_loop():
            while True:
                self.update_prices()
                time.sleep(interval_minutes * 60)  # تحويل الدقائق إلى ثوان
        
        # تشغيل التحديث في خيط منفصل
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
        print(f"تم بدء التحديث التلقائي كل {interval_minutes} دقيقة")

# إنشاء مثيل عام للخدمة
gold_service = GoldPriceService()

