from rest_framework import serializers

from .models import PayPalPayment, User
from datetime import date
from .choices import ProjectStatus
from django.contrib.auth.hashers import make_password
from .services.mail_serive import SMTPMailService
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models import Q
from datetime import datetime
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
# Serializers define the API representation.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["groups", "user_permissions", "is_superuser", "is_staff", 'plain_password']
    
    def create(self, validated_data):
        # Encrypt the password before saving
        validated_data['plain_password'] = validated_data.get('password')
        validated_data['password'] = make_password(validated_data.get('password'))
        validated_data['is_active'] = True
        # Check if role is 'admin', if yes, set is_superuser to True, otherwise False
        role = validated_data.get('role', None)
        if role == 'admin':
            validated_data['is_superuser'] = True
        else:
            validated_data['is_superuser'] = False
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Encrypt the password if it's present in validated_data
        password = validated_data.pop('password', None)
        print("password", password)
        if password and len(password)<=12:
            validated_data['plain_password'] = password
            validated_data['password'] = make_password(password)
            print("inside up")

        return super().update(instance, validated_data)


class WorkersListSerializer(serializers.ModelSerializer):
    # Define additional fields for task counts
    active_tasks = serializers.IntegerField(read_only=True)
    completed_tasks = serializers.IntegerField(read_only=True)
    cancelled_tasks = serializers.IntegerField(read_only=True)
    pending_tasks = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        exclude = ["groups", "user_permissions", "is_superuser", "is_staff", 'plain_password']

class ContractorssListSerializer(serializers.ModelSerializer):
    # Define additional fields for task counts
    active_project = serializers.IntegerField(read_only=True)
    completed_project = serializers.IntegerField(read_only=True)
    cancelled_project = serializers.IntegerField(read_only=True)
    pending_project = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        exclude = ["groups", "user_permissions", "is_superuser", "is_staff", 'plain_password']



class SupplierListSerializer(serializers.ModelSerializer):
    # Define additional fields for task counts
    total_workers = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = User
        exclude = ["groups", "user_permissions", "is_superuser", "is_staff", 'plain_password', 'password', 'supplier']
    
    def get_total_workers(self, obj):
        return User.objects.filter(supplier=obj).count()

class UserShortInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'avatar']


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
class EmptySerializer(serializers.Serializer):
    pass



colors = [
    '#2c3e50',
    '#58cd32',
    '#7c8dad'
]


    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
class SendMailToWorkersSerializer(serializers.Serializer):
    worker = serializers.CharField(max_length = 3, default='all')



class addTasksXLSSErialixer(serializers.Serializer):
    file = serializers.FileField()



class CreatePaypalLinkSerializer(serializers.Serializer):
    amount = serializers.FloatField()
    client =serializers.UUIDField(required = False)
    description = serializers.CharField()
    



class CreatePaypalLinkNewSerializer(serializers.Serializer):
    client =serializers.UUIDField(required = False)
    description = serializers.CharField()
    enableTax = serializers.BooleanField(default=True)
    itemsList = serializers.JSONField()
    payment_method = serializers.CharField(default='card')


class PayPalPaymentSerializer(serializers.ModelSerializer):
    client_info = UserShortInfoSerializer(source = 'client', read_only=True)
    created_by_info =  UserShortInfoSerializer(source = 'created_by', read_only=True)

    class Meta:
        model = PayPalPayment
        fields = '__all__'