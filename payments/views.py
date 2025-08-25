from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q, Sum
from django.db import models
from datetime import timedelta
import json
import uuid
import logging

from .models import SubscriptionPlan, UserSubscription, Payment, Discount, PaymentHistory
from .payment_gateways import PaymentGatewayFactory
from .payment_config import PaymentConfig
from .invoice_generator import InvoiceGenerator, BulkInvoiceGenerator

logger = logging.getLogger(__name__)


def is_admin(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_admin)
def admin_subscription_management(request):
    """Admin view for managing subscription plans and user subscriptions"""
    if request.method == 'POST':
        # Handle AJAX requests for creating plans, etc.
        import json
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'create_plan':
                plan = SubscriptionPlan.objects.create(
                    name=data.get('name'),
                    plan_type=data.get('plan_type'),
                    price=data.get('price'),
                    billing_cycle=data.get('billing_cycle'),
                    description=data.get('description', ''),
                    max_tests=int(data.get('max_tests', 10)),
                    max_questions=int(data.get('max_questions', 100)),
                    trial_days=int(data.get('trial_days', 0)),
                    pdf_extraction=data.get('pdf_extraction', False),
                    analytics_access=data.get('analytics_access', False),
                    priority_support=data.get('priority_support', False),
                    custom_branding=data.get('custom_branding', False),
                    api_access=data.get('api_access', False),
                )
                return JsonResponse({'success': True, 'plan_id': str(plan.id)})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    plans = SubscriptionPlan.objects.all().order_by('price')
    subscriptions = UserSubscription.objects.select_related('user', 'plan').order_by('-created_at')
    payments = Payment.objects.select_related('user', 'plan').order_by('-created_at')[:10]
    
    # Statistics
    active_subscriptions = UserSubscription.objects.filter(status='active').count()
    total_revenue = Payment.objects.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    active_discounts = Discount.objects.filter(is_active=True, valid_until__gte=timezone.now()).count()
    
    context = {
        'plans': plans,
        'subscriptions': subscriptions,
        'payments': payments,
        'stats': {
            'active_subscriptions': active_subscriptions,
            'total_revenue': total_revenue,
            'total_users': subscriptions.count(),
        },
        'active_discounts': active_discounts,
    }
    return render(request, 'payments/subscription_management.html', context)


@login_required
def subscription_plans(request):
    """View subscription plans for users"""
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
    user_subscription = None
    
    try:
        user_subscription = UserSubscription.objects.get(
            user=request.user, 
            status__in=['active', 'trial']
        )
    except UserSubscription.DoesNotExist:
        pass
    
    context = {
        'plans': plans,
        'user_subscription': user_subscription
    }
    return render(request, 'payments/subscription_plans.html', context)


