from rest_framework import serializers

from .models import User, Project, Tasks
from datetime import date
from .choices import ProjectStatus
from django.contrib.auth.hashers import make_password




# Serializers define the API representation.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["groups", "user_permissions", "is_superuser", "is_staff"]
    
    def create(self, validated_data):
        # Encrypt the password before saving
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

        if password and len(password)>=12:
            validated_data['password'] = make_password(password)

        return super().update(instance, validated_data)

class UserShortInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'avatar']


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
class EmptySerializer(serializers.Serializer):
    pass



class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

class ProjectShortInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'startDate', 'endDate', 'status', 'address']

class GetProjectSerializer(serializers.ModelSerializer):
    managers = UserShortInfoSerializer(many=True, read_only=True)
    total_tasks = serializers.SerializerMethodField()
    percentage  = serializers.SerializerMethodField()
    class Meta:
        model = Project
        fields = '__all__'

    get_total_tasks = lambda self, obj: obj.project_tasks.count()
    def get_percentage(self, obj):
        total_tasks = obj.project_tasks.count()
        if total_tasks == 0:
            return 0
        completed_tasks = obj.project_tasks.filter(status=ProjectStatus.COMPLETED).count()
        return (completed_tasks / total_tasks) * 100

class TasksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = '__all__'


    
class GetTasksSerializer(serializers.ModelSerializer):
    workers = UserShortInfoSerializer(many=True, read_only=True)
    class Meta:
        model = Tasks
        fields = '__all__'


class GetWorkerTasksSerializer(serializers.ModelSerializer):
    workers = UserShortInfoSerializer(many=True, read_only=True)
    project  = ProjectShortInfoSerializer(read_only=True)
    class Meta:
        model = Tasks
        fields = '__all__'
