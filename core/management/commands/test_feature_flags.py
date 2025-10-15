"""
Management command to test feature flag system.
Usage: python manage.py test_feature_flags
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from core.features import FeatureFlags
from django.apps import apps


class Command(BaseCommand):
    help = 'Test feature flag system and show current configuration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('FEATURE FLAG SYSTEM TEST'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        # Test 1: Check if FEATURES setting exists
        self.stdout.write(self.style.NOTICE('Test 1: FEATURES configuration'))
        if hasattr(settings, 'FEATURES'):
            self.stdout.write(self.style.SUCCESS('✓ FEATURES setting exists'))
        else:
            self.stdout.write(self.style.ERROR('✗ FEATURES setting not found'))
            return

        # Test 2: List all feature flags
        self.stdout.write(self.style.NOTICE('\nTest 2: All feature flags'))
        all_features = FeatureFlags.get_all()
        for feature, enabled in all_features.items():
            status = '✓ ENABLED' if enabled else '✗ DISABLED'
            style = self.style.SUCCESS if enabled else self.style.WARNING
            self.stdout.write(f'  {style(status)} - {feature}')

        # Test 3: Test individual feature checks
        self.stdout.write(self.style.NOTICE('\nTest 3: Individual feature checks'))
        test_features = [
            'PDF_EXTRACTOR_ENABLED',
            'PAYMENT_SYSTEM_ENABLED',
            'AI_GRADING_ENABLED',
            'PROCTORING_ENABLED',
        ]
        for feature in test_features:
            is_enabled = FeatureFlags.is_enabled(feature)
            status = '✓ ENABLED' if is_enabled else '✗ DISABLED'
            style = self.style.SUCCESS if is_enabled else self.style.WARNING
            self.stdout.write(f'  {style(status)} - {feature}')

        # Test 4: Check app loading
        self.stdout.write(self.style.NOTICE('\nTest 4: Conditional app loading'))
        installed_apps = [app.name for app in apps.get_app_configs()]

        # Check PDF extractor
        pdf_enabled = FeatureFlags.is_enabled('PDF_EXTRACTOR_ENABLED')
        pdf_loaded = 'pdf_extractor' in installed_apps
        if pdf_enabled == pdf_loaded:
            self.stdout.write(self.style.SUCCESS(
                f'  ✓ PDF Extractor: Flag={pdf_enabled}, Loaded={pdf_loaded} (MATCH)'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f'  ✗ PDF Extractor: Flag={pdf_enabled}, Loaded={pdf_loaded} (MISMATCH!)'
            ))

        # Check payments
        payment_enabled = FeatureFlags.is_enabled('PAYMENT_SYSTEM_ENABLED')
        payment_loaded = 'payments' in installed_apps
        if payment_enabled == payment_loaded:
            self.stdout.write(self.style.SUCCESS(
                f'  ✓ Payments: Flag={payment_enabled}, Loaded={payment_loaded} (MATCH)'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f'  ✗ Payments: Flag={payment_enabled}, Loaded={payment_loaded} (MISMATCH!)'
            ))

        # Test 5: Celery task routing (if PDF extractor is enabled)
        self.stdout.write(self.style.NOTICE('\nTest 5: Celery task routing'))
        if pdf_enabled:
            if hasattr(settings, 'CELERY_TASK_ROUTES'):
                self.stdout.write(self.style.SUCCESS(
                    '  ✓ CELERY_TASK_ROUTES configured for PDF extractor'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    '  ⚠ CELERY_TASK_ROUTES not found (may not be needed)'
                ))
        else:
            if hasattr(settings, 'CELERY_TASK_ROUTES'):
                self.stdout.write(self.style.WARNING(
                    '  ⚠ CELERY_TASK_ROUTES exists but PDF extractor disabled'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    '  ✓ CELERY_TASK_ROUTES not configured (as expected)'
                ))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('FEATURE FLAG SYSTEM TEST COMPLETE'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        # Show instructions
        self.stdout.write(self.style.NOTICE('To disable PDF extractor in production:'))
        self.stdout.write('  1. Edit .env file')
        self.stdout.write('  2. Set: PDF_EXTRACTOR_ENABLED=false')
        self.stdout.write('  3. Restart Django server')
        self.stdout.write('  4. Result: Saves ~17GB RAM + 6-14 CPU cores\n')
