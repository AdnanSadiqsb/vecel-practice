from drf_yasg import openapi


company = openapi.Parameter('company', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Company ID', default='all')
supplier = openapi.Parameter('supplier', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Supplier ID')
manager = openapi.Parameter('manager', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Manager ID')
client  = openapi.Parameter('client', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Client ID')
def get_company_tasks():
    return {'manual_parameters': [company],}

def get_supplier_workers():
    return {'manual_parameters': [supplier],}

def get_manager_projects():
    return {'manual_parameters': [manager, client],}