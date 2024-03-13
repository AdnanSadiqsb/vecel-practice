from rest_framework import serializers

from .models import User, Project, Tasks
from datetime import date
from .choices import ProjectStatus
from django.contrib.auth.hashers import make_password
from .services.mail_serive import SMTPMailService
from django.shortcuts import get_object_or_404


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
        print("password", password)
        if password and len(password)<=12:
            validated_data['password'] = make_password(password)
            print("inside up")

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
    

def sendMailOnTaskHandler(task=0, action='create' ):
        print("inside func call")
        taskObj = get_object_or_404(Tasks, id=task)
        workers = taskObj.workers.all()
        print("workers,", workers)
        worker_ids = [worker.id for worker in workers] 
        print("worker ids", worker_ids)
        users = User.objects.filter(id__in=worker_ids)
        emails = [user.email for user in users]
        message='You have been assigned a new task. Please review the details below:'
        subject = "New Task"
        if(action=='update'):
            message='The task assigned to you has been updated. Please review the changes below:'
            subject = "Task Updated"

        template_data={
        'task': GetTasksFormEmailOnCUSerializer(taskObj).data,
        'message':message
        }

        SMTPMailService.send_html_mail_service(subject=subject, template='cutask.html', template_data=template_data, recipient_list = emails)   

class TasksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = '__all__'
    
    def update(self, instance, validated_data):
        # Fetch existing data from the database
        existing_instance = Tasks.objects.get(pk=instance.pk)

        # Call the super method to perform the update
        updated_instance = super().update(instance, validated_data)

        # Check if any of the specified fields have changed
        if (validated_data.get('title', existing_instance.title) != existing_instance.title or
            validated_data.get('description', existing_instance.description) != existing_instance.description or
            validated_data.get('startDate', existing_instance.startDate) != existing_instance.startDate or
            validated_data.get('endDate', existing_instance.endDate) != existing_instance.endDate or
            validated_data.get('workers', existing_instance.workers) != existing_instance.workers or
            validated_data.get('status', existing_instance.status) != existing_instance.status):

            # Call the sendMailOnTaskHandler function if any of the specified fields have changed
            print("mail set func called")
            sendMailOnTaskHandler(task=updated_instance.pk, action='update')

        return updated_instance


class GetTasksFormEmailOnCUSerializer(serializers.ModelSerializer):
    project  = ProjectShortInfoSerializer(read_only=True)
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


class GetWorkerProjectForMailSerializer(serializers.ModelSerializer):
    tasks  = serializers.SerializerMethodField()
    class Meta:
        model = Project
        fields = '__all__'

    def get_tasks(self, obj):
        print("context worker", self.context['worker'].id)
        tasks = obj.project_tasks.filter(workers = self.context['worker'].id)
        serializer = TasksSerializer(tasks, many=True)
        return serializer.data