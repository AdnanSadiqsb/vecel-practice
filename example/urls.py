# example/urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from django.urls import include, path
from rest_framework import routers

from .views import UserViewSet

router = routers.DefaultRouter()
router.register(r"users", UserViewSet)
urlpatterns = [
    path("", include(router.urls)),
]



urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)