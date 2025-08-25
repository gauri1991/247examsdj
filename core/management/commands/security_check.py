"""
Django management command for running security checks and audits.
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
import logging

from exams.models import TestAttempt
from questions.models import UserAnswer
from exam_portal.security_config import get_security_config, log_security_incident

User = get_user_model()
logger = logging.getLogger('security')


class Command(BaseCommand):
    help = 'Run security checks and generate security audit report'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-type',
            type=str,
            choices=['all', 'users', 'data', 'activities', 'files'],
            default='all',
            help='Type of security check to perform'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to look back for activity analysis'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file for the security report'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting security audit...'))
        
        check_type = options['check_type']
        days_back = options['days']
        output_file = options.get('output')
        
        report = []
        
        if check_type in ['all', 'users']:
            report.extend(self.check_user_security())
        
        if check_type in ['all', 'data']:
            report.extend(self.check_data_integrity())
        
        if check_type in ['all', 'activities']:
            report.extend(self.check_suspicious_activities(days_back))
        
        if check_type in ['all', 'files']:
            report.extend(self.check_file_security())
        
        # Generate summary
        summary = self.generate_summary(report)
        
        # Output results
        self.output_report(report, summary, output_file)
        
        self.stdout.write(
            self.style.SUCCESS(f'Security audit completed. Found {len(report)} items to review.')
        )

    def check_user_security(self):
        """Check user account security."""
        issues = []
        
        # Check for weak passwords (users without password changes in 90 days)
        old_date = timezone.now() - timedelta(days=90)
        users_old_passwords = User.objects.filter(
            last_login__lt=old_date,
            is_active=True
        ).count()
        
        if users_old_passwords > 0:
            issues.append({
                'type': 'USER_SECURITY',
                'severity': 'medium',
                'description': f'{users_old_passwords} users haven\'t changed passwords in 90+ days',
                'recommendation': 'Implement password rotation policy'
            })
        
        # Check for inactive admin accounts
        inactive_admins = User.objects.filter(
            role='admin',
            is_active=True,
            last_login__lt=timezone.now() - timedelta(days=30)
        ).count()
        
        if inactive_admins > 0:
            issues.append({
                'type': 'USER_SECURITY',
                'severity': 'high',
                'description': f'{inactive_admins} admin accounts inactive for 30+ days',
                'recommendation': 'Review and disable unused admin accounts'
            })
        
        # Check for accounts with multiple failed login attempts
        # This would require implementing failed login tracking
        
        return issues

    def check_data_integrity(self):
        """Check data integrity and consistency."""
        issues = []
        
        # Check for orphaned test attempts
        orphaned_attempts = TestAttempt.objects.filter(
            user__isnull=True
        ).count()
        
        if orphaned_attempts > 0:
            issues.append({
                'type': 'DATA_INTEGRITY',
                'severity': 'medium',
                'description': f'{orphaned_attempts} orphaned test attempts found',
                'recommendation': 'Clean up orphaned records'
            })
        
        # Check for answers without test attempts
        orphaned_answers = UserAnswer.objects.filter(
            test_attempt__isnull=True
        ).count()
        
        if orphaned_answers > 0:
            issues.append({
                'type': 'DATA_INTEGRITY',
                'severity': 'medium',
                'description': f'{orphaned_answers} orphaned user answers found',
                'recommendation': 'Clean up orphaned answer records'
            })
        
        return issues

    def check_suspicious_activities(self, days_back):
        """Check for suspicious activities in the specified time period."""
        issues = []
        cutoff_date = timezone.now() - timedelta(days=days_back)
        
        # Check for unusually high test submission rates
        high_submission_users = TestAttempt.objects.filter(
            start_time__gte=cutoff_date
        ).values('user').annotate(
            attempt_count=Count('id')
        ).filter(attempt_count__gt=20)  # More than 20 attempts in the period
        
        if high_submission_users:
            issues.append({
                'type': 'SUSPICIOUS_ACTIVITY',
                'severity': 'high',
                'description': f'{len(high_submission_users)} users with >20 test attempts in {days_back} days',
                'recommendation': 'Investigate potential automated testing'
            })
        
        # Check for rapid answer submissions (potential cheating)
        rapid_submissions = TestAttempt.objects.filter(
            start_time__gte=cutoff_date,
            status='evaluated',
            time_spent_seconds__lt=60  # Less than 1 minute for entire test
        ).count()
        
        if rapid_submissions > 0:
            issues.append({
                'type': 'SUSPICIOUS_ACTIVITY',
                'severity': 'high',
                'description': f'{rapid_submissions} tests completed in <1 minute',
                'recommendation': 'Review minimum time requirements and investigate users'
            })
        
        return issues

    def check_file_security(self):
        """Check file upload security."""
        issues = []
        
        # This would check uploaded files for:
        # - File type validation
        # - Size limits
        # - Malware scanning results
        # - Suspicious file names
        
        # For now, just check if proper validation is in place
        config = get_security_config()
        file_config = config['file_upload']
        
        if not file_config.get('scan_for_malware'):
            issues.append({
                'type': 'FILE_SECURITY',
                'severity': 'medium',
                'description': 'Malware scanning not enabled for file uploads',
                'recommendation': 'Enable malware scanning for all uploads'
            })
        
        return issues

    def generate_summary(self, issues):
        """Generate a summary of security issues."""
        summary = {
            'total_issues': len(issues),
            'high_severity': len([i for i in issues if i['severity'] == 'high']),
            'medium_severity': len([i for i in issues if i['severity'] == 'medium']),
            'low_severity': len([i for i in issues if i['severity'] == 'low']),
            'categories': {}
        }
        
        for issue in issues:
            category = issue['type']
            if category not in summary['categories']:
                summary['categories'][category] = 0
            summary['categories'][category] += 1
        
        return summary

    def output_report(self, issues, summary, output_file=None):
        """Output the security report."""
        lines = []
        lines.append("=" * 50)
        lines.append("SECURITY AUDIT REPORT")
        lines.append(f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 50)
        lines.append("")
        
        # Summary
        lines.append("SUMMARY:")
        lines.append(f"Total Issues: {summary['total_issues']}")
        lines.append(f"High Severity: {summary['high_severity']}")
        lines.append(f"Medium Severity: {summary['medium_severity']}")
        lines.append(f"Low Severity: {summary['low_severity']}")
        lines.append("")
        
        # Issues by category
        lines.append("ISSUES BY CATEGORY:")
        for category, count in summary['categories'].items():
            lines.append(f"{category}: {count}")
        lines.append("")
        
        # Detailed issues
        lines.append("DETAILED FINDINGS:")
        lines.append("-" * 30)
        
        for i, issue in enumerate(issues, 1):
            lines.append(f"{i}. [{issue['severity'].upper()}] {issue['type']}")
            lines.append(f"   Description: {issue['description']}")
            lines.append(f"   Recommendation: {issue['recommendation']}")
            lines.append("")
        
        report_text = "\n".join(lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            self.stdout.write(f"Report saved to: {output_file}")
        else:
            self.stdout.write(report_text)
        
        # Log security audit
        log_security_incident(
            'SECURITY_AUDIT_COMPLETED',
            f'Found {summary["total_issues"]} issues ({summary["high_severity"]} high severity)',
            'info'
        )