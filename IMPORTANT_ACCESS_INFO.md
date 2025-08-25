# IMPORTANT: How to Access the Django Development Server

## ⚠️ USE HTTP, NOT HTTPS!

The Django development server only supports HTTP connections.

### ✅ CORRECT URLs:
- `http://dts.com:8000` (NOT https://)
- `http://192.168.29.81:8000` (NOT https://)
- `http://localhost:8000` (NOT https://)

### ❌ WRONG URLs (will cause errors):
- `https://dts.com:8000`
- `https://192.168.29.81:8000`
- `https://localhost:8000`

## Common Issues and Solutions:

### 1. Browser Auto-Redirecting to HTTPS
Some browsers automatically try to use HTTPS. To fix:

**Chrome/Edge:**
- Type the URL with `http://` explicitly
- If redirected to HTTPS, go to: `chrome://net-internals/#hsts`
- Under "Delete domain security policies", enter `dts.com`
- Click "Delete"

**Firefox:**
- Clear browsing data for the site
- Or use private/incognito mode

### 2. Browser Shows Security Warning
This is normal for development. The dev server doesn't have SSL certificates.

### 3. If You Need HTTPS (Advanced)
For development with HTTPS, you have options:
1. Use `django-sslserver` package
2. Set up a reverse proxy with nginx
3. Use a tool like `mkcert` for local certificates

But for normal development, HTTP is fine.

## Quick Test
Open a new incognito/private browser window and go to:
`http://dts.com:8000`

Make sure to type the full URL including `http://`