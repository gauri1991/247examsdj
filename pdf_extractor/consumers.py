import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import ProcessingJob, PDFDocument

logger = logging.getLogger(__name__)


class ProcessingProgressConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time PDF processing progress updates
    """
    
    async def connect(self):
        """
        Handle WebSocket connection
        """
        self.job_id = self.scope['url_route']['kwargs']['job_id']
        self.room_group_name = f'processing_{self.job_id}'
        
        # Check if user is authenticated and has access to this job
        user = self.scope["user"]
        if user == AnonymousUser:
            await self.close()
            return
        
        # Verify user has access to this processing job
        has_access = await self.check_job_access(user, self.job_id)
        if not has_access:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current status immediately
        current_status = await self.get_current_status()
        if current_status:
            await self.send(text_data=json.dumps({
                'type': 'progress_update',
                'data': current_status
            }))
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Handle messages from WebSocket (not used in this implementation)
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'request_status':
                # Client requesting current status
                current_status = await self.get_current_status()
                if current_status:
                    await self.send(text_data=json.dumps({
                        'type': 'progress_update',
                        'data': current_status
                    }))
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
    
    async def progress_update(self, event):
        """
        Handle progress update from group
        """
        # Send progress update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'progress_update',
            'data': event['data']
        }))
    
    async def processing_complete(self, event):
        """
        Handle processing completion notification
        """
        await self.send(text_data=json.dumps({
            'type': 'processing_complete',
            'data': event['data']
        }))
    
    async def processing_failed(self, event):
        """
        Handle processing failure notification
        """
        await self.send(text_data=json.dumps({
            'type': 'processing_failed',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def check_job_access(self, user, job_id):
        """
        Check if user has access to the processing job
        """
        try:
            job = ProcessingJob.objects.get(id=job_id)
            return job.pdf_document.uploaded_by == user
        except ProcessingJob.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_current_status(self):
        """
        Get current processing status
        """
        try:
            job = ProcessingJob.objects.get(id=self.job_id)
            
            status_data = {
                'job_id': str(job.id),
                'status': job.status,
                'progress_percentage': job.progress_percentage,
                'current_step': job.current_step,
                'current_step_display': job.current_step_display or job.get_current_step_display(),
                'error_details': job.error_details,
                'document_name': job.pdf_document.filename
            }
            
            # Add completion data if finished
            if job.status == 'completed':
                try:
                    stats = job.pdf_document.statistics
                    status_data['results'] = {
                        'total_questions': stats.total_questions_found,
                        'high_confidence': stats.high_confidence_questions,
                        'needs_review': stats.questions_requiring_review
                    }
                except:
                    status_data['results'] = {'total_questions': 0}
            
            return status_data
            
        except ProcessingJob.DoesNotExist:
            return None


class ProcessingNotificationMixin:
    """
    Mixin to send processing updates via WebSocket
    """
    
    @staticmethod
    async def send_progress_update(job_id, progress_data):
        """
        Send progress update to WebSocket group
        """
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        if channel_layer:
            await channel_layer.group_send(
                f'processing_{job_id}',
                {
                    'type': 'progress_update',
                    'data': progress_data
                }
            )
    
    @staticmethod
    async def send_completion_notification(job_id, completion_data):
        """
        Send completion notification to WebSocket group
        """
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        if channel_layer:
            await channel_layer.group_send(
                f'processing_{job_id}',
                {
                    'type': 'processing_complete',
                    'data': completion_data
                }
            )
    
    @staticmethod
    async def send_failure_notification(job_id, error_data):
        """
        Send failure notification to WebSocket group
        """
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        if channel_layer:
            await channel_layer.group_send(
                f'processing_{job_id}',
                {
                    'type': 'processing_failed',
                    'data': error_data
                }
            )