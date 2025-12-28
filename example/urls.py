from django.urls import include, path
from rest_framework import routers

from .views import UserViewSet, AuthViewSet, PaypalPaymentView, PaypalValidatePaymentView, GoogleLoginCallback, PetViewSet, TypeOfConfigViewSet

router = routers.DefaultRouter()
router.register(r"user", UserViewSet)
router.register(r"auth", AuthViewSet, basename="user_auth")
router.register(r"type_of_config", TypeOfConfigViewSet)
router.register(r"pet", PetViewSet)
# router.register(r"project", ProjectViewSet)
# router.register(r"task", TaskViewSet)
# router.register(r"paypal", PaypalPaymentView, basename="paypal_payment")
urlpatterns = [
    path('', include(router.urls)),
    # path('paypal/create/', PaypalPaymentView.as_view(), name='ordercreate'),
    # path('paypal/validate/', PaypalValidatePaymentView.as_view(), name='paypalvalidate'),

     path(
        "v1/auth/google/callback/",
        GoogleLoginCallback.as_view(),
        name="google_login_callback",
    ),

]