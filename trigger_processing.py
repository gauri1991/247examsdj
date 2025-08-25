#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/gss/Desktop/dts/test_platform')

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_platform.settings')
django.setup()

from pdf_extractor.models import PDFDocument
from pdf_extractor.tasks import process_pdf_document_task
import logging

# Configure logging to see debug output
logging.basicConfig(level=logging.INFO)

def test_pdf_processing():
    print("Looking for existing PDF documents...")
    
    # Get the most recent PDF document
    document = PDFDocument.objects.order_by('-uploaded_at').first()
    
    if not document:
        print("No PDF documents found")
        return
    
    print(f"Found document: {document.filename} (ID: {document.id})")
    print(f"Current status: {document.status}")
    
    # Trigger processing
    print("Starting processing...")
    result = process_pdf_document_task(document.id)
    
    print("Processing completed!")
    print(f"Result: {result}")

if __name__ == "__main__":
    test_pdf_processing()