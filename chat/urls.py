from django.urls import path
from .views import ChatHistoryView,MarkMessagesReadView

urlpatterns = [
    path(
        "interest/<int:interest_id>/history/",
        ChatHistoryView.as_view()
    ),
    path("interest/<int:interest_id>/read/", MarkMessagesReadView.as_view()),
]
