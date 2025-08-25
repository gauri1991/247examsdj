"""
Django Management Command: Generate Invoices
Generate PDF invoices for completed payments
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta

from payments.models import Payment
from payments.invoice_generator import BulkInvoiceGenerator


class Command(BaseCommand):
    help = 'Generate PDF invoices for completed payments'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--payment-id',
            type=str,
            help='Generate invoice for specific payment ID',
        )
        
        parser.add_argument(
            '--days-back',
            type=int,
            default=30,
            help='Generate invoices for payments from last N days (default: 30)',
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerate invoices even if they already exist',
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually generating invoices',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting invoice generation...')
        )
        
        # Get payments to process
        if options['payment_id']:
            # Single payment
            try:
                payments = Payment.objects.filter(
                    id=options['payment_id'],
                    status='completed'
                )
                if not payments.exists():
                    raise CommandError(f'Payment {options["payment_id"]} not found or not completed')
            except ValueError:
                raise CommandError(f'Invalid payment ID: {options["payment_id"]}')
        else:
            # Bulk payments
            since_date = timezone.now() - timedelta(days=options['days_back'])
            payments = Payment.objects.filter(
                status='completed',
                created_at__gte=since_date
            )
            
            # Exclude payments with existing invoices unless force is specified
            if not options['force']:
                payments = payments.exclude(metadata__invoice_generated=True)
        
        if not payments.exists():
            self.stdout.write(
                self.style.WARNING('No payments found to process.')
            )
            return
        
        self.stdout.write(
            f'Found {payments.count()} payment(s) to process.'
        )
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No invoices will be generated.')
            )
            for payment in payments[:10]:  # Show first 10
                self.stdout.write(
                    f'  - Payment {payment.id}: {payment.user.email} - {payment.currency} {payment.amount}'
                )
            if payments.count() > 10:
                self.stdout.write(f'  ... and {payments.count() - 10} more')
            return
        
        # Generate invoices
        bulk_generator = BulkInvoiceGenerator()
        
        if options['payment_id']:
            # Single invoice
            payment = payments.first()
            try:
                if options['force']:
                    filepath = bulk_generator.regenerate_invoice(payment)
                else:
                    filepath = bulk_generator.generator.save_invoice(payment)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully generated invoice for payment {payment.id}: {filepath}'
                    )
                )
            except Exception as e:
                raise CommandError(f'Failed to generate invoice: {str(e)}')
        else:
            # Bulk invoices
            results = bulk_generator.generate_bulk_invoices(payments)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully generated {results["success_count"]} invoices'
                )
            )
            
            if results['error_count'] > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'Failed to generate {results["error_count"]} invoices'
                    )
                )
                
                # Show first few errors
                for error in results['errors'][:5]:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  - Payment {error["payment_id"]}: {error["error"]}'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS('Invoice generation completed.')
        )