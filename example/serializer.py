from rest_framework import serializers

from .models import PayPalPayment, PetImage, User,typeOfConfig , Pet
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
        if password and len(password)<=12:
            validated_data['plain_password'] = password
            validated_data['password'] = make_password(password)
            print("inside up")

        return super().update(instance, validated_data)

class LoginResponseUserSerializer(serializers.ModelSerializer):
    linked_pet_id = serializers.SerializerMethodField()
    class Meta:
        model = User
        exclude = ["groups", "user_permissions", "is_superuser", "is_staff", 'plain_password']
    def get_linked_pet_id(self, obj):
        return Pet.objects.filter(owner=obj).order_by('-updated_at').first().id if Pet.objects.filter(owner=obj).exists() else None


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email', 'password']
    
    def create(self, validated_data):
        validated_data['plain_password'] = validated_data.get('password')
        validated_data['password'] = make_password(validated_data.get('password'))
        validated_data['is_active'] = True
        validated_data['username'] = validated_data.get('email')  # use email as username
        return super().create(validated_data)




class UserShortInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'avatar']


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class LoginWithGoogleSerializer(serializers.Serializer):
    id_token = serializers.CharField()
class EmptySerializer(serializers.Serializer):
    pass






    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
class SendMailToWorkersSerializer(serializers.Serializer):
    worker = serializers.CharField(max_length = 3, default='all')



class TypeOfConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = typeOfConfig
        fields = '__all__'

class PetImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PetImage
        fields = ["id", "image", "pet"]


class PetSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        exclude = ("id",)  # or fields you want


class PetSerializer(serializers.ModelSerializer):
    


    # uploaded_images = serializers.ListField(
    #     child=serializers.ImageField(),
    #     write_only=True,      # ✅ IMPORTANT
    #     required=False
    # )


    class Meta:
        model = Pet
        fields = "__all__"

    def create(self, validated_data):
        images = validated_data.pop("uploaded_images", [])
        pet = super().create(validated_data)

        PetImage.objects.bulk_create([
            PetImage(pet=pet, image=image)
            for image in images
        ])

        return pet

    def update(self, instance, validated_data):
        images = validated_data.pop("uploaded_images", [])
        pet = super().update(instance, validated_data)

        for image in images:
            PetImage.objects.create(pet=pet, image=image)

        return pet



    

class PetListSerializer(serializers.ModelSerializer):
    breed_info = TypeOfConfigSerializer(source = 'breed', read_only=True)
    images = PetImageSerializer(many=True, read_only=True)
    class Meta:
        model = Pet
        fields = '__all__'

class PetDetailSerializer(serializers.ModelSerializer):
    breed_info = TypeOfConfigSerializer(source = 'breed', read_only=True)
    pet_type_info = TypeOfConfigSerializer(source = 'pet_type', read_only=True)
    images = PetImageSerializer(many=True, read_only=True)
    class Meta:
        model = Pet
        fields = '__all__'


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