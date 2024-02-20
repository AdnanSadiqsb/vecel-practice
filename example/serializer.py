from rest_framework import serializers

from .models import User, Project, Tasks



# Serializers define the API representation.
class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.FileField(max_length=None, allow_empty_file=True, use_url=True)
    class Meta:
        model = User
        exclude = ["groups", "user_permissions", "is_superuser", "is_staff"]
    
    def create(self, validated_data):
        # Check if role is 'admin', if yes, set is_superuser to True, otherwise False
        role = validated_data.get('role', None)
        if role == 'admin':
            validated_data['is_superuser'] = True
        else:
            validated_data['is_superuser'] = False
        
        return super().create(validated_data)

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
    total_tasks = serializers.SerializerMethodField()
    class Meta:
        model = Project
        fields = '__all__'

    get_total_tasks = lambda self, obj: obj.project_tasks.count()

class TasksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = '__all__'

class GetTasksSerializer(serializers.ModelSerializer):
    workers = UserShortInfoSerializer(many=True, read_only=True)
    class Meta:
        model = Tasks
        fields = '__all__'
