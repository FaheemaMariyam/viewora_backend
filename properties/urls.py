from django.urls import path
from .views import PropertyCreateView,PropertyListView,PropertyDetailView

urlpatterns = [
    path("create/", PropertyCreateView.as_view()),
    path("view/",PropertyListView.as_view()),
    path("view/<int:pk>/", PropertyDetailView.as_view()),
]
