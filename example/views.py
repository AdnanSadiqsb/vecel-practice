# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import User, Project, Tasks
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework import serializers, mixins
from rest_framework.authtoken.models import Token

from . import serializer
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializer.UserSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['GET'], url_path='by-role/(?P<role>[^/]+)', serializer_class=serializer.UserSerializer)
    def get_users_by_role(self, request, role =None):
        users = User.objects.filter(role=role)
        data = self.get_serializer(users, many=True).data  
        return Response(data=data, status=status.HTTP_200_OK)

def get_and_authenticate_user(email, password):
    user = authenticate(username=email, password=password)
    if user is None:
        raise serializers.ValidationError("Invalid username/password. Please try again!")
    return user

class AuthViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = serializer.EmptySerializer

    @action(detail=False, methods=['POST', ],url_path='login',  serializer_class=serializer.LoginSerializer)
    def login(self, request):
        user = get_and_authenticate_user(email=request.data['email'], password=request.data['password'])
        data = serializer.UserSerializer(user).data  
        token, created = Token.objects.get_or_create(user=user)
        return Response(data={'user': data, 'token': token.key}, status=status.HTTP_200_OK)
    

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = serializer.ProjectSerializer
    permission_classes = [IsAuthenticated]
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializer.GetProjectSerializer
        return self.serializer_class

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Tasks.objects.all()
    serializer_class = serializer.TasksSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializer.GetTasksSerializer
        return self.serializer_class

