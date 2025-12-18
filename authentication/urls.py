from django.urls import path
from .views import RegisterView, LoginView, ProfileView, LogoutView,ChangePasswordView,ResetPasswordConfirmView,ResetPasswordRequestView,AdminOTPVerifyView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("profile/", ProfileView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("change-password/", ChangePasswordView.as_view()),
    path("reset-password/request/", ResetPasswordRequestView.as_view()),
    path("reset-password/confirm/", ResetPasswordConfirmView.as_view()),
    path("admin/verify-otp/", AdminOTPVerifyView.as_view()),


]
