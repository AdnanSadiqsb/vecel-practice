from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
# from celery import shared_task
import datetime
class SMTPMailService:
    @staticmethod
    def send_mail_service(subject, message, recipient_list):
        email_from = settings.EMAIL_HOST_USER
        send_mail(subject, message, email_from, recipient_list)
    
    @staticmethod
    def send_html_mail_service(subject,template, template_data, recipient_list):
        # try:
            template_data['datetime']= datetime
            message_html = render_to_string(template_name=template, context=template_data)
            email_from = settings.EMAIL_HOST_USER
            resp = send_mail(subject, '', email_from, recipient_list, html_message=message_html)
        # except Exception as e:
        #     print(e)
