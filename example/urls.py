from django.urls import include, path
from rest_framework import routers

from .views import UserViewSet, AuthViewSet, ProjectViewSet, TaskViewSet

router = routers.DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"auth", AuthViewSet)
router.register(r"project", ProjectViewSet)
router.register(r"task", TaskViewSet)
urlpatterns = [
    path('', include(router.urls))
]