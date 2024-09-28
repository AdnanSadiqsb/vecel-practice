# Create your views here.
from rest_framework import viewsets
from django.db.models.functions import TruncMonth

from rest_framework.permissions import IsAuthenticated
from datetime import date, datetime
from rest_framework.views import APIView
from example.services.paypal_service import make_paypal_payment, verify_paypal_payment, get_all_paypal_payments
from example.shemas import get_company_tasks
from .choices import ProjectStatus, UserRole
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
from django.db.models import Q, Count
from django.utils import timezone
import pandas as pd
from datetime import timedelta
from django.shortcuts import get_object_or_404
import randomcolor
import numpy as np  # Add this import statement

from drf_yasg.utils import swagger_auto_schema



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
    

    @action(detail=False, methods=['GET'], url_path='workers', serializer_class=serializer.WorkersListSerializer)
    def get_all_workers(self, request):
        users = User.objects.filter(role='worker')
        
        # Annotate users with task counts by status
        users = users.annotate(
            active_tasks=Count('task_workers', filter=Q(task_workers__status=ProjectStatus.ACTIVE)),
            completed_tasks=Count('task_workers', filter=Q(task_workers__status=ProjectStatus.COMPLETED)),
            cancelled_tasks=Count('task_workers', filter=Q(task_workers__status=ProjectStatus.CANCELLED)),
            pending_tasks=Count('task_workers', filter=Q(task_workers__status=ProjectStatus.PENDING))
        )
        data = self.get_serializer(users, many=True).data
        return Response(data=data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['GET'], url_path='contractors', serializer_class=serializer.ContractorssListSerializer)
    def get_all_contractors(self, request):
        users = User.objects.filter(role='contractor')
        
        # Annotate users with task counts by status
        users = users.annotate(
            active_project=Count('contractor', filter=Q(contractor__status=ProjectStatus.ACTIVE)),
            completed_project=Count('contractor', filter=Q(contractor__status=ProjectStatus.COMPLETED)),
            cancelled_project=Count('contractor', filter=Q(contractor__status=ProjectStatus.CANCELLED)),
            pending_project=Count('contractor', filter=Q(contractor__status=ProjectStatus.PENDING))
        )
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
        # projects = Project.objects.exclude(status=ProjectStatus.COMPLETED)
        projects = Project.objects.exclude(status=ProjectStatus.COMPLETED).select_related('client', 'contractor').prefetch_related('managers', 'project_tasks', 'project_tasks__workers')

        serilizer = serializer.GetProjectSerializer(projects, many=True)

        return Response(serilizer.data, status=status.HTTP_200_OK)
        
    
    @action(detail=False, methods=['GET'], url_path='projects', serializer_class=serializer.ProjectSerializer)
    def get_all_projects(self, request, pk =None):
        # projects = Project.objects.exclude(status=ProjectStatus.COMPLETED)
        projects = Project.objects.exclude(status=ProjectStatus.COMPLETED).select_related('client', 'contractor').prefetch_related('managers', 'project_tasks', 'project_tasks__workers')

        if(request.user.role == 'contractor'):
            projects = projects.filter(contractor=request.user)
        data = serializer.ProjectSerializer(projects, many=True).data  
        return Response(data=data, status=status.HTTP_200_OK)
    

    @action(detail=False, methods=['GET'], url_path='project-analaytics', serializer_class=serializer.ProjectSerializer)
    def get_project_analytics(self, request, pk=None):
        # Get the current year
        current_year = datetime.now().year

        # Annotate and count projects per month for the current year
        project_counts = Project.objects.filter(startDate__year=current_year) \
            .annotate(month=TruncMonth('startDate')) \
            .values('month') \
            .annotate(project_count=Count('id')) \
            .order_by('month')

        # Prepare response data
        months = [calendar.month_abbr[i] for i in range(1, 13)]  # ['Jan', 'Feb', ..., 'Dec']
        count_per_month = {calendar.month_abbr[i]: 0 for i in range(1, 13)}  # Initialize count for each month

        # Fill in the count for each month from the project_counts queryset
        for project in project_counts:
            month_name = project['month'].strftime("%b")  # Convert month to abbreviated name, e.g., 'Jan'
            count_per_month[month_name] = project['project_count']

        response = {
            'months': months,
            'count': [count_per_month[month] for month in months]  # List of counts in the order of months
        }

        return Response(data=response, status=status.HTTP_200_OK)
    
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
        last_mail_sent = LastMail.objects.first()
        last_mail_sent = last_mail_sent.sentAt if last_mail_sent else None

        return Response(data={'all_project':all_projects, 'active_projects':active_projects, 'completed_projects': completed_projects, 'pending_projects':pending_projects, 'workers':workers, 'managers':managers, 'last_mail_sent': last_mail_sent, 'clients':clients, 'contractors':contractors}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['GET'], url_path='my-projects-or-admin', serializer_class=serializer.GetProjectSerializer)
    def get_my_projects_or_admin(self, request, pk =None):
        print(request.user.role)
        # projects = Project.objects.exclude(status=ProjectStatus.COMPLETED)
        projects = Project.objects.exclude(status=ProjectStatus.COMPLETED).select_related('client', 'contractor').prefetch_related('managers', 'project_tasks', 'project_tasks__workers')

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
        projects = Project.objects.filter(status=ProjectStatus.COMPLETED).select_related('client', 'contractor').prefetch_related('managers', 'project_tasks', 'project_tasks__workers')

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
        # projects = Project.objects.filter(client=pk)
        projects = Project.objects.filter(client=pk).select_related('client', 'contractor').prefetch_related('managers', 'project_tasks', 'project_tasks__workers')

        data = serializer.GetClientProjectSerializer(projects, many=True).data  
        return Response(data=data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['patch'], url_path='delete-doc-tasks', serializer_class=serializer.DeleteUploadedFileSerializer)
    def delete_uploaded_file(self, request, pk =None):
        doc_name = request.data['document_name']
        project = get_object_or_404(Project, id = pk, uploaded_files__contains = [doc_name])
        project.uploaded_files.remove(doc_name)
        Tasks.objects.filter(fileName = doc_name, project = project).delete()
        project.save()
        return Response(data='tasks delete success fully', status=status.HTTP_200_OK)
    
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


