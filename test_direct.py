import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_platform.settings'
django.setup()

from pdf_extractor.models import PDFDocument
from pdf_extractor.processors import PDFTextExtractor
from io import BytesIO

print("Looking for documents...")
doc = PDFDocument.objects.order_by('-uploaded_at').first()
if doc:
    print(f"Found: {doc.filename}")
    print("Testing extraction directly...")
    
    extractor = PDFTextExtractor()
    with doc.file.open('rb') as f:
        content = f.read()
        temp_file = BytesIO(content)
        temp_file.name = doc.filename
        temp_file.size = len(content)
        
        result = extractor.extract_text_with_layout(temp_file)
        print(f"Direct extraction result: {result}")
else:
    print("No documents found")