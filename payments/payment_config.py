"""
Payment Gateway Configuration - Google Developer Standards
Handles Stripe and Razorpay payment gateway integration
"""

import os
from django.conf import settings
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PaymentConfig:
    """Centralized payment gateway configuration"""
    
    # Payment Gateway Selection
    DEFAULT_GATEWAY = os.environ.get('DEFAULT_PAYMENT_GATEWAY', 'razorpay')  # razorpay for India, stripe for global
    
    # Stripe Configuration
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_51234567890abcdefghijklmnopqrstuvwxyz')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_51234567890abcdefghijklmnopqrstuvwxyz')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_1234567890abcdefghijklmnopqrstuvwxyz')
    STRIPE_API_VERSION = '2023-10-16'
    
    # Razorpay Configuration (for Indian market)
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_1234567890abcd')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'abcdefghijklmnopqrstuvwxyz12')
    RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', 'webhook_secret_12345')
    
    # Currency Configuration
    DEFAULT_CURRENCY = 'INR'  # Indian Rupees for primary market
    SUPPORTED_CURRENCIES = ['INR', 'USD', 'EUR', 'GBP']
    
    # Payment Settings
    PAYMENT_SUCCESS_URL = '/payments/success/'
    PAYMENT_CANCEL_URL = '/payments/cancel/'
    PAYMENT_WEBHOOK_URL = '/payments/webhook/'
    
    # Test Mode Configuration
    TEST_MODE = os.environ.get('PAYMENT_TEST_MODE', 'True').lower() == 'true'
    
    # Invoice Settings
    INVOICE_PREFIX = 'INV'
    INVOICE_COMPANY_NAME = 'Exam Portal Platform'
    INVOICE_COMPANY_ADDRESS = 'Mumbai, Maharashtra, India'
    INVOICE_COMPANY_GSTIN = '29ABCDE1234F1Z5'  # Sample GSTIN for Indian invoices
    INVOICE_TERMS = 'Payment is due within 7 days. Thank you for your business!'
    
    @classmethod
    def get_stripe_config(cls) -> Dict[str, str]:
        """Get Stripe configuration"""
        return {
            'publishable_key': cls.STRIPE_PUBLISHABLE_KEY,
            'secret_key': cls.STRIPE_SECRET_KEY,
            'webhook_secret': cls.STRIPE_WEBHOOK_SECRET,
            'api_version': cls.STRIPE_API_VERSION,
            'test_mode': cls.TEST_MODE
        }
    
    @classmethod
    def get_razorpay_config(cls) -> Dict[str, str]:
        """Get Razorpay configuration"""
        return {
            'key_id': cls.RAZORPAY_KEY_ID,
            'key_secret': cls.RAZORPAY_KEY_SECRET,
            'webhook_secret': cls.RAZORPAY_WEBHOOK_SECRET,
            'test_mode': cls.TEST_MODE
        }
    
    @classmethod
    def get_active_gateway(cls, user_country: Optional[str] = None) -> str:
        """
        Determine which payment gateway to use based on user location
        Args:
            user_country: ISO country code
        Returns:
            Gateway name ('stripe' or 'razorpay')
        """
        # Use Razorpay for Indian users, Stripe for others
        indian_countries = ['IN', 'LK', 'BD', 'NP', 'BT']  # South Asian countries
        
        if user_country and user_country in indian_countries:
            return 'razorpay'
        elif user_country:
            return 'stripe'
        
        return cls.DEFAULT_GATEWAY
    
    @classmethod
    def get_currency_for_country(cls, country_code: str) -> str:
        """Get appropriate currency for country"""
        currency_map = {
            'IN': 'INR',
            'US': 'USD',
            'GB': 'GBP',
            'EU': 'EUR',
            # Add more mappings as needed
        }
        return currency_map.get(country_code, cls.DEFAULT_CURRENCY)
    
    @classmethod
    def format_amount_for_gateway(cls, amount: float, currency: str, gateway: str) -> int:
        """
        Format amount for specific gateway
        Stripe and Razorpay both expect amounts in smallest currency unit (paise/cents)
        """
        if currency.upper() in ['INR', 'USD', 'EUR', 'GBP']:
            # Convert to smallest unit (paise for INR, cents for USD)
            return int(amount * 100)
        return int(amount)
    
    @classmethod
    def validate_webhook_signature(cls, payload: str, signature: str, gateway: str) -> bool:
        """
        Validate webhook signature from payment gateway
        """
        try:
            if gateway == 'stripe':
                import stripe
                stripe.api_key = cls.STRIPE_SECRET_KEY
                stripe.Webhook.construct_event(
                    payload, signature, cls.STRIPE_WEBHOOK_SECRET
                )
                return True
            elif gateway == 'razorpay':
                import hmac
                import hashlib
                expected_signature = hmac.new(
                    bytes(cls.RAZORPAY_WEBHOOK_SECRET, 'utf-8'),
                    bytes(payload, 'utf-8'),
                    hashlib.sha256
                ).hexdigest()
                return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Webhook validation failed: {str(e)}")
            return False
        
        return False


# Subscription Plan Mappings for Payment Gateways
STRIPE_PRICE_IDS = {
    'basic_monthly': 'price_1234567890abcdef',
    'basic_yearly': 'price_2345678901bcdefg',
    'pro_monthly': 'price_3456789012cdefgh',
    'pro_yearly': 'price_4567890123defghi',
    'enterprise_monthly': 'price_5678901234efghij',
    'enterprise_yearly': 'price_6789012345fghijk',
}

RAZORPAY_PLAN_IDS = {
    'basic_monthly': 'plan_Basic1234567890',
    'basic_yearly': 'plan_BasicYr12345678',
    'pro_monthly': 'plan_Pro1234567890',
    'pro_yearly': 'plan_ProYr123456789',
    'enterprise_monthly': 'plan_Ent1234567890',
    'enterprise_yearly': 'plan_EntYr12345678',
}