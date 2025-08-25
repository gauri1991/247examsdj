from django.core.management.base import BaseCommand
from django.utils import timezone
from pdf_extractor.cleanup import cleanup_manager
import json


class Command(BaseCommand):
    help = 'Clean up temporary files and old PDF documents'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned without actually cleaning',
        )
        
        parser.add_argument(
            '--type',
            type=str,
            choices=['all', 'temp', 'documents', 'jobs'],
            default='all',
            help='Type of cleanup to perform',
        )
        
        parser.add_argument(
            '--age-days',
            type=int,
            help='Override default document age threshold (days)',
        )
        
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output results as JSON',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        cleanup_type = options['type']
        age_days = options.get('age_days')
        json_output = options['json']
        
        if age_days:
            cleanup_manager.max_file_age_days = age_days
        
        if dry_run:
            # Just show summary
            summary = cleanup_manager.get_cleanup_summary()
            
            if json_output:
                self.stdout.write(json.dumps(summary, indent=2))
            else:
                self.stdout.write(self.style.WARNING("DRY RUN - No files will be deleted"))
                self.stdout.write(f"\nItems pending cleanup:")
                self.stdout.write(f"  Old documents: {summary['old_documents']}")
                self.stdout.write(f"  Failed jobs: {summary['failed_jobs']}")
                self.stdout.write(f"  Temp files: {summary['temp_files']}")
        else:
            # Perform actual cleanup
            self.stdout.write("Starting cleanup process...")
            
            if cleanup_type == 'all':
                results = cleanup_manager.perform_full_cleanup()
            elif cleanup_type == 'temp':
                results = {'temp_files': cleanup_manager.cleanup_temporary_files()}
            elif cleanup_type == 'documents':
                results = {'old_documents': cleanup_manager.cleanup_old_documents()}
            elif cleanup_type == 'jobs':
                results = {'failed_jobs': cleanup_manager.cleanup_failed_jobs()}
            
            if json_output:
                self.stdout.write(json.dumps(results, indent=2))
            else:
                self._display_results(results)
    
    def _display_results(self, results):
        """
        Display cleanup results in a formatted way
        """
        self.stdout.write(self.style.SUCCESS("\nCleanup completed!"))
        
        if 'temp_files' in results:
            temp = results['temp_files']
            self.stdout.write(f"\nTemporary files:")
            self.stdout.write(f"  Files removed: {temp['files_removed']}")
            self.stdout.write(f"  Bytes freed: {temp['bytes_freed']:,}")
            if temp['errors']:
                self.stdout.write(self.style.ERROR(f"  Errors: {len(temp['errors'])}"))
        
        if 'old_documents' in results:
            docs = results['old_documents']
            self.stdout.write(f"\nOld documents:")
            self.stdout.write(f"  Documents removed: {docs['documents_removed']}")
            self.stdout.write(f"  Questions removed: {docs['questions_removed']}")
            self.stdout.write(f"  Jobs removed: {docs['jobs_removed']}")
            self.stdout.write(f"  Bytes freed: {docs['bytes_freed']:,}")
            if docs['errors']:
                self.stdout.write(self.style.ERROR(f"  Errors: {len(docs['errors'])}"))
        
        if 'failed_jobs' in results:
            jobs = results['failed_jobs']
            self.stdout.write(f"\nFailed jobs:")
            self.stdout.write(f"  Jobs cleaned: {jobs['jobs_cleaned']}")
            if jobs['errors']:
                self.stdout.write(self.style.ERROR(f"  Errors: {len(jobs['errors'])}"))
        
        if 'totals' in results:
            totals = results['totals']
            self.stdout.write(self.style.SUCCESS(f"\nTotal:"))
            self.stdout.write(f"  Files removed: {totals['files_removed']}")
            self.stdout.write(f"  Documents removed: {totals['documents_removed']}")
            self.stdout.write(f"  Bytes freed: {totals['bytes_freed']:,}")
            if totals['total_errors'] > 0:
                self.stdout.write(self.style.ERROR(f"  Total errors: {totals['total_errors']}"))