@login_required
@require_POST
def create_subscription(request):
    """Create a new subscription for the user"""
    plan_id = request.POST.get('plan_id')
    discount_code = request.POST.get('discount_code', '').strip()
    
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        return JsonResponse({'error': 'Invalid subscription plan'}, status=400)
    
    # Check if user already has an active subscription
    existing_subscription = UserSubscription.objects.filter(
        user=request.user,
        status__in=['active', 'trial']
    ).first()
    
    if existing_subscription:
        return JsonResponse({'error': 'You already have an active subscription'}, status=400)
    
    # Calculate pricing
    amount = plan.price
    discount = None
    
    # Apply discount if provided
    if discount_code:
        try:
            discount = Discount.objects.get(
                code=discount_code,
                is_active=True,
                valid_from__lte=timezone.now(),
                valid_until__gte=timezone.now()
            )
            if discount.is_valid and (not discount.applicable_plans.exists() or plan in discount.applicable_plans.all()):
                discount_amount = discount.calculate_discount(amount)
                amount -= discount_amount
        except Discount.DoesNotExist:
            return JsonResponse({'error': 'Invalid discount code'}, status=400)
    
    # Calculate subscription dates
    start_date = timezone.now()
    if plan.billing_cycle == 'monthly':
        end_date = start_date + timedelta(days=30)
    elif plan.billing_cycle == 'yearly':
        end_date = start_date + timedelta(days=365)
    else:  # lifetime
        end_date = start_date + timedelta(days=36500)  # 100 years
    
    # Determine payment gateway based on user location or preference
    payment_method = request.POST.get('payment_method', 'razorpay')  # Default to Razorpay for India
    user_country = request.POST.get('country', 'IN')  # Default to India
    gateway_name = PaymentConfig.get_active_gateway(user_country)
    
    # Override with user preference if specified
    if payment_method in ['stripe', 'razorpay']:
        gateway_name = payment_method
    
    # Get the appropriate gateway
    gateway = PaymentGatewayFactory.get_gateway(gateway_name)
    
    # Process payment based on gateway
    if gateway_name == 'stripe':
        # Create Stripe checkout session
        success_url = request.build_absolute_uri('/payments/success/')
        cancel_url = request.build_absolute_uri('/payments/cancel/')
        
        result = gateway.create_checkout_session(
            user=request.user,
            plan=plan,
            success_url=success_url,
            cancel_url=cancel_url,
            discount_code=discount_code
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'gateway': 'stripe',
                'checkout_url': result['checkout_url'],
                'session_id': result['session_id'],
                'publishable_key': result['publishable_key']
            })
        else:
            return JsonResponse({'error': result['error']}, status=400)
    
    elif gateway_name == 'razorpay':
        # Create Razorpay order
        result = gateway.create_order(
            user=request.user,
            plan=plan,
            discount_code=discount_code
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'gateway': 'razorpay',
                'order_id': result['order_id'],
                'amount': result['amount'],
                'currency': result['currency'],
                'key_id': result['key_id'],
                'payment_id': result['payment_id'],
                'user_email': result['user_email'],
                'user_name': result['user_name']
            })
        else:
            return JsonResponse({'error': result['error']}, status=400)
    
    else:
        return JsonResponse({'error': 'Invalid payment gateway'}, status=400)


@login_required
def subscription_status(request):
    """Get current subscription status"""
    try:
        subscription = UserSubscription.objects.get(
            user=request.user,
            status__in=['active', 'trial']
        )
        
        return JsonResponse({
            'has_subscription': True,
            'plan_name': subscription.plan.name,
            'status': subscription.status,
            'end_date': subscription.end_date.isoformat(),
            'days_remaining': subscription.days_remaining,
            'features': subscription.plan.features_list
        })
    except UserSubscription.DoesNotExist:
        return JsonResponse({'has_subscription': False})


@login_required
@require_POST
def cancel_subscription(request):
    """Cancel user's subscription"""
    try:
        subscription = UserSubscription.objects.get(
            user=request.user,
            status='active'
        )
        
        subscription.status = 'cancelled'
        subscription.cancelled_at = timezone.now()
        subscription.auto_renew = False
        subscription.save()
        
        # Create payment history
        PaymentHistory.objects.create(
            user=request.user,
            subscription=subscription,
            action='subscription_cancelled',
            description=f"Cancelled subscription for {subscription.plan.name}"
        )
        
        messages.success(request, 'Your subscription has been cancelled successfully.')
        return JsonResponse({'success': True})
        
    except UserSubscription.DoesNotExist:
        return JsonResponse({'error': 'No active subscription found'}, status=400)


@require_POST
def validate_discount(request):
    """Validate discount code"""
    discount_code = request.POST.get('code', '').strip()
    plan_id = request.POST.get('plan_id')
    
    if not discount_code:
        return JsonResponse({'valid': False, 'error': 'Discount code is required'})
    
    try:
        discount = Discount.objects.get(code=discount_code)
        plan = SubscriptionPlan.objects.get(id=plan_id) if plan_id else None
        
        if not discount.is_valid:
            return JsonResponse({'valid': False, 'error': 'Discount code is not valid'})
        
        # Check if discount applies to the plan
        if plan and discount.applicable_plans.exists() and plan not in discount.applicable_plans.all():
            return JsonResponse({'valid': False, 'error': 'Discount code not applicable to this plan'})
        
        discount_amount = discount.calculate_discount(plan.price if plan else 100)
        
        return JsonResponse({
            'valid': True,
            'discount_type': discount.discount_type,
            'value': float(discount.value),
            'discount_amount': float(discount_amount),
            'description': discount.description or f"{discount.value}{'%' if discount.discount_type == 'percentage' else '$'} off"
        })
        
    except (Discount.DoesNotExist, SubscriptionPlan.DoesNotExist):
        return JsonResponse({'valid': False, 'error': 'Invalid discount code'})


