# properties/views.py
from django.shortcuts import get_object_or_404
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import IsApprovedSeller

from .models import Property
from .pagination import PropertyPagination
from .serializers import (
    PropertyCreateSerializer,
    PropertyDetailSerializer,
    PropertyListSerializer,
)


class PropertyCreateView(APIView):
    permission_classes = [IsApprovedSeller]

    def post(self, request):
        serializer = PropertyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(seller=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PropertyListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PropertyListSerializer
    pagination_class = PropertyPagination

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    search_fields = ["title", "description", "city", "locality"]

    ordering_fields = ["price", "created_at", "view_count", "interest_count"]

    ordering = ["-created_at"]

    def get_queryset(self):
        qs = Property.objects.filter(status="published", is_active=True)

        city = self.request.query_params.get("city")
        property_type = self.request.query_params.get("property_type")
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")

        if city:
            qs = qs.filter(city__iexact=city)

        if property_type:
            qs = qs.filter(property_type=property_type)

        if min_price:
            qs = qs.filter(price__gte=min_price)

        if max_price:
            qs = qs.filter(price__lte=max_price)

        return qs


class PropertyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        property_obj = get_object_or_404(
            Property, id=pk, status="published", is_active=True
        )

        serializer = PropertyDetailSerializer(
            property_obj, context={"request": request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)
