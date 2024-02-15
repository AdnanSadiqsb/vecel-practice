
from django.http import HttpResponse
def server_running(request):
    content = """
    <html>
    <head>
        <style>
            body {
                background: #EFEFBB;  /* fallback for old browsers */
                background: -webkit-linear-gradient(to right, #D4D3DD, #EFEFBB);  /* Chrome 10-25, Safari 5.1-6 */
                background: linear-gradient(to right, #D4D3DD, #EFEFBB); /* W3C, IE 10+/ Edge, Firefox 16+, Chrome 26+, Opera 12+, Safari 7+ */

            }
            h1 {
                font-family: system-ui;
                color: black;
                font-size: 30px;
                text-align: center;
                margin-top: 50px;
                margin-top: 50px;
            }
            p{
                text-align: center;
                font-size: 2rem;
            }
            div{
                margin-top:100px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            h5{
                text-align: center;
                color: darkolivegreen;
            }
            
        </style>
    </head>
    <body>
    <div>
    	<img src="https://humanalytics.s3.amazonaws.com/media/logo/Cleaning/logo-dark.svg">
        </div>
        <h1>TIMELINE server is online and operational.</h1> 
        <h5 class="text-center">V 1.1</h5>
    </body>
    </html>

    """
    return HttpResponse(content)

from drf_yasg import openapi
from rest_framework import permissions
from drf_yasg.views import get_schema_view
schema_view = get_schema_view(
    openapi.Info(
        title="Timeline API",
        default_version="v1",
        description="Project to manage the project and tasks assigned to workers",
        contact=openapi.Contact(email="adnansadiqxyz@gmail.com"),
        license=openapi.License(name="Tech Force"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('example.urls')),
    path('', server_running),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]