@login_required
def payment_history(request):
    """View user's payment history"""
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    subscriptions = UserSubscription.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'payments': payments,
        'subscriptions': subscriptions
    }
    return render(request, 'payments/payment_history.html', context)


@user_passes_test(is_admin)
def admin_discount_management(request):
    """Admin view for managing discount codes"""
    discounts = Discount.objects.all().order_by('-created_at')
    plans = SubscriptionPlan.objects.filter(is_active=True)
    
    # Separate active and expired discounts
    active_discounts = []
    expired_discounts = []
    
    for discount in discounts:
        if discount.is_valid:
            active_discounts.append(discount)
        else:
            expired_discounts.append(discount)
    
    # Statistics
    active_count = len(active_discounts)
    total_uses = sum(discount.used_count for discount in discounts)
    total_savings = 0  # This would be calculated based on actual usage
    
    context = {
        'discounts': active_discounts,
        'expired_discounts': expired_discounts,
        'plans': plans,
        'active_count': active_count,
        'total_uses': total_uses,
        'total_savings': total_savings,
    }
    return render(request, 'payments/discount_management.html', context)


@user_passes_test(is_admin)
def admin_transaction_management(request):
    """Admin view for managing payment transactions"""
    payments = Payment.objects.select_related('user', 'plan').order_by('-created_at')
    
    # Statistics
    stats = {
        'completed': payments.filter(status='completed').count(),
        'pending': payments.filter(status='pending').count(),
        'failed': payments.filter(status='failed').count(),
        'total_volume': payments.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
    }
    
    context = {
        'payments': payments,
        'stats': stats,
    }
    return render(request, 'payments/transaction_management.html', context)


