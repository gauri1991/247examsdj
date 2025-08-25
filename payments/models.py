from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class SubscriptionPlan(models.Model):
    PLAN_TYPES = [
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    BILLING_CYCLES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES)
    
    # Features
    max_tests = models.IntegerField(default=10, help_text="Maximum tests per month (-1 for unlimited)")
    max_questions = models.IntegerField(default=100, help_text="Maximum questions per test (-1 for unlimited)")
    pdf_extraction = models.BooleanField(default=False)
    analytics_access = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    custom_branding = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    trial_days = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscription_plans'
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} - ${self.price}/{self.billing_cycle}"
    
    @property
    def features_list(self):
        features = []
        if self.max_tests == -1:
            features.append("Unlimited Tests")
        else:
            features.append(f"{self.max_tests} Tests/month")
            
        if self.max_questions == -1:
            features.append("Unlimited Questions")
        else:
            features.append(f"{self.max_questions} Questions/test")
            
        if self.pdf_extraction:
            features.append("PDF Extraction")
        if self.analytics_access:
            features.append("Advanced Analytics")
        if self.priority_support:
            features.append("Priority Support")
        if self.custom_branding:
            features.append("Custom Branding")
        if self.api_access:
            features.append("API Access")
            
        return features


class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('trial', 'Trial'),
        ('suspended', 'Suspended'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscriptions')
    
    # Subscription details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    next_billing_date = models.DateTimeField(null=True, blank=True)
    
    # Payment details
    stripe_subscription_id = models.CharField(max_length=100, null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=100, null=True, blank=True)
    
    # Usage tracking
    tests_used = models.IntegerField(default=0)
    questions_used = models.IntegerField(default=0)
    
    # Auto-renewal
    auto_renew = models.BooleanField(default=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_subscriptions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"
    
    @property
    def is_active(self):
        return self.status == 'active' and self.end_date > timezone.now()
    
    @property
    def days_remaining(self):
        if self.end_date > timezone.now():
            return (self.end_date - timezone.now()).days
        return 0
    
    def can_create_test(self):
        if self.plan.max_tests == -1:  # Unlimited
            return True
        return self.tests_used < self.plan.max_tests
    
    def can_add_questions(self, count=1):
        if self.plan.max_questions == -1:  # Unlimited
            return True
        return (self.questions_used + count) <= self.plan.max_questions


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    GATEWAY_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('razorpay', 'Razorpay'),
        ('manual', 'Manual'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='payments', null=True)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='payments')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    
    # Gateway references
    gateway_transaction_id = models.CharField(max_length=200, null=True, blank=True)
    gateway_payment_intent_id = models.CharField(max_length=200, null=True, blank=True)
    
    # Metadata
    description = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"${self.amount} - {self.user.username} ({self.status})"


class Discount(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    
    # Discount details
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2)  # Percentage or fixed amount
    
    # Restrictions
    applicable_plans = models.ManyToManyField(SubscriptionPlan, blank=True)
    max_uses = models.IntegerField(null=True, blank=True, help_text="Null for unlimited uses")
    used_count = models.IntegerField(default=0)
    
    # Validity
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'discounts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.value}{'%' if self.discount_type == 'percentage' else '$'}"
    
    @property
    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True
    
    def calculate_discount(self, amount):
        if not self.is_valid:
            return 0
        
        if self.discount_type == 'percentage':
            return (amount * self.value) / 100
        else:  # fixed
            return min(self.value, amount)


class PaymentHistory(models.Model):
    """Track payment-related events for audit purposes"""
    ACTION_CHOICES = [
        ('payment_created', 'Payment Created'),
        ('payment_completed', 'Payment Completed'),
        ('payment_failed', 'Payment Failed'),
        ('refund_processed', 'Refund Processed'),
        ('subscription_created', 'Subscription Created'),
        ('subscription_renewed', 'Subscription Renewed'),
        ('subscription_cancelled', 'Subscription Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_history')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='history', null=True, blank=True)
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='history', null=True, blank=True)
    
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payment_history'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} - {self.user.username} ({self.created_at})"