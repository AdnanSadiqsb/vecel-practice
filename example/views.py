# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import User
from .serializer import UserSerializer
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from . import serializer
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

def get_and_authenticate_user(email, password):
    print(email, password)
    user = authenticate(username=email, password=password)
    if user is None:
        raise serializers.ValidationError("Invalid username/password. Please try again!")
    return user

class AuthViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = [AllowAny, ]
    serializer_class = serializer.EmptySerializer

    @action(detail=False, methods=['POST', ],url_path='login',  serializer_class=serializer.LoginSerializer)
    def login(self, request):
        user = get_and_authenticate_user(email=request.data['email'], password=request.data['password'])
        print(user)
        data = UserSerializer(user).data  
        token, created = Token.objects.get_or_create(user=user)
        print(token)
        return Response(data={'user': data, 'token': token.key}, status=status.HTTP_200_OK)

