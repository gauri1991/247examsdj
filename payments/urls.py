from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Admin views
    path('admin/subscriptions/', views.admin_subscription_management, name='admin_subscription_management'),
    path('admin/discounts/', views.admin_discount_management, name='admin_discount_management'),
    path('admin/transactions/', views.admin_transaction_management, name='admin_transaction_management'),
    
    # User views
    path('plans/', views.subscription_plans, name='subscription_plans'),
    path('history/', views.payment_history, name='payment_history'),
    path('success/', views.payment_success, name='payment_success'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
    
    # API endpoints
    path('api/create-subscription/', views.create_subscription, name='create_subscription'),
    path('api/subscription-status/', views.subscription_status, name='subscription_status'),
    path('api/cancel-subscription/', views.cancel_subscription, name='cancel_subscription'),
    path('api/validate-discount/', views.validate_discount, name='validate_discount'),
    path('api/create-discount/', views.create_discount, name='create_discount'),
    path('api/process-refund/', views.process_refund, name='process_refund'),
    path('api/generate-invoices/', views.generate_invoices, name='generate_invoices'),
    path('api/verify-razorpay/', views.verify_razorpay_payment, name='verify_razorpay_payment'),
    path('api/regenerate-invoice/', views.regenerate_invoice, name='regenerate_invoice'),
    
    # Invoice downloads
    path('invoice/<uuid:payment_id>/download/', views.download_invoice, name='download_invoice'),
    
    # Webhook endpoints
    path('webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'),
    path('webhooks/razorpay/', views.razorpay_webhook, name='razorpay_webhook'),
]