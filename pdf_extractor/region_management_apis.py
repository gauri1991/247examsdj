from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
import json

from .models import PDFDocument, SavedRegion, PageReviewStatus


def get_user_document_or_404(request, document_id):
    """
    Get document with permission check for region management.
    Admin users can access any document, regular users only their own.
    """
    if request.user.is_superuser:
        return get_object_or_404(PDFDocument, id=document_id)
    else:
        return get_object_or_404(PDFDocument, id=document_id, uploaded_by=request.user)


@login_required
def delete_saved_region_api(request, document_id, region_id):
    """
    API endpoint to delete a saved region
    """
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'DELETE required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        saved_region = get_object_or_404(SavedRegion, id=region_id, pdf_document=document)
        page_number = saved_region.page_number
        
        # Delete the region
        saved_region.delete()
        
        # Check if there are any remaining unsupported regions on this page
        remaining_unsupported = SavedRegion.objects.filter(
            pdf_document=document,
            page_number=page_number,
            status='unsupported'
        ).count()
        
        # Update page status if no more unsupported regions
        if remaining_unsupported == 0:
            try:
                page_status = PageReviewStatus.objects.get(
                    pdf_document=document,
                    page_number=page_number
                )
                
                # Check if there are any completed regions
                completed_regions = SavedRegion.objects.filter(
                    pdf_document=document,
                    page_number=page_number,
                    status='completed'
                ).count()
                
                if completed_regions > 0:
                    page_status.status = 'completed'
                else:
                    page_status.status = 'pending'
                    
                page_status.save()
                
            except PageReviewStatus.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'message': 'Region deleted successfully',
            'remaining_unsupported': remaining_unsupported
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def update_saved_region_api(request, document_id, region_id):
    """
    API endpoint to update a saved region's properties
    """
    if request.method != 'PUT':
        return JsonResponse({'success': False, 'error': 'PUT required'})
    
    document = get_user_document_or_404(request, document_id)
    
    try:
        data = json.loads(request.body)
        saved_region = get_object_or_404(SavedRegion, id=region_id, pdf_document=document)
        
        # Update allowed fields
        if 'coordinates' in data:
            saved_region.coordinates = data['coordinates']
        if 'status' in data:
            saved_region.status = data['status']
        if 'notes' in data:
            saved_region.notes = data['notes']
        if 'region_type' in data:
            saved_region.region_type = data['region_type']
            
        saved_region.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Region updated successfully',
            'region': {
                'id': str(saved_region.id),
                'coordinates': saved_region.coordinates,
                'status': saved_region.status,
                'notes': saved_region.notes,
                'region_type': saved_region.region_type,
                'status_color': saved_region.status_color
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def delete_document_api(request, document_id):
    """
    API endpoint to delete a PDF document and all related data
    """
    if request.method != "DELETE":
        return JsonResponse({"success": False, "error": "DELETE required"})
    
    try:
        # Get the document and verify ownership
        document = get_user_document_or_404(request, document_id)
        
        # Store document name for response
        document_name = document.filename
        
        # Delete the document (Django will cascade delete related objects)
        # This will automatically delete:
        # - ExtractedQuestion objects
        # - SavedRegion objects  
        # - PageReviewStatus objects
        # - ProcessingJob objects
        # - ProcessingStatistics objects
        # - RegionCorrection objects
        # - RegionReviewSession objects
        # - The actual PDF file
        document.delete()
        
        return JsonResponse({
            "success": True,
            "message": f"Document \"{document_name}\" has been permanently deleted",
            "deleted_document": document_name
        })
        
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
