"""
Health check and monitoring endpoints for production deployment
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import psutil
import os
import time
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["GET", "HEAD"])
def health_check(request):
    """Basic health check endpoint for load balancers"""
    return JsonResponse({"status": "healthy"}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
def readiness_check(request):
    """
    Comprehensive readiness check for application dependencies
    Returns 200 if all services are ready, 503 otherwise
    """
    checks = {
        "database": False,
        "cache": False,
        "storage": False,
    }
    errors = []
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            checks["database"] = True
    except Exception as e:
        errors.append(f"Database error: {str(e)}")
        logger.error(f"Database health check failed: {e}")
    
    # Check cache (Redis)
    try:
        cache.set("health_check", "ok", 10)
        if cache.get("health_check") == "ok":
            checks["cache"] = True
    except Exception as e:
        errors.append(f"Cache error: {str(e)}")
        logger.error(f"Cache health check failed: {e}")
    
    # Check storage
    try:
        test_file = os.path.join(settings.MEDIA_ROOT, ".health_check")
        with open(test_file, "w") as f:
            f.write(str(time.time()))
        os.remove(test_file)
        checks["storage"] = True
    except Exception as e:
        errors.append(f"Storage error: {str(e)}")
        logger.error(f"Storage health check failed: {e}")
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    response_data = {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
    }
    
    if errors:
        response_data["errors"] = errors
    
    return JsonResponse(response_data, status=status_code)

@csrf_exempt
@require_http_methods(["GET"])
def liveness_check(request):
    """
    Liveness check to ensure the application is running
    Returns system metrics and application status
    """
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get process info
        process = psutil.Process(os.getpid())
        process_info = {
            "pid": process.pid,
            "cpu_percent": process.cpu_percent(),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "threads": process.num_threads(),
            "open_files": len(process.open_files()),
        }
        
        # Check database connections
        db_connections = len(connection.queries) if settings.DEBUG else "N/A"
        
        response_data = {
            "status": "alive",
            "timestamp": time.time(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / 1024 / 1024 / 1024,
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / 1024 / 1024 / 1024,
            },
            "process": process_info,
            "database": {
                "queries_executed": db_connections,
            }
        }
        
        # Add warning if resources are low
        warnings = []
        if cpu_percent > 80:
            warnings.append("High CPU usage")
        if memory.percent > 80:
            warnings.append("High memory usage")
        if disk.percent > 80:
            warnings.append("Low disk space")
        
        if warnings:
            response_data["warnings"] = warnings
        
        return JsonResponse(response_data, status=200)
    
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500
        )

@csrf_exempt
@require_http_methods(["GET"])
def metrics(request):
    """
    Prometheus-compatible metrics endpoint
    """
    try:
        # Collect metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        process = psutil.Process(os.getpid())
        
        # Format as Prometheus metrics
        metrics_text = f"""# HELP exam_portal_cpu_usage_percent CPU usage percentage
# TYPE exam_portal_cpu_usage_percent gauge
exam_portal_cpu_usage_percent {cpu_percent}

# HELP exam_portal_memory_usage_percent Memory usage percentage
# TYPE exam_portal_memory_usage_percent gauge
exam_portal_memory_usage_percent {memory.percent}

# HELP exam_portal_memory_available_bytes Available memory in bytes
# TYPE exam_portal_memory_available_bytes gauge
exam_portal_memory_available_bytes {memory.available}

# HELP exam_portal_disk_usage_percent Disk usage percentage
# TYPE exam_portal_disk_usage_percent gauge
exam_portal_disk_usage_percent {disk.percent}

# HELP exam_portal_disk_free_bytes Free disk space in bytes
# TYPE exam_portal_disk_free_bytes gauge
exam_portal_disk_free_bytes {disk.free}

# HELP exam_portal_process_memory_bytes Process memory usage in bytes
# TYPE exam_portal_process_memory_bytes gauge
exam_portal_process_memory_bytes {process.memory_info().rss}

# HELP exam_portal_process_cpu_percent Process CPU usage percentage
# TYPE exam_portal_process_cpu_percent gauge
exam_portal_process_cpu_percent {process.cpu_percent()}

# HELP exam_portal_process_threads Number of process threads
# TYPE exam_portal_process_threads gauge
exam_portal_process_threads {process.num_threads()}

# HELP exam_portal_process_open_files Number of open files
# TYPE exam_portal_process_open_files gauge
exam_portal_process_open_files {len(process.open_files())}
"""
        
        from django.http import HttpResponse
        return HttpResponse(
            metrics_text,
            content_type="text/plain; version=0.0.4; charset=utf-8"
        )
    
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        from django.http import HttpResponse
        return HttpResponse(
            f"# Error collecting metrics: {str(e)}",
            content_type="text/plain",
            status=500
        )