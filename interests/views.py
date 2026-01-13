import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import IsApprovedBroker, IsClientUser

# from authentication.tasks import send_notification_task
from notifications.tasks import send_notification_task
from properties.models import Property

# from .services import assign_broker_to_interest
from utils.sqs import send_interest_created_event

from .models import PropertyInterest
from .serializers import (
    PropertyInterestListSerializer,
)

logger = logging.getLogger("viewora")
User = get_user_model()


class CreateInterestView(APIView):
    permission_classes = [IsClientUser]

    @swagger_auto_schema(
        tags=["Interests"],
        operation_summary="Create interest",
        operation_description="Client expresses interest in a property",
        security=[{"cookieAuth": []}],
        responses={
            201: "Interest created",
            400: "Already expressed interest / Own property",
            404: "Property not found",
        },
    )
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
        brokers = User.objects.filter(
            profile__role="broker",
            profile__is_admin_approved=True,
        )

        # realtime notifications (Celery)
        for broker in brokers:
            send_notification_task.delay(
                broker.id,
                "New Property Interest",
                f"A client is interested in {property_obj.title}",
                {
                    "interest_id": str(interest.id),
                    "property_id": str(property_obj.id),
                },
            )

        broker_emails = list(brokers.values_list("email", flat=True))

        send_interest_created_event(
            {
                "event": "INTEREST_CREATED",
                "interest_id": str(interest.id),
                "property_id": str(property_obj.id),
                "property_title": property_obj.title,
                "client_name": request.user.username,
                "broker_emails": broker_emails,
            }
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
                status="requested",
            )

            interest.broker = request.user
            interest.status = "assigned"
            interest.save(update_fields=["broker", "status"])

            #  async notification
            send_notification_task.delay(
                interest.client.id,
                "Interest Accepted",
                "A broker has accepted your interest",
                {"interest_id": str(interest.id)},
            )

            return Response({"message": "Interest accepted"}, status=200)


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
                return Response({"message": "Property already sold"}, status=400)

            interest.status = "closed"
            interest.save(update_fields=["status"])

            property_obj.status = "sold"
            property_obj.save(update_fields=["status"])

            PropertyInterest.objects.filter(property=property_obj).exclude(
                id=interest.id
            ).update(status="cancelled")

            send_notification_task.delay(
                property_obj.seller.id,
                "Property Sold",
                "Your property deal has been closed successfully",
                {"property_id": str(property_obj.id)},
            )

            return Response({"message": "Deal closed successfully"}, status=200)


class BrokerAssignedInterestsView(APIView):
    permission_classes = [IsApprovedBroker]

    @swagger_auto_schema(
        tags=["Interests"],
        operation_summary="Broker assigned interests",
        security=[{"cookieAuth": []}],
        responses={200: PropertyInterestListSerializer(many=True)},
    )
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

    @swagger_auto_schema(
        tags=["Interests"],
        operation_summary="Available interests for brokers",
        security=[{"cookieAuth": []}],
        responses={200: PropertyInterestListSerializer(many=True)},
    )
    def get(self, request):
        qs = (
            PropertyInterest.objects.filter(status="requested")
            .select_related("property", "client")
            .order_by("-created_at")
        )

        serializer = PropertyInterestListSerializer(qs, many=True)
        return Response(serializer.data)


class ClientInterestsView(APIView):
    permission_classes = [IsClientUser]

    @swagger_auto_schema(
        tags=["Interests"],
        operation_summary="Client interests",
        security=[{"cookieAuth": []}],
        responses={200: PropertyInterestListSerializer(many=True)},
    )
    def get(self, request):
        qs = PropertyInterest.objects.filter(client=request.user).annotate(
            unread_count=Count(
                "messages",
                filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user),
            )
        )

        serializer = PropertyInterestListSerializer(qs, many=True)
        return Response(serializer.data)


class BrokerStartInterestView(APIView):
    permission_classes = [IsApprovedBroker]

    @swagger_auto_schema(
        tags=["Interests"],
        operation_summary="Start interest",
        operation_description="Move interest from assigned to in_progress when chat starts",
        security=[{"cookieAuth": []}],
        responses={200: "Interest moved to in_progress"},
    )
    def post(self, request, interest_id):
        interest = get_object_or_404(
            PropertyInterest,
            id=interest_id,
            broker=request.user,
        )

        if interest.status == "assigned":
            interest.status = "in_progress"
            interest.save(update_fields=["status"])

        return Response(
            {"status": interest.status},
            status=status.HTTP_200_OK,
        )
