"""vercel_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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



from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('example.urls')),
    path('', server_running),
]