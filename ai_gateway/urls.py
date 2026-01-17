from django.urls import path

from .views import AreaInsightsGateway,PropertiesForRAG, SyncAIGateway

urlpatterns = [
    path("area-insights/", AreaInsightsGateway.as_view()),
    path("properties/", PropertiesForRAG.as_view()),
    path("sync/", SyncAIGateway.as_view()),
]
