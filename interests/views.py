import logging

from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import IsApprovedBroker, IsClientUser
from properties.models import Property

from .models import PropertyInterest
from .serializers import (
    PropertyInterestCreateSerializer,
    PropertyInterestListSerializer,
)
from .services import assign_broker_to_interest

logger = logging.getLogger("viewora")


class CreateInterestView(APIView):
    permission_classes = [IsClientUser]

    def post(self, request, property_id):

        property_obj = get_object_or_404(
            Property, id=property_id, status="published", is_active=True
        )

        if property_obj.seller == request.user:
            return Response(
                {"message": "You cannot show interest in your own property"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # )
        interest, created = PropertyInterest.objects.get_or_create(
            property=property_obj, client=request.user
        )

        if not created:
            logger.warning(
                f"Duplicate interest attempt | property={property_obj.id} | client={request.user.id}"
            )
            return Response(
                {"message": "Already expressed interest"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        logger.info(
            f"Interest created | interest_id={interest.id} | property={property_obj.id} | client={request.user.id}"
        )

        # Signals handle broker + count

        return Response({"message": "Interest created"}, status=status.HTTP_201_CREATED)


class BrokerAcceptInterestView(APIView):
    permission_classes = [IsApprovedBroker]

    def post(self, request, interest_id):
        with transaction.atomic():

            interest = get_object_or_404(
                PropertyInterest.objects.select_for_update(),
                id=interest_id,
                status="requested",  #  still unclaimed
            )

            # FIRST broker wins
            interest.broker = request.user
            interest.status = "assigned"
            interest.save(update_fields=["broker", "status"])

            return Response({"message": "Interest accepted"}, status=status.HTTP_200_OK)


class BrokerCloseDealView(APIView):
    permission_classes = [IsApprovedBroker]

    def post(self, request, interest_id):

        with transaction.atomic():

            interest = get_object_or_404(
                PropertyInterest.objects.select_for_update(),
                id=interest_id,
                broker=request.user,
                status="in_progress",
            )

            property_obj = interest.property

            if property_obj.status == "sold":
                return Response(
                    {"message": "Property already sold"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Close deal
            interest.status = "closed"
            interest.save(update_fields=["status"])

            property_obj.status = "sold"
            property_obj.save(update_fields=["status"])

            # Cancel other interests
            PropertyInterest.objects.filter(property=property_obj).exclude(
                id=interest.id
            ).update(status="cancelled")

            return Response(
                {"message": "Deal closed successfully"}, status=status.HTTP_200_OK
            )


class BrokerAssignedInterestsView(APIView):
    permission_classes = [IsApprovedBroker]

    def get(self, request):
        qs = PropertyInterest.objects.filter(broker=request.user).annotate(
            unread_count=Count(
                "messages",
                filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user),
            )
        )

        serializer = PropertyInterestListSerializer(qs, many=True)
        return Response(serializer.data)


class BrokerAvailableInterestsView(APIView):
    permission_classes = [IsApprovedBroker]

    def get(self, request):
        qs = PropertyInterest.objects.filter(status="requested").select_related(
            "property", "client"
        )

        serializer = PropertyInterestListSerializer(qs, many=True)
        return Response(serializer.data)


class ClientInterestsView(APIView):
    permission_classes = [IsClientUser]

    def get(self, request):
        qs = PropertyInterest.objects.filter(client=request.user).annotate(
            unread_count=Count(
                "messages",
                filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user),
            )
        )

        serializer = PropertyInterestListSerializer(qs, many=True)
        return Response(serializer.data)
