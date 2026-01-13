# notifications/urls.py
from django.urls import path

from .views import (
    NotificationListView,
    NotificationMarkReadView,
    NotificationUnreadCountView,
)

urlpatterns = [
    # path("store/", StoreNotificationView.as_view()),
    path("", NotificationListView.as_view()),
    path("unread-count/", NotificationUnreadCountView.as_view()),
    path("mark-read/", NotificationMarkReadView.as_view()),
]
