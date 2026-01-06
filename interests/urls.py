from django.urls import path

from .views import (
    BrokerAcceptInterestView,
    BrokerAssignedInterestsView,
    BrokerAvailableInterestsView,
    BrokerCloseDealView,
    BrokerStartInterestView,
    ClientInterestsView,
    CreateInterestView,
)

urlpatterns = [
    path(
        "property/<int:property_id>/interest/",
        CreateInterestView.as_view(),
        name="create-interest",
    ),
    path(
        "broker/available-interests/",
        BrokerAvailableInterestsView.as_view(),
        name="broker-available-interests",
    ),
    path(
        "interest/<int:interest_id>/accept/",
        BrokerAcceptInterestView.as_view(),
        name="broker-accept-interest",
    ),
    path(
        "interest/<int:interest_id>/close/",
        BrokerCloseDealView.as_view(),
        name="broker-close-deal",
    ),
    path(
        "broker/interests/",
        BrokerAssignedInterestsView.as_view(),
        name="broker-assigned-interests",
    ),
    path(
        "client/interests/",
        ClientInterestsView.as_view(),
        name="client-interests",
    ),
    path(
        "interest/<int:interest_id>/start/",
        BrokerStartInterestView.as_view(),
        name="broker-start-interest",
    ),
]
