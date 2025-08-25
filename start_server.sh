#!/bin/bash

# Django Exam Portal Startup Script

echo "🚀 Starting Django Exam Portal..."
echo "================================="

# Activate virtual environment
source venv/bin/activate

# Check if database needs migration
echo "📊 Checking database..."
python manage.py migrate --check > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️  Running database migrations..."
    python manage.py migrate
fi

# Create superuser if none exists
echo "👤 Checking for admin user..."
python manage.py shell -c "
from users.models import User
if not User.objects.filter(role='admin').exists():
    User.objects.create_user(
        username='admin', 
        email='admin@example.com', 
        password='admin123', 
        role='admin', 
        first_name='Admin', 
        last_name='User'
    )
    print('✅ Created admin user: admin/admin123')
else:
    print('✅ Admin user exists')
"

# Collect static files if needed
if [ ! -d "staticfiles" ]; then
    echo "📁 Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo ""
echo "🎯 Server Configuration:"
echo "   - Security Level: Development (rate limiting disabled)"
echo "   - Cache: Local memory (no Redis required)"
echo "   - Debug Mode: Enabled"
echo "   - Admin: http://localhost:8001/admin/ (admin/admin123)"
echo ""

# Start the server
echo "🌐 Starting server on http://localhost:8001..."
echo "   Press Ctrl+C to stop"
echo ""

python manage.py runserver 8001