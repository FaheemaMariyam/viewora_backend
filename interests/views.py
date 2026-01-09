import logging

from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import IsApprovedBroker, IsClientUser
from properties.models import Property

from .models import PropertyInterest
from .serializers import (
    
    PropertyInterestListSerializer,
)
from django.contrib.auth import get_user_model
# from authentication.tasks import send_notification_task
from notifications.tasks import send_notification_task
# from .services import assign_broker_to_interest

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
        # Signals handle broker + count

        return Response({"message": "Interest created"}, status=status.HTTP_201_CREATED)


# class BrokerAcceptInterestView(APIView):
#     permission_classes = [IsApprovedBroker]

#     @swagger_auto_schema(
#         tags=["Interests"],
#         operation_summary="Accept interest",
#         operation_description="Broker accepts an available interest (first broker wins)",
#         security=[{"cookieAuth": []}],
#         responses={
#             200: "Interest accepted",
#             404: "Interest not found",
#         },
#     )
#     def post(self, request, interest_id):
#         with transaction.atomic():

#             interest = get_object_or_404(
#                 PropertyInterest.objects.select_for_update(),
#                 id=interest_id,
#                 status="requested",  #  still unclaimed
#             )

#             # FIRST broker wins
#             interest.broker = request.user
#             interest.status = "assigned"
#             interest.save(update_fields=["broker", "status"])

#             client = interest.client
#             send_push_notification(
#                 client.profile.fcm_token,
#                 "Interest Accepted",
#                 "A broker has accepted your interest",
#             )

#             return Response({"message": "Interest accepted"}, status=status.HTTP_200_OK)
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


# class BrokerCloseDealView(APIView):
#     permission_classes = [IsApprovedBroker]

#     @swagger_auto_schema(
#         tags=["Interests"],
#         operation_summary="Close deal",
#         operation_description="Marks interest as closed and property as sold",
#         security=[{"cookieAuth": []}],
#         responses={
#             200: "Deal closed successfully",
#             400: "Property already sold",
#             404: "Interest not found",
#         },
#     )
#     def post(self, request, interest_id):

#         with transaction.atomic():

#             interest = get_object_or_404(
#                 PropertyInterest.objects.select_for_update(),
#                 id=interest_id,
#                 broker=request.user,
#                 status="in_progress",
#             )

#             property_obj = interest.property

#             if property_obj.status == "sold":
#                 return Response(
#                     {"message": "Property already sold"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )
#             seller = property_obj.seller
#             send_push_notification(
#                 seller.profile.fcm_token,
#                 "Property Sold",
#                 "Your property deal has been closed successfully",
#             )

#             # Close deal
#             interest.status = "closed"
#             interest.save(update_fields=["status"])

#             property_obj.status = "sold"
#             property_obj.save(update_fields=["status"])

#             # Cancel other interests
#             PropertyInterest.objects.filter(property=property_obj).exclude(
#                 id=interest.id
#             ).update(status="cancelled")

#             return Response(
#                 {"message": "Deal closed successfully"}, status=status.HTTP_200_OK
#             )
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
                    {"message": "Property already sold"}, status=400
                )

            interest.status = "closed"
            interest.save(update_fields=["status"])

            property_obj.status = "sold"
            property_obj.save(update_fields=["status"])

            PropertyInterest.objects.filter(property=property_obj).exclude(
                id=interest.id
            ).update(status="cancelled")

            # 🔔 async notification to seller
            # send_notification_task.delay(
            #     property_obj.seller.id,
            #     "Property Sold",
            #     "Your property deal has been closed successfully",
            #     {"property_id": str(property_obj.id)},
            # )
            send_notification_task.delay(
    property_obj.seller.id,
    "Property Sold",
    "Your property deal has been closed successfully",
    {"property_id": str(property_obj.id)},
)           
            # admins = User.objects.filter(is_staff=True)
            # for admin in admins:
            #     send_notification_task.delay(
            #         admin.id,
            #         "Deal Closed",
            #         f"{property_obj.title} was sold by broker {request.user.username}",
            #         {
            #             "property_id": str(property_obj.id),
            #             "broker_id": str(request.user.id),
            #             "interest_id": str(interest.id),
            #         },
            #     )


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
        qs = PropertyInterest.objects.filter(status="requested").select_related(
            "property", "client"
        ).order_by("-created_at")

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
