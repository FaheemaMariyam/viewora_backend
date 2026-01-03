# properties/views.py
from django.shortcuts import get_object_or_404
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import IsApprovedSeller

from .models import Property,PropertyImage
from .pagination import PropertyPagination
from .serializers import (
    PropertyCreateSerializer,
    PropertyDetailSerializer,
    PropertyListSerializer,
    SellerPropertyListSerializer,
    PropertyUpdateSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed

# class PropertyCreateView(APIView):
#     permission_classes = [IsApprovedSeller]

#     def post(self, request):
#         serializer = PropertyCreateSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save(seller=request.user)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
class PropertyCreateView(APIView):
    permission_classes = [IsApprovedSeller]

    def post(self, request):
        serializer = PropertyCreateSerializer(
            data=request.data
        )
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


class SellerPropertyListView(generics.ListAPIView):
    permission_classes = [IsApprovedSeller]
    serializer_class = SellerPropertyListSerializer

    def get_queryset(self):
        return Property.objects.filter(
            seller=self.request.user,
            
        ).order_by("-created_at")

# class SellerPropertyArchiveView(APIView):
#     permission_classes = [IsApprovedSeller]

#     def patch(self, request, pk):
#         prop = get_object_or_404(
#             Property,
#             id=pk,
#             seller=request.user
#         )
#         prop.is_active = False
#         prop.status = "archived"
#         prop.save()

#         return Response({"message": "Property archived"})
class SellerPropertyToggleArchiveView(APIView):
    permission_classes = [IsApprovedSeller]

    def patch(self, request, pk):
        prop = get_object_or_404(
            Property,
            id=pk,
            seller=request.user
        )

        prop.is_active = not prop.is_active
        prop.status = "published" if prop.is_active else "archived"
        prop.save(update_fields=["is_active", "status"])

        return Response({
            "id": prop.id,
            "is_active": prop.is_active,
            "status": prop.status,
        })
class SellerPropertyDetailView(generics.RetrieveAPIView):
    permission_classes = [IsApprovedSeller]
    serializer_class = PropertyDetailSerializer

    def get_queryset(self):
        return Property.objects.filter(seller=self.request.user)

# class SellerPropertyUpdateView(generics.UpdateAPIView):
#     permission_classes = [IsApprovedSeller]
#     serializer_class = PropertyUpdateSerializer

#     def get_queryset(self):
#         return Property.objects.filter(seller=self.request.user)
class SellerPropertyUpdateView(generics.UpdateAPIView):
    permission_classes = [IsApprovedSeller]
    serializer_class = PropertyUpdateSerializer

    def get_queryset(self):
        return Property.objects.filter(seller=self.request.user)

    def patch(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().patch(request, *args, **kwargs)

