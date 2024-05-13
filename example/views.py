# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from datetime import date, datetime
from .choices import ProjectStatus
from .models import User, Project, Tasks, LastMail
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework import serializers, mixins
from rest_framework.authtoken.models import Token
from rest_framework.parsers import FormParser, MultiPartParser
from .services.mail_serive import SMTPMailService
from . import serializer
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
import pandas as pd
from datetime import timedelta
from django.shortcuts import get_object_or_404
import randomcolor
import numpy as np  # Add this import statement




class UserViewSet(viewsets.ModelViewSet):
    parser_classes = (FormParser, MultiPartParser)
    queryset = User.objects.all()
    serializer_class = serializer.UserSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['GET'], url_path='by-role/(?P<role>[^/]+)', serializer_class=serializer.UserSerializer)
    def get_users_by_role(self, request, role =None):
        users = User.objects.filter(role=role)
        data = self.get_serializer(users, many=True).data  
        return Response(data=data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['GET'], url_path='by-role-option/(?P<role>[^/]+)', serializer_class=serializer.UserShortInfoSerializer)
    def get_users_by_role_for_option(self, request, role =None):
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
    
def determine_status(start_date, end_date):
    # Get the current date
    current_date = datetime.now().date()  # Use datetime.now() to get both date and time

    # Parse start_date and end_date strings into datetime.date objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None

    # Determine the status based on the dates
    if start_date <= current_date <= end_date:
        return "active"
    elif start_date > current_date:
        return "pending"
    elif current_date > end_date:
        return "completed"
    return None

