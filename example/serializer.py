from rest_framework import serializers

from .models import User, Project, Tasks
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


class ProjectSerializer(serializers.ModelSerializer):
    clientInfo = serializers.JSONField(write_only=True, required =False)  # Serializer for creating client
    contractorInfo = serializers.JSONField(write_only=True, required =False)
    class Meta:
        model = Project
        fields = '__all__'
    
    def get_next_color(self):
        last_project = Project.objects.order_by('-id').first()
        if last_project:
            last_color = last_project.color
            if last_color in colors:
                next_index = (colors.index(last_color) + 1) % len(colors)
                return colors[next_index]
        return colors[0]

    def create(self, validated_data):
        client_info_data = validated_data.pop('clientInfo', None)
        contractor_info_data = validated_data.pop('contractorInfo', None)
        if 'color' not in validated_data or not validated_data['color']:
            validated_data['color'] = self.get_next_color()
        with transaction.atomic():
            if not validated_data.get('client', None) and client_info_data and client_info_data.get('email'):
                client = self.get_or_create_user(client_info_data, role='client', context=self.context)
                validated_data['client'] = client
            
            if not validated_data.get('contractor', None) and contractor_info_data and contractor_info_data.get('email'):
                contractor = self.get_or_create_user(contractor_info_data, role='contractor', context=self.context)
                validated_data['contractor'] = contractor
        
            return super().create(validated_data)


    def update(self, instance, validated_data):
        # Encrypt the password if it's present in validated_data
        original_project = Project.objects.get(pk=instance.pk)
        print("original_project", original_project.color)
        print("instace", instance.color)
        if original_project.color != instance.color:
            Tasks.objects.filter(project=instance).update(color=instance.color)

        return super().update(instance, validated_data)
    
    def get_or_create_user(self, user_data, role, context):
        if user_data:
            serializer = UserSerializer(data={**user_data, "role": role}, context=context)
            serializer.is_valid(raise_exception=True)
            return serializer.save()
        return None

class ProjectShortInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'startDate', 'endDate', 'status', 'address']

class GetProjectSerializer(serializers.ModelSerializer):
    managers = UserShortInfoSerializer(many=True, read_only=True)
    client = UserShortInfoSerializer(read_only=True)
    contractor = UserShortInfoSerializer(read_only=True)
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
    
class DeleteUploadedFileSerializer(serializers.Serializer):
    document_name = serializers.CharField()

class TasksSerializer(serializers.ModelSerializer):
    schedule_mode = serializers.BooleanField( write_only=True, required=False, default=False)
    class Meta:
        model = Tasks
        fields = '__all__'
    
    def create(self, validated_data):
        schedule_mode = validated_data.pop('schedule_mode', False)
        created_instance = super().create(validated_data)
        print("created instance", created_instance)
        newTaksMailToContractor(task=created_instance.pk)
        if schedule_mode:
           sendMailOnTaskHandler(task=created_instance.pk) 
        return created_instance
    
    def update(self, instance, validated_data):
        # Fetch existing data from the database
        schedule_mode = validated_data.pop('schedule_mode', False)
        existing_instance = Tasks.objects.get(pk=instance.pk)
        print("schedule mode", schedule_mode)
        # Call the super method to perform the update
        updated_instance = super().update(instance, validated_data)
        if status == ProjectStatus.COMPLETED:
            sendMailToClientAndContractor(task=updated_instance.pk)
        if(schedule_mode):
            return updated_instance

        status = validated_data.get('status', None)

          
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


class GetClientProjectSerializer(serializers.ModelSerializer):
 
    total_tasks = serializers.SerializerMethodField()
    percentage  = serializers.SerializerMethodField()
    project_tasks = TasksSerializer(many=True, read_only=True)
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
        worker_ids = [worker.id for worker in workers] 
        users = User.objects.filter(id__in=worker_ids, is_sentMail=True)
        message = 'You have been assigned a new task. Please review the details below:'
        subject = "New Task"

        if action == 'update':
            message = 'The task assigned to you has been updated. Please review the changes below:'
            subject = "Task Updated"
        task = GetTasksFormEmailOnCUSerializer(taskObj).data

        start_obj = datetime.strptime(task['startDate'], "%Y-%m-%d")
        end_obj = datetime.strptime(task['endDate'], "%Y-%m-%d")
        task['startDate'] = start_obj.strftime("%a %m/%d/%y")
        task['endDate'] = end_obj.strftime("%a %m/%d/%y")
        current_datetime = datetime.now()
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        subject_with_datetime = f"{subject} - {datetime_string}"
        print("subject", subject_with_datetime)
        for user in users:
            print("user", user)
            # Customize template_data for each user
            template_data = {
                'task': task,
                'message': message,
                'email': user.email,
                'password':user.plain_password,
                'link': settings.FRONTEND_BASE_URL
            }
            print("email", user.email)
            SMTPMailService.send_html_mail_service(
                subject=subject_with_datetime,
                template='cutask.html',
                template_data=template_data,
                recipient_list=[user.email]  # Send email to each user individually
            )  
