from django.urls import include, path
from rest_framework import routers

from .views import UserViewSet, AuthViewSet

router = routers.DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"auth", AuthViewSet)
urlpatterns = [
    path('', include(router.urls))
]