import calendar

def get_current_month_intervals():
    today = timezone.now().date()
    # Get the first and last day of the current month
    first_day = today.replace(day=1)
    last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    # Calculate the range of days in the current month
    days_in_month = (last_day - first_day).days + 1
    interval_length = days_in_month // 7

    # Create intervals by dividing the month into 7 parts
    intervals = [(first_day + timedelta(days=i * interval_length),
                  first_day + timedelta(days=(i + 1) * interval_length - 1)) for i in range(7)]
    
    # Adjust the last interval to end at the last day of the month
    intervals[-1] = (intervals[-1][0], last_day)

    # Format dates for response
    dates = [interval[0].strftime('%Y-%m-%d') for interval in intervals]
    return intervals, dates


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
        tasks = Tasks.objects.select_related('project').prefetch_related('workers')

        if(request.user.role == 'contractor'):
            tasks = tasks.filter(project__contractor=request.user)
        serilizer = serializer.GetTasksSerializer(tasks, many=True)
        return Response(serilizer.data, status=status.HTTP_200_OK)
    
    
    @action(detail=False, methods=['GET'], url_path='dashboard-analaytics', serializer_class=serializer.GetTasksSerializer)
    def get_dashboard_analaytics(self, request, pk =None):
        intervals, dates = get_current_month_intervals()
        series = {
            'pending': [],
            'completed': [],
            'active': []
        }

        for start, end in intervals:
            # Count tasks grouped by status within the interval
            pending_count = Tasks.objects.filter(
                startDate__lte=end, 
                endDate__gte=start, 
                status=ProjectStatus.PENDING
            ).count()

            completed_count = Tasks.objects.filter(
                startDate__lte=end, 
                endDate__gte=start, 
                status=ProjectStatus.COMPLETED
            ).count()

            active_count = Tasks.objects.filter(
                startDate__lte=end, 
                endDate__gte=start, 
                status=ProjectStatus.ACTIVE
            ).count()

            # Append counts to the respective series
            series['pending'].append(pending_count)
            series['completed'].append(completed_count)
            series['active'].append(active_count)

        # Format the response as per the required structure
        response = {
            'series': [
                {'name': 'pending', 'data': series['pending']},
                {'name': 'completed', 'data': series['completed']},
                {'name': 'active', 'data': series['active']}
            ],
            'dates': dates
        }


        return Response(data=response, status=status.HTTP_200_OK)

    
    @action(detail=True, methods=['GET'], url_path='project', serializer_class=serializer.GetTasksSerializer)
    def get_projects(self, request, pk =None):
        tasks = Tasks.objects.select_related('project').prefetch_related('workers').filter(project=pk)

        data = serializer.GetTasksSerializer(tasks, many=True).data  
        return Response(data=data, status=status.HTTP_200_OK)
    

    @swagger_auto_schema(**get_company_tasks())
    @action(detail=False, methods=['GET'], url_path='today-tasks', serializer_class=serializer.GetTasksSerializer, permission_classes = [AllowAny])
    def get_today_tasks(self, request, pk =None):
        today = timezone.now().date()
        project = request.query_params.get('project', 'all')
        todayTasks = Tasks.objects.select_related('project').prefetch_related('workers').filter(startDate__lte=today, endDate__gte=today)
        # todayTasks = Tasks.objects.filter(startDate__lte=today, endDate__gte=today)

        if project != 'all':
            todayTasks = todayTasks.filter(project=project)
        data = serializer.GetTasksSerializer(todayTasks, many=True).data  
        return Response(data=data, status=status.HTTP_200_OK)
    


    @action(detail=False, methods=['GET'], url_path='worker-today/(?P<worker>[0-9a-f-]{36})', serializer_class=serializer.GetTasksSerializer, permission_classes = [AllowAny])
    def get_worker_today_tasks(self, request,worker):
        today = timezone.now().date()
        todayTasks = Tasks.objects.select_related('project').prefetch_related('workers').filter(startDate__lte=today, endDate__gte=today, workers = worker)

        data = serializer.GetTasksSerializer(todayTasks, many=True).data  
        return Response(data=data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['GET'], url_path='worker-tasks', serializer_class=serializer.GetWorkerTasksSerializer)
    def get_worker_tasks(self, request, pk =None):
        tasks = Tasks.objects.filter(workers = pk)
        data = serializer.GetWorkerTasksSerializer(tasks, many=True).data
        return Response(data=data, status=status.HTTP_200_OK)
    

    @action(detail=False, methods=['GET'], url_path='all-tasks', serializer_class=serializer.GetWorkerTasksSerializer)
    def get_all_tasks(self, request, pk =None):
        tasks = Tasks.objects.select_related('project').prefetch_related('workers')
        
        data = serializer.GetWorkersTasksSerializer(tasks, many=True).data
        return Response(data=data, status=status.HTTP_200_OK)


    
    @action(detail=True, methods=['DELETE'], url_path='worker/(?P<worker>[0-9a-f-]{36})')
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
    

    @action(detail=False, methods=['POST'], url_path='bulk-upload/(?P<project>[0-9a-f-]{36})', permission_classes = [AllowAny], serializer_class=serializer.addTasksXLSSErialixer, parser_classes = (FormParser, MultiPartParser))
    def bulk_upload_tasks(self, request, project =None):

        file = request.data['file']
        
        file_name   = f'{file.name} on {datetime.now()}'
        df = pd.read_excel(file)
        # Read the Excel file and convert to a list of dictionaries
        excel_data = df.replace({np.nan: ''}).to_dict(orient='records')

        # Print the data
        start = timezone.now().date()
        end = timezone.now().date() + timedelta(days=4)
        project = get_object_or_404(Project, id = project)
        count  = 0
        for row in excel_data:
            if 'labor' in str(row.get('Cost Code', '')).lower():
                data = {
                    'project': project,
                    'title': row['Title'],
                    'description': row.get('Description', ''),
                    'startDate': start,
                    'endDate': end,
                    'color': randomcolor.RandomColor().generate()[0],
                    'costCode': row.get('Cost Code', ''),
                    'quantity': row.get('Quantity', ''),
                    'unit': row.get('Unit', ''),
                    'fileName':file_name
                }
                count += 1
                task = Tasks.objects.create(**data)

        project.uploaded_files.append(file_name)
        project.save()
        return Response(data=f'{count} tasks are created successfully', status=status.HTTP_200_OK)
    


