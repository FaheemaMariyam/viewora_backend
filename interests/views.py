from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from properties.models import Property
from .models import PropertyInterest
from .serializers import PropertyInterestListSerializer,PropertyInterestCreateSerializer
from authentication.permissions import IsClientUser,IsApprovedBroker
from .services import assign_broker_to_interest
from django.db import transaction

class CreateInterestView(APIView):
    permission_classes = [IsClientUser]

    def post(self, request, property_id):

        property_obj = get_object_or_404(
            Property,
            id=property_id,
            status="published",
            is_active=True
        )

        if property_obj.seller == request.user:
            return Response(
                {"message": "You cannot show interest in your own property"},
                status=status.HTTP_400_BAD_REQUEST
            )

        interest, created = PropertyInterest.objects.get_or_create(
            property=property_obj,
            client=request.user
        )
        
        if not created:
            return Response(
                {"message": "Already expressed interest"},
                status=status.HTTP_400_BAD_REQUEST
            )
        assign_broker_to_interest(interest)

        property_obj.interest_count += 1
        property_obj.save(update_fields=["interest_count"])

        return Response(
            {"message": "Interest created"},
            status=status.HTTP_201_CREATED
        )

class BrokerAcceptInterestView(APIView):
    permission_classes = [IsApprovedBroker]

    def post(self, request, interest_id):

        with transaction.atomic():

            interest = get_object_or_404(
                PropertyInterest.objects.select_for_update(),
                id=interest_id,
                status='assigned'
            )

            if interest.broker != request.user:
                return Response(
                    {"message": "Not authorized for this interest"},
                    status=status.HTTP_403_FORBIDDEN
                )

            interest.status = 'in_progress'
            interest.save(update_fields=['status'])

            return Response(
                {"message": "Interest accepted"},
                status=status.HTTP_200_OK
            )

class BrokerCloseDealView(APIView):
    permission_classes = [IsApprovedBroker]

    def post(self, request, interest_id):

        with transaction.atomic():

            interest = get_object_or_404(
                PropertyInterest.objects.select_for_update(),
                id=interest_id,
                broker=request.user,
                status='in_progress'
            )

            property_obj = interest.property

            if property_obj.status == 'sold':
                return Response(
                    {"message": "Property already sold"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Close deal
            interest.status = 'closed'
            interest.save(update_fields=['status'])

            property_obj.status = 'sold'
            property_obj.save(update_fields=['status'])

            # Cancel other interests
            PropertyInterest.objects.filter(
                property=property_obj
            ).exclude(id=interest.id).update(status='cancelled')

            return Response(
                {"message": "Deal closed successfully"},
                status=status.HTTP_200_OK
            )

class BrokerAssignedInterestsView(APIView):
    permission_classes = [IsApprovedBroker]

    def get(self, request):
        qs = PropertyInterest.objects.filter(
            broker=request.user,
            status__in=['assigned', 'in_progress']
        )
        serializer = PropertyInterestListSerializer(qs, many=True)

        return Response(serializer.data)
