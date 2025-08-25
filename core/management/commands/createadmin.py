from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create admin users quickly'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the admin')
        parser.add_argument('--password', type=str, default='admin123', help='Password (default: admin123)')
        parser.add_argument('--email', type=str, help='Email address')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options.get('email') or f"{username}@example.com"

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists'))
            user = User.objects.get(username=username)
            if not user.is_superuser:
                user.is_staff = True
                user.is_superuser = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Updated "{username}" to superuser'))
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Created admin user "{username}"'))
            self.stdout.write(f'Password: {password}')
            self.stdout.write(f'Email: {email}')