class ProjectViewSet(viewsets.ModelViewSet):
    parser_classes = (FormParser, MultiPartParser)
    queryset = Project.objects.all()
    serializer_class = serializer.ProjectSerializer
    permission_classes = [IsAuthenticated]
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializer.GetProjectSerializer
        return self.serializer_class
    
    def create(self, request, *args, **kwargs):
        requestData = request.data.copy()
        start_date = request.data.get('startDate')
        end_date = request.data.get('endDate')
        statusAc = determine_status(start_date, end_date)
        requestData['status'] = statusAc
        serializ = serializer.ProjectSerializer(data=requestData)
        serializ.is_valid(raise_exception=True)
        serializ.save()
        return Response(serializ.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        projects = Project.objects.exclude(status=ProjectStatus.COMPLETED)


        serilizer = serializer.GetProjectSerializer(projects, many=True)

        return Response(serilizer.data, status=status.HTTP_200_OK)
        
    
    @action(detail=False, methods=['GET'], url_path='projects', serializer_class=serializer.ProjectSerializer)
    def get_all_projects(self, request, pk =None):
        projects = Project.objects.exclude(status=ProjectStatus.COMPLETED)
        if(request.user.role == 'contractor'):
            projects = projects.filter(contractor=request.user)
        data = serializer.ProjectSerializer(projects, many=True).data  
        return Response(data=data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['GET'], url_path='dashboard', serializer_class=serializer.ProjectSerializer)
    def get_project_stats(self, request, pk =None):
        projects = Project.objects.all()
        all_projects = projects.count()
        active_projects = projects.filter(status=ProjectStatus.ACTIVE).count()
        completed_projects = projects.filter(status=ProjectStatus.COMPLETED).count()
        pending_projects = projects.filter(status=ProjectStatus.PENDING).count()
        workers = User.objects.filter(role='worker').count()
        managers = User.objects.filter(role='manager').count()
        clients = User.objects.filter(role='client').count()
        contractors = User.objects.filter(role='contractor').count()
        last_mail_sent = LastMail.objects.first().sentAt

        return Response(data={'all_project':all_projects, 'active_projects':active_projects, 'completed_projects': completed_projects, 'pending_projects':pending_projects, 'workers':workers, 'managers':managers, 'last_mail_sent': last_mail_sent, 'clients':clients, 'contractors':contractors}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['GET'], url_path='my-projects-or-admin', serializer_class=serializer.GetProjectSerializer)
    def get_my_projects_or_admin(self, request, pk =None):
        print(request.user.role)
        projects = Project.objects.exclude(status=ProjectStatus.COMPLETED)
        if request.user.role == 'manager':
            projects = projects.filter(managers=request.user.id)
        elif request.user.role == 'contractor':
            projects = projects.filter(contractor=request.user.id)
        elif request.user.role == 'client':
            projects = projects.filter(client=request.user.id)
        data = serializer.GetProjectSerializer(projects, many=True).data  
        return Response(data=data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'], url_path='completed', serializer_class=serializer.GetProjectSerializer)
    def get_completed_projects(self, request, pk =None):
        print(request.user.role)
        projects = Project.objects.filter(status=ProjectStatus.COMPLETED)
        if request.user.role == 'manager':
            projects = projects.filter(managers=request.user.id)
        elif request.user.role == 'contractor':
            projects = projects.filter(contractor=request.user.id)
        elif request.user.role == 'client':
            projects = projects.filter(client=request.user.id)
        elif request.user.role == 'worker':
            projects = projects.filter(project_tasks__workers=request.user.id)
        data = serializer.GetProjectSerializer(projects, many=True).data  
        return Response(data=data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['GET'], url_path='client-projects', serializer_class=serializer.GetProjectSerializer)
    def get_client_projects(self, request, pk =None):
        print(request.user.role)
        projects = Project.objects.filter(client=pk)
        
        data = serializer.GetClientProjectSerializer(projects, many=True).data  
        return Response(data=data, status=status.HTTP_200_OK)
    
def sendTaskToWorker(worker):
    print("mail sent called")
    projects = Project.objects.filter(Q(project_tasks__workers=worker) & ~Q(status=ProjectStatus.COMPLETED)).distinct()
    serialize = serializer.GetWorkerProjectForMailSerializer(projects, many=True, context={'worker':worker})
    respData = serialize.data.copy()
    for project in respData:
        # Convert startDate and endDate format for each task in the project
        for task in project["tasks"]:
            task["startDate"] = datetime.strptime(task["startDate"], "%Y-%m-%d").strftime("%a %m/%d/%y")
            task["endDate"] = datetime.strptime(task["endDate"], "%Y-%m-%d").strftime("%a %m/%d/%y")

        # Convert startDate and endDate format for the project itself
        project["startDate"] = datetime.strptime(project["startDate"], "%Y-%m-%d").strftime("%a %m/%d/%y")
        project["endDate"] = datetime.strptime(project["endDate"], "%Y-%m-%d").strftime("%a %m/%d/%y")
    template_data={
    'reciverName':worker.username,
    'projects': respData,
    'email': worker.email,
    'password':worker.plain_password,
    'link': settings.FRONTEND_BASE_URL
    }
    datetime_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject_with_datetime = f"Your Assigned Tasks - {datetime_string}"
    print("temp data", template_data)
    SMTPMailService.send_html_mail_service(subject=subject_with_datetime, template='tasks.html', template_data=template_data, recipient_list = [worker.email])
    
def darken_color(color, factor=0.5):
    """
    Darken a color by a given factor.
    Factor should be between 0 and 1.
    """
    r, g, b = color[0:3]  # Extract RGB components
    return (
        int(r * factor),
        int(g * factor),
        int(b * factor)
    )

class TaskViewSet(viewsets.ModelViewSet):
    parser_classes = (FormParser, MultiPartParser)
    queryset = Tasks.objects.all()
    serializer_class = serializer.TasksSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializer.GetTasksSerializer
        return self.serializer_class
    
    def create(self, request, *args, **kwargs):
        requestData = request.data.copy()
        start_date = request.data.get('startDate')
        end_date = request.data.get('endDate')
        statusAc = determine_status(start_date, end_date)
        requestData['status'] = statusAc
        serializ = serializer.TasksSerializer(data=requestData)
        serializ.is_valid(raise_exception=True)
        serializ.save()
        serializer.sendMailOnTaskHandler(task= serializ.data['id'])
        return Response(serializ.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        tasks = Tasks.objects.all()
        if(request.user.role == 'contractor'):
            tasks = tasks.filter(project__contractor=request.user)
        serilizer = serializer.GetTasksSerializer(tasks, many=True)
        return Response(serilizer.data, status=status.HTTP_200_OK)
    @action(detail=True, methods=['GET'], url_path='project', serializer_class=serializer.GetTasksSerializer)
    def get_projects(self, request, pk =None):
        users = Tasks.objects.filter(project=pk)
        data = serializer.GetTasksSerializer(users, many=True).data  
        return Response(data=data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['GET'], url_path='worker-tasks', serializer_class=serializer.GetWorkerTasksSerializer)
    def get_all_worker_tasks(self, request, pk =None):
        tasks = Tasks.objects.filter(workers = pk)
        data = serializer.GetWorkerTasksSerializer(tasks, many=True).data
        return Response(data=data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['DELETE'], url_path='worker/(?P<worker>\d+)')
    def delete_worker_tasks(self, request, pk=None, *args, **kwargs):
        task = Tasks.objects.get(id=pk)
        worker_id = kwargs.get('worker')
        if worker_id is not None:
            task.workers.remove(worker_id)
            task.save()
            return Response(data='Worker deleted from the task', status=status.HTTP_200_OK)
        else:
            return Response(data='Invalid worker ID provided', status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['POST'], url_path='worker-mail', permission_classes = [IsAuthenticated], serializer_class=serializer.SendMailToWorkersSerializer)
    def send_email_to_workers(self, request, pk =None):
        rqst = request.data['worker']
        workers = []
        if rqst=='all':
            workers = User.objects.filter(is_active = True, is_sentMail = True)
            instance, created = LastMail.objects.get_or_create(defaults={'sentAt':timezone.now()})
            instance.__dict__.update({'sentAt':timezone.now()})
            instance.save()
        else:
            workers  = User.objects.filter(id=rqst)  
        print(workers)
        for worker in workers:
            sendTaskToWorker(worker)
        
        return Response(data='mail sent to workers', status=status.HTTP_200_OK)
    

    @action(detail=False, methods=['POST'], url_path='bulk-upload/(?P<project>\d+)', permission_classes = [AllowAny], serializer_class=serializer.addTasksXLSSErialixer, parser_classes = (FormParser, MultiPartParser))
    def bulk_upload_tasks(self, request, project =None):

        file = request.data['file']
        df = pd.read_excel(file)
        # Read the Excel file and convert to a list of dictionaries
        excel_data = df.replace({np.nan: ''}).to_dict(orient='records')

        # Print the data
        start = timezone.now().date()
        end = timezone.now().date() + timedelta(days=4)
        project = get_object_or_404(Project, id = project)
        count  = 0
        for row in excel_data:
            data = {
                'project' : project,
                'title' : row['Title'],
                'description' : row.get('Description',''),
                'startDate' : start,
                'endDate' : end,
                'color':  randomcolor.RandomColor().generate()[0],
                'costCode': row.get('Cost Code', ''),
                'quantity': row.get('Quantity', ''),
                'unit': row.get('Unit', '')

            }
            count +=1
            task = Tasks.objects.create(**data)
        return Response(data=f'{count} tasks are created successfully', status=status.HTTP_200_OK)
    
    

