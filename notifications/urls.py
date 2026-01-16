# notifications/urls.py
from django.urls import path

from .views import (
    NotificationListView,
    NotificationMarkReadView,
    NotificationUnreadCountView,
)

urlpatterns = [
    path("", NotificationListView.as_view()),
    path("unread-count/", NotificationUnreadCountView.as_view()),
    path("mark-read/", NotificationMarkReadView.as_view()),
]
