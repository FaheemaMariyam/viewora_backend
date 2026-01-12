# properties/views.py
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.permissions import IsApprovedSeller

from .models import Property, PropertyImage
from .pagination import PropertyPagination
from .serializers import (
    PropertyCreateSerializer,
    PropertyDetailSerializer,
    PropertyListSerializer,
    PropertyUpdateSerializer,
    SellerPropertyListSerializer,
)
from .tasks import record_property_view_task

class PropertyCreateView(APIView):
    permission_classes = [IsApprovedSeller]

    @swagger_auto_schema(
        tags=["Properties"],
        operation_summary="Create property",
        operation_description="Seller creates a new property with optional images",
        security=[{"cookieAuth": []}],
        request_body=PropertyCreateSerializer,
        responses={
            201: PropertyDetailSerializer,
            400: "Validation error",
        },
    )
    def post(self, request):
        serializer = PropertyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(seller=request.user)
        return Response(serializer.data, status=201)


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

    @swagger_auto_schema(
        tags=["Properties"],
        operation_summary="List properties",
        operation_description="List published properties with filters and pagination",
        security=[{"cookieAuth": []}],
        responses={200: PropertyListSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PropertyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Properties"],
        operation_summary="Get property details",
        security=[{"cookieAuth": []}],
        responses={
            200: PropertyDetailSerializer,
            404: "Property not found",
        },
    )
    def get(self, request, pk):
        property_obj = get_object_or_404(
            Property, id=pk, status="published", is_active=True
        )
        record_property_view_task.delay(
            property_obj.id,
            property_obj.city,
            property_obj.locality
        )
        serializer = PropertyDetailSerializer(
            property_obj, context={"request": request}  
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


class SellerPropertyListView(generics.ListAPIView):
    permission_classes = [IsApprovedSeller]
    serializer_class = SellerPropertyListSerializer

    def get_queryset(self):
        return Property.objects.filter(
            seller=self.request.user,
        ).order_by("-created_at")

    @swagger_auto_schema(
        tags=["Seller Properties"],
        operation_summary="Seller properties",
        security=[{"cookieAuth": []}],
        responses={200: SellerPropertyListSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class SellerPropertyToggleArchiveView(APIView):
    permission_classes = [IsApprovedSeller]

    @swagger_auto_schema(
        tags=["Seller Properties"],
        operation_summary="Toggle property archive",
        security=[{"cookieAuth": []}],
        responses={
            200: "Property archived/unarchived",
            404: "Property not found",
        },
    )
    def patch(self, request, pk):
        prop = get_object_or_404(Property, id=pk, seller=request.user)

        prop.is_active = not prop.is_active
        prop.status = "published" if prop.is_active else "archived"
        prop.save(update_fields=["is_active", "status"])

        return Response(
            {
                "id": prop.id,
                "is_active": prop.is_active,
                "status": prop.status,
            }
        )


class SellerPropertyDetailView(generics.RetrieveAPIView):
    permission_classes = [IsApprovedSeller]
    serializer_class = PropertyDetailSerializer

    @swagger_auto_schema(
        tags=["Seller Properties"],
        operation_summary="Seller property detail",
        security=[{"cookieAuth": []}],
        responses={200: PropertyDetailSerializer},
    )
    def get_queryset(self):
        return Property.objects.filter(seller=self.request.user)


class SellerPropertyUpdateView(generics.UpdateAPIView):
    permission_classes = [IsApprovedSeller]
    serializer_class = PropertyUpdateSerializer

    @swagger_auto_schema(
        tags=["Seller Properties"],
        operation_summary="Update property",
        security=[{"cookieAuth": []}],
        request_body=PropertyUpdateSerializer,
        responses={200: PropertyDetailSerializer},
    )
    def get_queryset(self):
        return Property.objects.filter(seller=self.request.user)

    def patch(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().patch(request, *args, **kwargs)
