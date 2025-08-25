"""
Payment Gateway Services - Enterprise Implementation
Handles Stripe and Razorpay payment processing
"""

import stripe
import razorpay
import logging
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

from .payment_config import PaymentConfig
from .models import Payment, UserSubscription, PaymentHistory

logger = logging.getLogger(__name__)


class StripeGateway:
    """Stripe payment gateway implementation"""
    
    def __init__(self):
        config = PaymentConfig.get_stripe_config()
        stripe.api_key = config['secret_key']
        stripe.api_version = config['api_version']
        self.publishable_key = config['publishable_key']
    
    def create_checkout_session(
        self, 
        user, 
        plan, 
        success_url: str, 
        cancel_url: str,
        discount_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create Stripe checkout session for subscription
        """
        try:
            # Get the Stripe price ID for this plan
            from .payment_config import STRIPE_PRICE_IDS
            price_key = f"{plan.plan_type}_{plan.billing_cycle}"
            price_id = STRIPE_PRICE_IDS.get(price_key)
            
            if not price_id:
                raise ValueError(f"No Stripe price ID configured for {price_key}")
            
            # Create customer if doesn't exist
            customer = self._get_or_create_customer(user)
            
            # Prepare checkout session parameters
            session_params = {
                'payment_method_types': ['card'],
                'line_items': [{
                    'price': price_id,
                    'quantity': 1,
                }],
                'mode': 'subscription',
                'success_url': success_url + '?session_id={CHECKOUT_SESSION_ID}',
                'cancel_url': cancel_url,
                'customer': customer.id,
                'metadata': {
                    'user_id': str(user.id),
                    'plan_id': str(plan.id),
                }
            }
            
            # Apply discount if provided
            if discount_code:
                # You would need to create these promotion codes in Stripe dashboard
                session_params['discounts'] = [{'promotion_code': discount_code}]
            
            # Create the session
            session = stripe.checkout.Session.create(**session_params)
            
            # Create pending payment record
            Payment.objects.create(
                user=user,
                plan=plan,
                amount=plan.price,
                currency='USD',
                status='pending',
                gateway='stripe',
                gateway_transaction_id=session.id,
                metadata={
                    'checkout_session_id': session.id,
                    'customer_id': customer.id
                }
            )
            
            return {
                'success': True,
                'session_id': session.id,
                'checkout_url': session.url,
                'publishable_key': self.publishable_key
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error creating Stripe session: {str(e)}")
            return {
                'success': False,
                'error': 'An error occurred processing your payment'
            }
    
    def _get_or_create_customer(self, user) -> stripe.Customer:
        """Get or create Stripe customer for user"""
        # Check if user has stripe customer ID stored
        if hasattr(user, 'stripe_customer_id') and user.stripe_customer_id:
            try:
                return stripe.Customer.retrieve(user.stripe_customer_id)
            except stripe.error.InvalidRequestError:
                pass
        
        # Create new customer
        customer = stripe.Customer.create(
            email=user.email,
            name=user.get_full_name() or user.username,
            metadata={'user_id': str(user.id)}
        )
        
        # Store customer ID (you might want to add this field to User model)
        # user.stripe_customer_id = customer.id
        # user.save(update_fields=['stripe_customer_id'])
        
        return customer
    
    def process_webhook(self, payload: str, signature: str) -> Tuple[bool, str]:
        """Process Stripe webhook"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, PaymentConfig.STRIPE_WEBHOOK_SECRET
            )
            
            # Handle different event types
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                self._handle_successful_payment(session)
                
            elif event['type'] == 'invoice.payment_succeeded':
                invoice = event['data']['object']
                self._handle_subscription_renewal(invoice)
                
            elif event['type'] == 'customer.subscription.deleted':
                subscription = event['data']['object']
                self._handle_subscription_cancellation(subscription)
            
            return True, "Webhook processed successfully"
            
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid Stripe webhook signature")
            return False, "Invalid signature"
        except Exception as e:
            logger.error(f"Error processing Stripe webhook: {str(e)}")
            return False, str(e)
    
    def _handle_successful_payment(self, session):
        """Handle successful payment from Stripe"""
        with transaction.atomic():
            # Update payment record
            payment = Payment.objects.filter(
                gateway_transaction_id=session['id']
            ).first()
            
            if payment:
                payment.status = 'completed'
                payment.metadata['stripe_subscription_id'] = session.get('subscription')
                payment.save()
                
                # Create or update subscription
                UserSubscription.objects.update_or_create(
                    user=payment.user,
                    defaults={
                        'plan': payment.plan,
                        'status': 'active',
                        'start_date': timezone.now(),
                        'current_period_end': timezone.now() + timezone.timedelta(days=30),
                        'stripe_subscription_id': session.get('subscription')
                    }
                )
                
                # Log payment history
                PaymentHistory.objects.create(
                    payment=payment,
                    action='payment_completed',
                    metadata={'session_id': session['id']}
                )
    
    def _handle_subscription_renewal(self, invoice):
        """Handle subscription renewal"""
        # Implementation for handling recurring payments
        pass
    
    def _handle_subscription_cancellation(self, subscription):
        """Handle subscription cancellation"""
        # Update UserSubscription status to cancelled
        pass
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a Stripe subscription"""
        try:
            stripe.Subscription.delete(subscription_id)
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling Stripe subscription: {str(e)}")
            return False


class RazorpayGateway:
    """Razorpay payment gateway implementation for Indian market"""
    
    def __init__(self):
        config = PaymentConfig.get_razorpay_config()
        self.client = razorpay.Client(
            auth=(config['key_id'], config['key_secret'])
        )
        self.key_id = config['key_id']
    
    def create_order(
        self, 
        user, 
        plan, 
        discount_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create Razorpay order for payment
        """
        try:
            # Calculate amount (Razorpay expects amount in paise)
            amount = PaymentConfig.format_amount_for_gateway(
                plan.price, 'INR', 'razorpay'
            )
            
            # Apply discount if provided
            if discount_code:
                from .models import Discount
                discount = Discount.objects.filter(
                    code=discount_code,
                    is_active=True,
                    valid_until__gte=timezone.now()
                ).first()
                
                if discount:
                    if discount.discount_type == 'percentage':
                        amount = int(amount * (1 - discount.value / 100))
                    else:
                        amount = max(0, amount - int(discount.value * 100))
            
            # Create Razorpay order
            order_data = {
                'amount': amount,
                'currency': 'INR',
                'payment_capture': 1,  # Auto capture payment
                'notes': {
                    'user_id': str(user.id),
                    'plan_id': str(plan.id),
                    'plan_name': plan.name
                }
            }
            
            order = self.client.order.create(data=order_data)
            
            # Create pending payment record
            payment = Payment.objects.create(
                user=user,
                plan=plan,
                amount=Decimal(amount / 100),  # Convert back to rupees for storage
                currency='INR',
                status='pending',
                gateway='razorpay',
                gateway_transaction_id=order['id'],
                metadata={
                    'razorpay_order_id': order['id'],
                    'amount_in_paise': amount
                }
            )
            
            return {
                'success': True,
                'order_id': order['id'],
                'amount': amount,
                'currency': 'INR',
                'key_id': self.key_id,
                'payment_id': str(payment.id),
                'user_email': user.email,
                'user_name': user.get_full_name() or user.username
            }
            
        except Exception as e:
            logger.error(f"Error creating Razorpay order: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment(
        self, 
        razorpay_order_id: str, 
        razorpay_payment_id: str, 
        razorpay_signature: str
    ) -> Tuple[bool, str]:
        """
        Verify Razorpay payment signature
        """
        try:
            # Verify signature
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            
            self.client.utility.verify_payment_signature(params_dict)
            
            # Update payment status
            with transaction.atomic():
                payment = Payment.objects.filter(
                    gateway_transaction_id=razorpay_order_id
                ).first()
                
                if payment:
                    payment.status = 'completed'
                    payment.metadata['razorpay_payment_id'] = razorpay_payment_id
                    payment.metadata['razorpay_signature'] = razorpay_signature
                    payment.save()
                    
                    # Create or update subscription
                    UserSubscription.objects.update_or_create(
                        user=payment.user,
                        defaults={
                            'plan': payment.plan,
                            'status': 'active',
                            'start_date': timezone.now(),
                            'current_period_end': timezone.now() + timezone.timedelta(
                                days=30 if payment.plan.billing_cycle == 'monthly' else 365
                            )
                        }
                    )
                    
                    # Log payment history
                    PaymentHistory.objects.create(
                        payment=payment,
                        action='payment_verified',
                        metadata={
                            'razorpay_payment_id': razorpay_payment_id,
                            'verified_at': timezone.now().isoformat()
                        }
                    )
            
            return True, "Payment verified successfully"
            
        except razorpay.errors.SignatureVerificationError:
            logger.error("Razorpay signature verification failed")
            return False, "Payment verification failed"
        except Exception as e:
            logger.error(f"Error verifying Razorpay payment: {str(e)}")
            return False, str(e)
    
    def process_webhook(self, payload: Dict[str, Any], signature: str) -> Tuple[bool, str]:
        """Process Razorpay webhook"""
        try:
            # Verify webhook signature
            webhook_body = json.dumps(payload, separators=(',', ':'))
            if not PaymentConfig.validate_webhook_signature(webhook_body, signature, 'razorpay'):
                return False, "Invalid signature"
            
            event = payload.get('event')
            
            if event == 'payment.captured':
                self._handle_payment_captured(payload['payload']['payment']['entity'])
            elif event == 'payment.failed':
                self._handle_payment_failed(payload['payload']['payment']['entity'])
            elif event == 'subscription.activated':
                self._handle_subscription_activated(payload['payload']['subscription']['entity'])
            elif event == 'subscription.cancelled':
                self._handle_subscription_cancelled(payload['payload']['subscription']['entity'])
            
            return True, "Webhook processed successfully"
            
        except Exception as e:
            logger.error(f"Error processing Razorpay webhook: {str(e)}")
            return False, str(e)
    
    def _handle_payment_captured(self, payment_entity):
        """Handle captured payment from Razorpay"""
        # Update payment status to completed
        order_id = payment_entity.get('order_id')
        if order_id:
            Payment.objects.filter(gateway_transaction_id=order_id).update(
                status='completed',
                metadata={'razorpay_payment': payment_entity}
            )
    
    def _handle_payment_failed(self, payment_entity):
        """Handle failed payment from Razorpay"""
        order_id = payment_entity.get('order_id')
        if order_id:
            Payment.objects.filter(gateway_transaction_id=order_id).update(
                status='failed',
                metadata={'failure_reason': payment_entity.get('error_description')}
            )
    
    def _handle_subscription_activated(self, subscription_entity):
        """Handle subscription activation"""
        # Implementation for subscription activation
        pass
    
    def _handle_subscription_cancelled(self, subscription_entity):
        """Handle subscription cancellation"""
        # Implementation for subscription cancellation
        pass
    
    def create_subscription(
        self, 
        user, 
        plan,
        payment_method: str = 'card'
    ) -> Dict[str, Any]:
        """Create Razorpay subscription for recurring payments"""
        try:
            from .payment_config import RAZORPAY_PLAN_IDS
            plan_key = f"{plan.plan_type}_{plan.billing_cycle}"
            plan_id = RAZORPAY_PLAN_IDS.get(plan_key)
            
            if not plan_id:
                # Create plan if doesn't exist
                plan_id = self._create_subscription_plan(plan)
            
            subscription_data = {
                'plan_id': plan_id,
                'customer_notify': 1,
                'total_count': 12 if plan.billing_cycle == 'monthly' else 1,
                'notes': {
                    'user_id': str(user.id),
                    'user_email': user.email
                }
            }
            
            subscription = self.client.subscription.create(data=subscription_data)
            
            return {
                'success': True,
                'subscription_id': subscription['id'],
                'short_url': subscription.get('short_url'),
                'key_id': self.key_id
            }
            
        except Exception as e:
            logger.error(f"Error creating Razorpay subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_subscription_plan(self, plan) -> str:
        """Create subscription plan in Razorpay"""
        plan_data = {
            'period': plan.billing_cycle,
            'interval': 1,
            'item': {
                'name': plan.name,
                'amount': PaymentConfig.format_amount_for_gateway(plan.price, 'INR', 'razorpay'),
                'currency': 'INR',
                'description': plan.description
            }
        }
        
        created_plan = self.client.plan.create(data=plan_data)
        return created_plan['id']


class PaymentGatewayFactory:
    """Factory class to get appropriate payment gateway"""
    
    @staticmethod
    def get_gateway(gateway_name: str):
        """
        Get payment gateway instance
        Args:
            gateway_name: 'stripe' or 'razorpay'
        Returns:
            Gateway instance
        """
        if gateway_name.lower() == 'stripe':
            return StripeGateway()
        elif gateway_name.lower() == 'razorpay':
            return RazorpayGateway()
        else:
            raise ValueError(f"Unknown payment gateway: {gateway_name}")
    
    @staticmethod
    def get_gateway_for_user(user, user_country: Optional[str] = None):
        """Get appropriate gateway based on user location"""
        gateway_name = PaymentConfig.get_active_gateway(user_country)
        return PaymentGatewayFactory.get_gateway(gateway_name)