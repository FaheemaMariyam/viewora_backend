import os
import requests
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Property

@receiver(post_save, sender=Property)
@receiver(post_delete, sender=Property)
def trigger_ai_sync(sender, instance, **kwargs):
    """
    Automatically trigger a sync of the AI RAG index when a property is changed
    """
    try:
        # We call the gateway endpoint directly if possible, or the internal AI service
        # It's safer to call the internal AI service URL directly from the backend
        ai_service_url = os.getenv("AI_SERVICE_URL", "http://ai_service:8001")
        print(f"🤖 AI Sync Triggered by {instance.id}")
        
        # We don't want to block the request, so we should ideally use a task (Celery)
        # But for now, we'll do a simple request with a short timeout
        requests.post(f"{ai_service_url}/ai/sync", timeout=5)
        
    except Exception as e:
        print(f"⚠️ Failed to trigger AI sync: {e}")
