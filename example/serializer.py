from rest_framework import serializers

from .models import User, Project, Tasks



# Serializers define the API representation.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["groups", "user_permissions"]

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

class GetProjectSerializer(serializers.ModelSerializer):
    managers = UserShortInfoSerializer(many=True, read_only=True)
    class Meta:
        model = Project
        fields = '__all__'

class TasksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = '__all__'

class GetTasksSerializer(serializers.ModelSerializer):
    workers = UserShortInfoSerializer(many=True, read_only=True)
    class Meta:
        model = Tasks
        fields = '__all__'
