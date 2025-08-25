from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/pdf-extractor/processing/(?P<job_id>[0-9a-f-]+)/$', consumers.ProcessingProgressConsumer.as_asgi()),
]