from django.urls import path

from .views import PropertyCreateView, PropertyDetailView, PropertyListView

urlpatterns = [
    path("create/", PropertyCreateView.as_view()),
    path("view/", PropertyListView.as_view()),
    path("view/<int:pk>/", PropertyDetailView.as_view()),
]
