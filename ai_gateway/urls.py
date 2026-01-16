from django.urls import path

from .views import AreaInsightsGateway,PropertiesForRAG

urlpatterns = [
    path("area-insights/", AreaInsightsGateway.as_view()),
    path("properties/", PropertiesForRAG.as_view()),
]
