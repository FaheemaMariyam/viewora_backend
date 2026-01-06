from django.urls import path

from .views import PropertyCreateView, PropertyDetailView, PropertyListView,SellerPropertyListView,SellerPropertyToggleArchiveView,SellerPropertyDetailView,SellerPropertyUpdateView

urlpatterns = [
    path("create/", PropertyCreateView.as_view()),
    path("view/", PropertyListView.as_view()),
    path("view/<int:pk>/", PropertyDetailView.as_view()),
    path("seller/my-properties/", SellerPropertyListView.as_view()),
    
    path(
  "seller/property/<int:pk>/toggle-archive/",
  SellerPropertyToggleArchiveView.as_view()
),
    path(
  "seller/property/<int:pk>/",
  SellerPropertyDetailView.as_view()
),
path(
  "seller/property/<int:pk>/update/",
  SellerPropertyUpdateView.as_view()
),



]