# Additional API endpoints for admin functions
@require_POST
def create_discount(request):
    """Create a new discount code"""
    try:
        data = json.loads(request.body)
        
        # Check if discount code already exists
        if Discount.objects.filter(code=data.get('code')).exists():
            return JsonResponse({'success': False, 'error': 'Discount code already exists'})
        
        # Parse dates
        from datetime import datetime
        valid_from = datetime.strptime(data.get('valid_from'), '%Y-%m-%d').date()
        valid_until = datetime.strptime(data.get('valid_until'), '%Y-%m-%d').date()
        
        discount = Discount.objects.create(
            code=data.get('code').upper(),
            name=data.get('name'),
            description=data.get('description', ''),
            discount_type=data.get('discount_type'),
            value=data.get('value'),
            valid_from=valid_from,
            valid_until=valid_until,
            max_uses=data.get('max_uses') if data.get('max_uses') else None,
            is_active=True
        )
        
        # Add applicable plans if specified
        applicable_plans = data.get('applicable_plans', [])
        if applicable_plans:
            plans = SubscriptionPlan.objects.filter(id__in=applicable_plans)
            discount.applicable_plans.set(plans)
        
        return JsonResponse({'success': True, 'discount_id': str(discount.id)})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def process_refund(request):
    """Process a refund for a payment"""
    try:
        data = json.loads(request.body)
        transaction_id = data.get('transaction_id')
        
        # This is a placeholder - in real implementation, you would integrate with payment gateway
        payment = Payment.objects.filter(
            gateway_transaction_id=transaction_id,
            status='completed'
        ).first()
        
        if not payment:
            return JsonResponse({'success': False, 'error': 'Transaction not found or not eligible for refund'})
        
        # Update payment status
        payment.status = 'refunded'
        payment.refunded_at = timezone.now()
        payment.save()
        
        # Create payment history
        PaymentHistory.objects.create(
            user=payment.user,
            payment=payment,
            action='refund_processed',
            description=f"Refund processed for transaction {transaction_id}"
        )
        
        return JsonResponse({'success': True, 'message': 'Refund processed successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def generate_invoices(request):
    """Generate PDF invoices for completed payments"""
    try:
        # Get completed payments without invoices
        payments_without_invoices = Payment.objects.filter(
            status='completed'
        ).exclude(
            metadata__invoice_generated=True
        )
        
        if not payments_without_invoices.exists():
            return JsonResponse({
                'success': True,
                'message': 'No payments found that need invoices'
            })
        
        # Generate invoices in bulk
        bulk_generator = BulkInvoiceGenerator()
        results = bulk_generator.generate_bulk_invoices(payments_without_invoices)
        
        return JsonResponse({
            'success': True,
            'message': f'Generated {results["success_count"]} invoices successfully',
            'details': {
                'success_count': results['success_count'],
                'error_count': results['error_count'],
                'total_count': results['total_count'],
                'errors': results['errors'][:5]  # Return first 5 errors
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating invoices: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': 'An error occurred while generating invoices'
        }, status=500)


@login_required
def download_invoice(request, payment_id):
    """Download invoice PDF for a specific payment"""
    try:
        payment = Payment.objects.get(id=payment_id, user=request.user)
        
        if payment.status != 'completed':
            return JsonResponse({'error': 'Invoice not available for this payment'}, status=400)
        
        generator = InvoiceGenerator()
        
        # Check if invoice already exists
        invoice_url = generator.get_invoice_url(payment)
        
        if not invoice_url:
            # Generate invoice if it doesn't exist
            filepath = generator.save_invoice(payment)
            invoice_url = default_storage.url(filepath)
        
        # Generate PDF and serve it
        pdf_buffer = generator.generate_invoice(payment)
        
        from django.http import HttpResponse
        response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{payment.id}.pdf"'
        
        return response
        
    except Payment.DoesNotExist:
        return JsonResponse({'error': 'Payment not found'}, status=404)
    except Exception as e:
        logger.error(f"Error downloading invoice: {str(e)}")
        return JsonResponse({'error': 'Error generating invoice'}, status=500)


@login_required
@require_POST
def regenerate_invoice(request):
    """Regenerate invoice for a payment"""
    payment_id = request.POST.get('payment_id')
    
    try:
        payment = Payment.objects.get(id=payment_id, user=request.user)
        
        if payment.status != 'completed':
            return JsonResponse({'error': 'Cannot generate invoice for incomplete payment'}, status=400)
        
        # Regenerate invoice
        bulk_generator = BulkInvoiceGenerator()
        filepath = bulk_generator.regenerate_invoice(payment)
        
        return JsonResponse({
            'success': True,
            'message': 'Invoice regenerated successfully',
            'download_url': f'/payments/invoice/{payment.id}/download/'
        })
        
    except Payment.DoesNotExist:
        return JsonResponse({'error': 'Payment not found'}, status=404)
    except Exception as e:
        logger.error(f"Error regenerating invoice: {str(e)}")
        return JsonResponse({'error': 'Error regenerating invoice'}, status=500)


# Webhook endpoints (for payment gateway integration)
@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not sig_header:
        logger.warning("Missing Stripe signature header")
        return HttpResponse(status=400)
    
    # Get Stripe gateway and process webhook
    gateway = PaymentGatewayFactory.get_gateway('stripe')
    success, message = gateway.process_webhook(payload.decode('utf-8'), sig_header)
    
    if success:
        return JsonResponse({'status': 'success'})
    else:
        logger.error(f"Stripe webhook processing failed: {message}")
        return HttpResponse(status=400)


@csrf_exempt  
@require_POST
def razorpay_webhook(request):
    """Handle Razorpay webhook events"""
    try:
        payload = json.loads(request.body)
        signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE')
        
        if not signature:
            logger.warning("Missing Razorpay signature header")
            return HttpResponse(status=400)
        
        # Get Razorpay gateway and process webhook
        gateway = PaymentGatewayFactory.get_gateway('razorpay')
        success, message = gateway.process_webhook(payload, signature)
        
        if success:
            return JsonResponse({'status': 'success'})
        else:
            logger.error(f"Razorpay webhook processing failed: {message}")
            return HttpResponse(status=400)
            
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload in Razorpay webhook")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Unexpected error in Razorpay webhook: {str(e)}")
        return HttpResponse(status=500)


@login_required
def payment_success(request):
    """Handle payment success page"""
    session_id = request.GET.get('session_id')
    payment_id = request.GET.get('payment_id')
    
    context = {
        'session_id': session_id,
        'payment_id': payment_id
    }
    
    # If it's a Stripe session, you could retrieve more details
    if session_id:
        try:
            import stripe
            stripe.api_key = PaymentConfig.get_stripe_config()['secret_key']
            session = stripe.checkout.Session.retrieve(session_id)
            
            context['amount'] = session.amount_total / 100  # Convert from cents
            context['currency'] = session.currency.upper()
        except Exception as e:
            logger.error(f"Error retrieving Stripe session: {str(e)}")
    
    return render(request, 'payments/success.html', context)


@login_required
def payment_cancel(request):
    """Handle payment cancellation page"""
    return render(request, 'payments/cancel.html')


@login_required
@require_POST
def verify_razorpay_payment(request):
    """Verify Razorpay payment after successful payment"""
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_signature = request.POST.get('razorpay_signature')
    
    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return JsonResponse({'error': 'Missing payment verification data'}, status=400)
    
    # Get Razorpay gateway and verify payment
    gateway = PaymentGatewayFactory.get_gateway('razorpay')
    success, message = gateway.verify_payment(
        razorpay_order_id, 
        razorpay_payment_id, 
        razorpay_signature
    )
    
    if success:
        return JsonResponse({
            'success': True,
            'message': message,
            'redirect_url': '/payments/success/'
        })
    else:
        return JsonResponse({
            'success': False,
            'error': message
        }, status=400)


@login_required
@require_POST
def process_refund(request):
    """Process refund for a payment"""
    payment_id = request.POST.get('payment_id')
    refund_amount = request.POST.get('refund_amount')
    reason = request.POST.get('reason', '')
    
    try:
        payment = Payment.objects.get(id=payment_id, user=request.user)
        
        if payment.status != 'completed':
            return JsonResponse({'error': 'Payment is not eligible for refund'}, status=400)
        
        # Determine which gateway to use
        gateway = PaymentGatewayFactory.get_gateway(payment.gateway)
        
        # Process refund based on gateway
        if payment.gateway == 'stripe':
            import stripe
            stripe.api_key = PaymentConfig.get_stripe_config()['secret_key']
            
            # Find the payment intent or charge
            if hasattr(gateway, 'process_refund'):
                success = gateway.process_refund(payment, refund_amount, reason)
            else:
                # Basic Stripe refund implementation
                try:
                    refund = stripe.Refund.create(
                        payment_intent=payment.transaction_id,
                        amount=int(float(refund_amount) * 100) if refund_amount else None,
                        reason=reason
                    )
                    success = True
                except stripe.error.StripeError:
                    success = False
                    
        elif payment.gateway == 'razorpay':
            # Razorpay refund implementation
            import razorpay
            razorpay_client = razorpay.Client(auth=(
                PaymentConfig.get_razorpay_config()['key_id'],
                PaymentConfig.get_razorpay_config()['key_secret']
            ))
            
            try:
                refund_amount_paise = int(float(refund_amount) * 100) if refund_amount else None
                refund = razorpay_client.payment.refund(
                    payment.metadata.get('razorpay_payment_id'),
                    {
                        'amount': refund_amount_paise,
                        'notes': {'reason': reason}
                    }
                )
                success = True
            except Exception:
                success = False
        else:
            success = False
        
        if success:
            # Update payment status
            payment.status = 'refunded' if not refund_amount else 'partially_refunded'
            payment.save()
            
            # Create payment history
            PaymentHistory.objects.create(
                user=request.user,
                payment=payment,
                action='refund_processed',
                description=f'Refund processed: {refund_amount or "full amount"} - {reason}'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Refund processed successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to process refund'
            }, status=400)
            
    except Payment.DoesNotExist:
        return JsonResponse({'error': 'Payment not found'}, status=404)
    except Exception as e:
        logger.error(f"Error processing refund: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while processing refund'
        }, status=500)