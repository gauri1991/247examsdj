from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription, Payment, Discount, PaymentHistory


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'billing_cycle', 'is_active', 'is_popular']
    list_filter = ['plan_type', 'billing_cycle', 'is_active', 'is_popular']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'start_date', 'end_date', 'auto_renew']
    list_filter = ['status', 'auto_renew', 'plan__plan_type']
    search_fields = ['user__username', 'user__email', 'plan__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'currency', 'status', 'gateway', 'created_at']
    list_filter = ['status', 'gateway', 'currency']
    search_fields = ['user__username', 'user__email', 'gateway_transaction_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'discount_type', 'value', 'used_count', 'max_uses', 'is_active']
    list_filter = ['discount_type', 'is_active']
    search_fields = ['code', 'name']
    readonly_fields = ['id', 'used_count', 'created_at', 'updated_at']
    filter_horizontal = ['applicable_plans']


@admin.register(PaymentHistory)  
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'created_at']
    list_filter = ['action']
    search_fields = ['user__username', 'user__email', 'description']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'