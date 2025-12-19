from django.urls import path
from .views import CreateInterestView,BrokerAcceptInterestView,BrokerCloseDealView,BrokerAssignedInterestsView

urlpatterns = [
    path(
        "property/<int:property_id>/interest/",
        CreateInterestView.as_view(),
        name="create-interest"
    ),
     path(
        "interest/<int:interest_id>/accept/",
        BrokerAcceptInterestView.as_view(),
        name="broker-accept-interest"
    ),
    path(
        "interest/<int:interest_id>/close/",
        BrokerCloseDealView.as_view(),
        name="broker-close-deal"
    ),
    path(
    "broker/interests/",
    BrokerAssignedInterestsView.as_view(),
    name="broker-assigned-interests"
)

]