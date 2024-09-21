from drf_yasg import openapi


company = openapi.Parameter('company', openapi.IN_PATH, type=openapi.TYPE_STRING, description='Company ID', default='all')
def get_company_tasks():
    return {'manual_parameters': [company],}