def sendMailToClientAndContractor(task):
   
    task= Tasks.objects.get(id=task)
    if(task.project.client):
        print("clint mail sent")
        SMTPMailService.send_html_mail_service(
        subject=f'{task.title} completed',
        template='common.html',
        template_data={
            'message':f'''
I am pleased to inform you that the task <b>{task.title}</b> has been successfully completed.
<br>
<br>
<br>
Please feel free to review the work at your earliest convenience. If you have any questions or require further assistance, do not hesitate to reach out to me.
<br>
<br>
Thank you for entrusting us with this task. We look forward to continuing our collaboration in the future.
''',
            'reciverName':task.project.client.username,
            'role':task.project.client.role
        },
        recipient_list=[task.project.client.email] 
        )  

    if(task.project.contractor):
        print("clint mail sent")
        SMTPMailService.send_html_mail_service(
        subject=f'{task.title} completed',
        template='common.html',
        template_data={
            'message':f'''
I am pleased to inform you that the task <b>{task.title}</b> you were assigned has been successfully completed.  
<br>
<br>
Your dedication and hard work have contributed significantly to the success of this project, and we sincerely appreciate your efforts.
<br>
<br>
Please feel free to review the completed work, and if you have any questions or require further clarification, don't hesitate to reach out.
''',
            'reciverName':task.project.contractor.username,
            'role':task.project.contractor.role,
        },
        recipient_list=[task.project.contractor.email]  # Send email to each user individually
        )  

def newTaksMailToContractor(task):
    task= Tasks.objects.get(id=task)
    if(task.project.contractor):
        print("clint mail sent")
        SMTPMailService.send_html_mail_service(
        subject=f'New task {task.title} ',
        template='common.html',
        template_data={
            'message':f'''
    I'm writing to inform you that a new task <b>{task.title}</b> has been assigned to you. Please log in to your profile to view the details of the task and get started at your earliest convenience.
<br>
<br>
If you have any questions or need further clarification regarding the task, please don't hesitate to reach out to me.

''',
            'reciverName':task.project.contractor.username,
            'role':task.project.contractor.role
        },
        recipient_list=[task.project.contractor.email] 
        )  

class TasksSerializer(serializers.ModelSerializer):
    schedule_mode = serializers.BooleanField( write_only=True, required=False, default=False)
    class Meta:
        model = Tasks
        fields = '__all__'
    
    def create(self, validated_data):
        schedule_mode = validated_data.pop('schedule_mode', False)
        created_instance = super().create(validated_data)
        print("created instance", created_instance)
        newTaksMailToContractor(task=created_instance.pk)
        if schedule_mode:
           sendMailOnTaskHandler(task=created_instance.pk) 
        return created_instance
    
    def update(self, instance, validated_data):
        # Fetch existing data from the database
        schedule_mode = validated_data.pop('schedule_mode', False)
        existing_instance = Tasks.objects.get(pk=instance.pk)
        print("schedule mode", schedule_mode)
        # Call the super method to perform the update
        updated_instance = super().update(instance, validated_data)
        status = validated_data.get('status', None)
        if status == ProjectStatus.COMPLETED:
            sendMailToClientAndContractor(task=updated_instance.pk)
        if(schedule_mode):
            return updated_instance


          
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

        tasks = obj.project_tasks.filter(
            Q(workers=self.context['worker'].id) & ~Q(status=ProjectStatus.COMPLETED)
        )        
        serializer = TasksSerializer(tasks, many=True)
        return serializer.data
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
class SendMailToWorkersSerializer(serializers.Serializer):
    worker = serializers.CharField(max_length = 3, default='all')



class addTasksXLSSErialixer(serializers.Serializer):
    file = serializers.FileField()