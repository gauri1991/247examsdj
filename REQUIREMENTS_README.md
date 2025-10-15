# Requirements Files Structure

## Overview

This project uses multiple requirements files to optimize deployment and avoid unnecessary dependencies.

---

## File Structure

```
requirements-base.txt           # Core packages (NO GPU/CUDA)
requirements-ocr.txt            # OCR with GPU support (OPTIONAL, ~5GB)
requirements-production.txt     # Production deployment (uses base)
requirements.txt                # Development (includes OCR)
```

---

## Requirements Files

### 1. `requirements-base.txt` ⭐ RECOMMENDED FOR PRODUCTION

**What it includes:**
- Django and core framework
- PostgreSQL, Redis
- Celery (configuration only)
- All production features EXCEPT OCR/GPU

**What it EXCLUDES:**
- ❌ PyTorch (~2GB)
- ❌ NVIDIA CUDA packages (~3GB)
- ❌ EasyOCR and GPU dependencies

**Size:** ~500MB (vs 5GB with GPU packages)

**Use this for:**
- ✅ Production deployment
- ✅ VPS without GPU
- ✅ When `PDF_EXTRACTOR_ENABLED=false`
- ✅ Docker containers
- ✅ Fast deployment

**Install:**
```bash
pip install -r requirements-base.txt
```

---

### 2. `requirements-ocr.txt` (OPTIONAL)

**What it includes:**
- Everything from `requirements-base.txt`
- PyTorch with CUDA support
- 12 NVIDIA CUDA packages
- EasyOCR (deep learning OCR)
- OpenCV with GPU acceleration
- Image processing libraries

**Size:** ~5GB total

**Use this ONLY if:**
- ✅ You have a GPU (NVIDIA)
- ✅ You enable `PDF_EXTRACTOR_ENABLED=true`
- ✅ You need deep learning OCR
- ✅ Development environment with GPU

**DO NOT use for:**
- ❌ Production VPS (usually no GPU)
- ❌ Docker containers (unless GPU-enabled)
- ❌ When PDF processing is disabled

**Install:**
```bash
# Only if you have GPU and need OCR
pip install -r requirements-ocr.txt
```

---

### 3. `requirements-production.txt` ⭐ USE FOR DOKPLOY

**What it includes:**
- Everything from `requirements-base.txt`
- Production-specific packages:
  - Gunicorn (WSGI server)
  - WhiteNoise (static files)
  - Sentry SDK (error tracking)
  - Django Health Check
  - Django Defender (security)
  - Performance monitoring
  - Logging utilities

**What it EXCLUDES:**
- ❌ GPU/CUDA packages
- ❌ OCR libraries
- ❌ Development tools

**Size:** ~600MB

**Use this for:**
- ✅ Dokploy deployment
- ✅ Production VPS
- ✅ Docker production builds
- ✅ Any production environment

**Install:**
```bash
pip install -r requirements-production.txt
```

---

### 4. `requirements.txt` (DEVELOPMENT)

**What it includes:**
- Everything from `requirements-base.txt`
- OCR packages (EasyOCR, PyTorch)
- GPU/CUDA support
- All development features

**Size:** ~5GB

**Use this for:**
- ✅ Local development
- ✅ If you have GPU
- ✅ Full feature development

**Install:**
```bash
pip install -r requirements.txt
```

---

## Quick Decision Guide

### For Production Deployment (Dokploy/VPS):
```bash
# Use this:
pip install -r requirements-production.txt
```

### For Development (Local):
```bash
# If you DON'T need PDF OCR:
pip install -r requirements-base.txt

# If you NEED PDF OCR and have GPU:
pip install -r requirements.txt
# OR
pip install -r requirements-ocr.txt
```

---

## Comparison Table

| Feature | base | ocr | production | txt |
|---------|------|-----|------------|-----|
| Django Core | ✅ | ✅ | ✅ | ✅ |
| PostgreSQL | ✅ | ✅ | ✅ | ✅ |
| Redis | ✅ | ✅ | ✅ | ✅ |
| Celery | ✅ | ✅ | ✅ | ✅ |
| Basic PDF | ✅ | ✅ | ✅ | ✅ |
| OCR/GPU | ❌ | ✅ | ❌ | ✅ |
| CUDA Packages | ❌ | ✅ | ❌ | ✅ |
| Gunicorn | ❌ | ❌ | ✅ | ❌ |
| Sentry | ❌ | ❌ | ✅ | ❌ |
| Health Checks | ❌ | ❌ | ✅ | ❌ |
| **Size** | ~500MB | ~5GB | ~600MB | ~5GB |
| **Use Case** | Base/Light | Development | Production | Development |

