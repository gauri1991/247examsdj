# PDF Extractor Settings

# File upload settings
PDF_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
PDF_ALLOWED_EXTENSIONS = ['.pdf']

# Processing settings
PDF_PROCESSING_TIMEOUT = 600  # 10 minutes max processing time
PDF_MAX_PAGES_PER_DOCUMENT = 500  # Maximum pages to process

# OCR settings
PDF_OCR_LANGUAGES = ['eng']  # Languages for OCR
PDF_OCR_DPI = 300  # DPI for PDF to image conversion

# Cleanup settings
PDF_TEMP_DIR = '/tmp/pdf_processing'  # Temporary file directory
PDF_MAX_FILE_AGE_DAYS = 30  # Delete documents older than this
PDF_MAX_TEMP_AGE_HOURS = 24  # Delete temp files older than this
PDF_CLEANUP_NOTIFY_ADMINS = True  # Send email notifications for cleanup

# Error handling
PDF_SEND_ERROR_NOTIFICATIONS = True  # Send email for critical errors
PDF_ERROR_LOG_RETENTION_DAYS = 90  # Keep error logs for this long

# Performance settings
PDF_CHUNK_SIZE = 1024 * 1024  # 1MB chunks for file processing
PDF_MAX_CONCURRENT_JOBS = 5  # Maximum concurrent processing jobs

# WebSocket settings
PDF_WEBSOCKET_ENABLED = True  # Enable WebSocket for real-time updates