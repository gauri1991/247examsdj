from pdf_extractor.models import PDFDocument
from pdf_extractor.tasks import process_pdf_document_task

document = PDFDocument.objects.order_by('-uploaded_at').first()
if document:
    print(f"Processing document: {document.filename}")
    result = process_pdf_document_task(document.id)
    print(f"Result: {result}")
else:
    print("No documents found")