---

## Size Impact

### Before Optimization (requirements.txt):
```
Total size: ~5GB
- Django & core: ~200MB
- PostgreSQL, Redis: ~100MB
- PyTorch: ~2GB
- NVIDIA CUDA: ~3GB
- Other packages: ~200MB

Deployment time: 10-15 minutes
```

### After Optimization (requirements-production.txt):
```
Total size: ~600MB (88% reduction!)
- Django & core: ~200MB
- PostgreSQL, Redis: ~100MB
- Production tools: ~200MB
- Other packages: ~100MB

Deployment time: 2-3 minutes (5x faster!)
```

---

## Dockerfile Configuration

### For Production (Dokploy):
```dockerfile
# Use production requirements
COPY requirements-production.txt .
RUN pip install -r requirements-production.txt
```

### For Development with GPU:
```dockerfile
# Use full requirements
COPY requirements.txt .
RUN pip install -r requirements.txt
```

---

## Environment Variables

Set these in your `.env` or Dokploy environment:

```bash
# Disable PDF processing in production (no GPU needed)
PDF_EXTRACTOR_ENABLED=false
PDF_UPLOAD_ALLOWED=false

# Enable basic features
PAYMENT_SYSTEM_ENABLED=true
ADVANCED_ANALYTICS_ENABLED=true
BULK_OPERATIONS_ENABLED=true
```

---

## Migration Guide

### If you're currently using `requirements.txt` in production:

1. **Update Dockerfile:**
   ```dockerfile
   # Change from:
   COPY requirements.txt .
   RUN pip install -r requirements.txt

   # To:
   COPY requirements-production.txt requirements-base.txt ./
   RUN pip install -r requirements-production.txt
   ```

2. **Update docker-compose.yml:**
   No changes needed - it uses Dockerfile

3. **Redeploy:**
   - Push changes to GitHub
   - Redeploy in Dokploy
   - Deployment will be much faster!

---

## Benefits

### ✅ Production with requirements-production.txt:
- **88% smaller** package size
- **5x faster** deployment
- **No GPU dependencies** (works on any VPS)
- **Optimized** for your use case
- **Secure** - only necessary packages
- **Maintainable** - clear separation

### ❌ Production with requirements.txt:
- Large package size (5GB)
- Slow deployment (10-15 min)
- Requires GPU (fails on regular VPS)
- Wasted resources
- Unnecessary dependencies

---

## Troubleshooting

### Error: "Could not find a version that satisfies..."
**Cause:** Missing requirements-base.txt
**Solution:** Make sure both files are in the repository:
```bash
git add requirements-base.txt requirements-production.txt
git commit -m "Add optimized requirements structure"
git push
```

### Error: "No module named 'easyocr'"
**Cause:** Trying to use OCR without installing requirements-ocr.txt
**Solution:** Either:
1. Disable PDF processing: `PDF_EXTRACTOR_ENABLED=false`
2. Or install OCR packages: `pip install -r requirements-ocr.txt`

### Deployment is slow
**Cause:** Using requirements.txt instead of requirements-production.txt
**Solution:** Update Dockerfile to use requirements-production.txt

---

## Summary

**For your Dokploy deployment:**
- ✅ Use `requirements-production.txt`
- ✅ Set `PDF_EXTRACTOR_ENABLED=false`
- ✅ Deployment will be fast and efficient
- ✅ No GPU/CUDA packages
- ✅ ~600MB instead of ~5GB

**Result:**
- Faster deployment (2-3 min vs 10-15 min)
- Less disk space (600MB vs 5GB)
- Works on any VPS (no GPU needed)
- Production-optimized

---

## Questions?

- **Q: Can I enable PDF processing later?**
  - A: Yes! Install requirements-ocr.txt and set PDF_EXTRACTOR_ENABLED=true

- **Q: Will my app still work without OCR packages?**
  - A: Yes! All core features work. Only PDF OCR is disabled.

- **Q: What if I want to use OCR without GPU?**
  - A: Use pytesseract only (included in base) instead of easyocr

- **Q: Do I need to change anything in Dokploy?**
  - A: No, just push the updated files and redeploy
