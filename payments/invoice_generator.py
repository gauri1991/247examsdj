"""
PDF Invoice Generator - Google Developer Standards
Professional invoice generation using ReportLab
"""

import os
from decimal import Decimal
from datetime import datetime
from io import BytesIO
from typing import Optional, Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Line

from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from .payment_config import PaymentConfig
from .models import Payment


class InvoiceGenerator:
    """Professional PDF invoice generator"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.company_name = PaymentConfig.INVOICE_COMPANY_NAME
        self.company_address = PaymentConfig.INVOICE_COMPANY_ADDRESS
        self.company_gstin = PaymentConfig.INVOICE_COMPANY_GSTIN
        self.terms = PaymentConfig.INVOICE_TERMS
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2563eb'),
            alignment=TA_CENTER
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#1f2937'),
            alignment=TA_LEFT
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_LEFT
        )
        
        self.right_align_style = ParagraphStyle(
            'RightAlign',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT
        )
    
    def generate_invoice(self, payment: Payment) -> BytesIO:
        """
        Generate PDF invoice for a payment
        Args:
            payment: Payment object
        Returns:
            BytesIO object containing PDF data
        """
        buffer = BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build the invoice content
        story = []
        
        # Header
        story.extend(self._build_header(payment))
        
        # Invoice details
        story.extend(self._build_invoice_details(payment))
        
        # Bill to section
        story.extend(self._build_bill_to_section(payment))
        
        # Line items
        story.extend(self._build_line_items(payment))
        
        # Payment details
        story.extend(self._build_payment_details(payment))
        
        # Footer
        story.extend(self._build_footer())
        
        # Build the PDF
        doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
        
        buffer.seek(0)
        return buffer
    
    def _build_header(self, payment: Payment) -> list:
        """Build invoice header"""
        story = []
        
        # Company logo placeholder (you can add actual logo)
        story.append(Paragraph(f"<b>{self.company_name}</b>", self.title_style))
        story.append(Spacer(1, 12))
        
        # Invoice title and number
        invoice_number = f"{PaymentConfig.INVOICE_PREFIX}-{payment.id}"
        story.append(Paragraph(f"<b>INVOICE #{invoice_number}</b>", self.heading_style))
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_invoice_details(self, payment: Payment) -> list:
        """Build invoice details section"""
        story = []
        
        # Create invoice details table
        invoice_date = payment.created_at.strftime('%B %d, %Y')
        due_date = (payment.created_at + timezone.timedelta(days=7)).strftime('%B %d, %Y')
        
        details_data = [
            ['Invoice Date:', invoice_date, 'Due Date:', due_date],
            ['Invoice Number:', f"{PaymentConfig.INVOICE_PREFIX}-{payment.id}", 
             'Payment Status:', payment.status.title()],
        ]
        
        details_table = Table(details_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        story.append(details_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_bill_to_section(self, payment: Payment) -> list:
        """Build bill to section"""
        story = []
        
        # Company info and Bill To sections
        company_info = [
            f"<b>{self.company_name}</b>",
            self.company_address,
            f"GSTIN: {self.company_gstin}",
        ]
        
        bill_to_info = [
            f"<b>{payment.user.get_full_name() or payment.user.username}</b>",
            payment.user.email,
            f"User ID: {payment.user.id}",
        ]
        
        # Create side-by-side layout
        bill_data = [
            ['<b>From:</b>', '<b>Bill To:</b>'],
            [self._create_address_paragraph(company_info), 
             self._create_address_paragraph(bill_to_info)]
        ]
        
        bill_table = Table(bill_data, colWidths=[3*inch, 3*inch])
        bill_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(bill_table)
        story.append(Spacer(1, 30))
        
        return story
    
    def _create_address_paragraph(self, info_list: list) -> Paragraph:
        """Create paragraph from address info list"""
        content = '<br/>'.join(info_list)
        return Paragraph(content, self.normal_style)
    
    def _build_line_items(self, payment: Payment) -> list:
        """Build line items table"""
        story = []
        
        # Line items header
        story.append(Paragraph('<b>Items</b>', self.heading_style))
        
        # Prepare line items data
        line_items_data = [
            ['Description', 'Quantity', 'Unit Price', 'Total']
        ]
        
        # Add subscription item
        description = f"{payment.plan.name} Subscription"
        if payment.plan.billing_cycle == 'monthly':
            description += " (Monthly)"
        elif payment.plan.billing_cycle == 'yearly':
            description += " (Yearly)"
        
        unit_price = f"{payment.currency} {payment.amount:,.2f}"
        total = f"{payment.currency} {payment.amount:,.2f}"
        
        line_items_data.append([
            description,
            '1',
            unit_price,
            total
        ])
        
        # Calculate tax if applicable (for Indian invoices)
        if payment.currency == 'INR':
            # Add GST calculation (18% for digital services in India)
            base_amount = payment.amount / Decimal('1.18')  # Remove GST to get base
            gst_amount = payment.amount - base_amount
            
            line_items_data.append([
                'SGST + CGST (18%)',
                '',
                '',
                f"INR {gst_amount:,.2f}"
            ])
        
        # Create line items table
        line_items_table = Table(line_items_data, colWidths=[3*inch, 0.8*inch, 1.1*inch, 1.1*inch])
        line_items_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(line_items_table)
        story.append(Spacer(1, 20))
        
        # Total section
        total_data = [
            ['', '', '<b>Total Amount:</b>', f"<b>{payment.currency} {payment.amount:,.2f}</b>"]
        ]
        
        total_table = Table(total_data, colWidths=[3*inch, 0.8*inch, 1.1*inch, 1.1*inch])
        total_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('TEXTCOLOR', (2, 0), (-1, -1), colors.HexColor('#2563eb')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(total_table)
        story.append(Spacer(1, 30))
        
        return story
    
    def _build_payment_details(self, payment: Payment) -> list:
        """Build payment details section"""
        story = []
        
        story.append(Paragraph('<b>Payment Information</b>', self.heading_style))
        
        # Payment details
        payment_info = [
            f"Payment Method: {payment.gateway.title()}",
            f"Transaction ID: {payment.gateway_transaction_id or 'N/A'}",
            f"Payment Date: {payment.created_at.strftime('%B %d, %Y at %I:%M %p')}",
            f"Status: {payment.status.title()}"
        ]
        
        for info in payment_info:
            story.append(Paragraph(info, self.normal_style))
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_footer(self) -> list:
        """Build invoice footer"""
        story = []
        
        # Terms and conditions
        story.append(Paragraph('<b>Terms & Conditions</b>', self.heading_style))
        story.append(Paragraph(self.terms, self.normal_style))
        story.append(Spacer(1, 20))
        
        # Thank you note
        thank_you_style = ParagraphStyle(
            'ThankYou',
            parent=self.styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2563eb'),
            spaceBefore=20,
            spaceAfter=20
        )
        
        story.append(Paragraph('<b>Thank you for your business!</b>', thank_you_style))
        
        return story
    
    def _add_page_number(self, canvas, doc):
        """Add page number to each page"""
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawRightString(A4[0] - 72, 30, text)
        canvas.restoreState()
    
    def save_invoice(self, payment: Payment) -> str:
        """
        Generate and save invoice PDF
        Returns: File path of saved invoice
        """
        # Generate PDF
        pdf_buffer = self.generate_invoice(payment)
        
        # Create filename
        filename = f"invoice_{PaymentConfig.INVOICE_PREFIX}_{payment.id}.pdf"
        filepath = f"invoices/{payment.user.id}/{filename}"
        
        # Save to storage
        saved_path = default_storage.save(filepath, ContentFile(pdf_buffer.read()))
        
        # Update payment metadata
        if not payment.metadata:
            payment.metadata = {}
        payment.metadata['invoice_generated'] = True
        payment.metadata['invoice_path'] = saved_path
        payment.metadata['invoice_generated_at'] = timezone.now().isoformat()
        payment.save()
        
        return saved_path
    
    def get_invoice_url(self, payment: Payment) -> Optional[str]:
        """Get URL for existing invoice"""
        if payment.metadata and payment.metadata.get('invoice_path'):
            return default_storage.url(payment.metadata['invoice_path'])
        return None


class BulkInvoiceGenerator:
    """Generate multiple invoices in bulk"""
    
    def __init__(self):
        self.generator = InvoiceGenerator()
    
    def generate_bulk_invoices(self, payments_queryset) -> Dict[str, Any]:
        """
        Generate invoices for multiple payments
        Returns: Dictionary with results
        """
        results = {
            'success_count': 0,
            'error_count': 0,
            'total_count': payments_queryset.count(),
            'errors': [],
            'generated_files': []
        }
        
        for payment in payments_queryset:
            try:
                # Skip if invoice already generated
                if payment.metadata and payment.metadata.get('invoice_generated'):
                    continue
                
                # Generate invoice
                filepath = self.generator.save_invoice(payment)
                results['generated_files'].append(filepath)
                results['success_count'] += 1
                
            except Exception as e:
                results['error_count'] += 1
                results['errors'].append({
                    'payment_id': str(payment.id),
                    'error': str(e)
                })
        
        return results
    
    def regenerate_invoice(self, payment: Payment) -> str:
        """Regenerate invoice (even if already exists)"""
        # Clear existing invoice metadata
        if payment.metadata:
            payment.metadata.pop('invoice_generated', None)
            payment.metadata.pop('invoice_path', None)
            payment.metadata.pop('invoice_generated_at', None)
            payment.save()
        
        return self.generator.save_invoice(payment)