class PaypalPaymentView(viewsets.GenericViewSet):
    """
    endpoint for create payment url
    """
    queryset = Tasks.objects.all()
    serializer_class = serializer.TasksSerializer
    @action(detail=False, methods=['POST'], url_path='create-link', serializer_class=serializer.CreatePaypalLinkSerializer)
    def create_payment_link(self, request):

        amount=20 # 20$ for example
        status,payment_id,approved_url=make_paypal_payment(amount=request.data['amount'],description=request.data['description'], currency="USD",return_url="https://example.com/payment/paypal/success/",cancel_url="https://example.com")
        if status:
            # handel_subscribtion_paypal(plan=plan,user_id=request.user,payment_id=payment_id)
            return Response({"success":True,"msg":"payment link has been successfully created","approved_url":approved_url},status=201)
        else:
            return Response({"success":False,"msg":"Authentication or payment failed"},status=400)
        
    
    @action(detail=False, methods=['GET'], url_path='payments', serializer_class=serializer.CreatePaypalLinkSerializer)
    def get_all_payments(self, request):

        payments = get_all_paypal_payments()
        return Response(data=payments,status=201)
       



class PaypalValidatePaymentView(APIView):
    """
    endpoint for validate payment 
    """
    # permission_classes=[IsAuthenticated,]

    def post(self, request, *args, **kwargs):
        # payment_id=request.data.get("payment_id")
        payment_id= 'PAYID-M3AGIAA4AL50455CR637712P'
        payment_status=verify_paypal_payment(payment_id=payment_id)
        if payment_status:
            # your business logic 
             
            return Response({"success":True,"msg":"payment improved"},status=200)
        else:
            return Response({"success":False,"msg":"payment failed or cancelled"},status=200)
    

