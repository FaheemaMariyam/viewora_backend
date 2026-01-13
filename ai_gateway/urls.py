from django.urls import path

from .views import AreaInsightsGateway

urlpatterns = [
    path("area-insights/", AreaInsightsGateway.as_view()),
]
