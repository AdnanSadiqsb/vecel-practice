from django.urls import include, path
from rest_framework import routers

from .views import UserViewSet, AuthViewSet, ProjectViewSet, TaskViewSet, PaypalPaymentView, PaypalValidatePaymentView

router = routers.DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"auth", AuthViewSet)
router.register(r"project", ProjectViewSet)
router.register(r"task", TaskViewSet)
urlpatterns = [
    path('', include(router.urls)),
    path('paypal/create/', PaypalPaymentView.as_view(), name='ordercreate'),
    path('paypal/validate/', PaypalValidatePaymentView.as_view(), name='paypalvalidate'),
]