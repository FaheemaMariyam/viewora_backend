from django.urls import path
from .views import PropertyCreateView,PropertyListView

urlpatterns = [
    path("create/", PropertyCreateView.as_view()),
    path("view/",PropertyListView.as_view()),
]
