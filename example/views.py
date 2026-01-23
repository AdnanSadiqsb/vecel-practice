# Create your views here.
import math
from rest_framework import viewsets
from django.db.models.functions import TruncMonth
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
import stripe
from example.services.paypal_service import make_paypal_payment, get_paypal_payment_by_id, get_all_paypal_payments, execute_paypal_payment
from .models import PayPalPayment, User, typeOfConfig, Pet, PetImage
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework import serializers, mixins
from rest_framework.authtoken.models import Token
from rest_framework.parsers import FormParser, MultiPartParser
from . import serializer
from django.conf import settings
from django.db.models import Q, Count
from django.utils import timezone
import pandas as pd
from datetime import timedelta
from django.shortcuts import get_object_or_404
import randomcolor
import numpy as np  # Add this import statement
from rest_framework.renderers import JSONRenderer
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from urllib.parse import urljoin

import requests

from django.urls import reverse

class UserViewSet(viewsets.GenericViewSet,  mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    # parser_classes = (FormParser, MultiPartParser)
    queryset = User.objects.all()
    serializer_class = serializer.UserSerializer
    # permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        if self.action == "signup_google":
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'manual_signup':
            return serializer.UserCreateSerializer
        if self.action == 'signup_google':
            return serializer.LoginWithGoogleSerializer
        

        return serializer.UserSerializer
    


    @action(
    detail=False,
    methods=['POST'],
    url_path='signup-google',
    permission_classes=[AllowAny],
    authentication_classes=[]
    )
    def signup_google(self, request):
        id_token_value = request.data.get('id_token')

        if not id_token_value:
            return Response(
                {'error': 'ID token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            id_info = id_token.verify_oauth2_token(
                id_token_value,
                google_requests.Request(),
                settings.GOOGLE_MOBILE_CLIENT_ID
            )
        except ValueError as e:
            return Response(
                {'error': 'Invalid Google token', 'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        google_id = id_info['sub']
        email = id_info.get('email')
        name = id_info.get('name', '')

        user = User.objects.filter(
            Q(email=email) | Q(google_id=google_id)
        ).first()

        if not user:
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User.objects.create(
                username=username,
                email=email,
                name=name,
                google_id=google_id,
                is_active=True
            )
        else:
            if not user.google_id:
                user.google_id = google_id
                user.save()

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
            },
            'token': token.key,
            'message': 'Successfully authenticated with Google'
        }, status=status.HTTP_200_OK)
                
     
      
    
    @action(detail=False, methods=['POST'], url_path='signup-apple', permission_classes=[AllowAny])
    def signup_apple(self, request):
        # Placeholder for Apple signup
        # Implement OAuth flow here
        return Response({'message': 'Apple signup not implemented yet'}, status=501)
    
    @action(detail=False, methods=['POST'], url_path='signup-manual', permission_classes=[AllowAny], serializer_class=serializer.UserCreateSerializer)
    def manual_signup(self, request):
        self_serializer = self.get_serializer(data=request.data)
        self_serializer.is_valid(raise_exception=True)
        user = self_serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        user_info = serializer.UserSerializer(user)
        return Response({
            'user': user_info,
            'token': token.key,
            'message': 'Successfully created new user'
        }, status=status.HTTP_200_OK)
        # Placeholder for Apple signup
        # Implement OAuth flow here
    



class GoogleLoginCallback(APIView):
    renderer_classes = [JSONRenderer]  # 🔥 THIS FIXES THE ERROR

    def get(self, request, *args, **kwargs):
        code = request.GET.get("code")

        if not code:
            return Response(
                {"error": "Authorization code not provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔹 STEP 1: Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_OAUTH_CALLBACK_URL,
            "grant_type": "authorization_code",
        }

        token_response = requests.post(token_url, data=token_data)
        token_response_data = token_response.json()

        if "id_token" not in token_response_data:
            return Response(
                {"error": "Failed to obtain ID token from Google"},
                status=status.HTTP_400_BAD_REQUEST
            )

        id_token_value = token_response_data["id_token"]

        # 🔹 STEP 2: Verify ID token
        try:
            id_info = id_token.verify_oauth2_token(
                id_token_value,
                google_requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID
            )
        except ValueError:
            return Response(
                {"error": "Invalid Google token"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔹 STEP 3: Extract user info
        google_id = id_info["sub"]
        email = id_info.get("email")
        name = id_info.get("name", "")

        # 🔹 STEP 4: Create / Get user
        user = User.objects.filter(
            Q(email=email) | Q(google_id=google_id)
        ).first()

        if user:
            if not user.google_id:
                user.google_id = google_id
                user.save()
        else:
            base_username = email.split("@")[0]
            username = base_username
            counter = 1

            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User.objects.create(
                username=username,
                email=email,
                name=name,
                google_id=google_id,
                is_active=True
            )

        # 🔹 STEP 5: DRF Token
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                },
                "message": "Google login successful",
            },
            status=status.HTTP_200_OK
        )


class GoogleMobileLogin(APIView):
    permission_classes = []
    serializer_class = serializer.LoginWithGoogleSerializer

    def post(self, request):
        id_token_value = request.data.get("id_token")

        if not id_token_value:
            return Response(
                {"error": "ID token not provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            id_info = id_token.verify_oauth2_token(
                id_token_value,
                google_requests.Request(),
                settings.GOOGLE_MOBILE_CLIENT_ID
            )
        except ValueError:
            return Response(
                {"error": "Invalid Google token"},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = id_info.get("email")
        google_id = id_info.get("sub")
        name = id_info.get("name", "")

        user = User.objects.filter(
            Q(email=email) | Q(google_id=google_id)
        ).first()

        if not user:
            user = User.objects.create(
                username=email.split("@")[0],
                email=email,
                name=name,
                google_id=google_id,
                is_active=True
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
            },
            "message": "Google login successful"
        })

class TypeOfConfigViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    queryset = typeOfConfig.objects.all()
    serializer_class = serializer.TypeOfConfigSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (FormParser, MultiPartParser)


    @swagger_auto_schema(
    
        manual_parameters=[
            openapi.Parameter(
                name="parent_type",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Parent type ID to filter by",
                required=False,
            ),
        ],
        consumes=["multipart/form-data"],
        responses={201: serializer.PetSwaggerSerializer},
    )
    @action(detail=False, methods=['GET'], url_path='config-by-type/(?P<config_type>[^/.]+)', serializer_class=serializer.TypeOfConfigSerializer)
    def get_config_by_type(self, request, config_type):
        parent_type = request.query_params.get('parent_type', None)
        configs = typeOfConfig.objects.filter(type=config_type)
        if parent_type:
            configs = configs.filter(parent_type__id=parent_type)
        data = self.get_serializer(configs, many=True).data
        return Response(data=data, status=status.HTTP_200_OK)
    
class PetViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    queryset = Pet.objects.all()
    serializer_class = serializer.PetSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]


    @swagger_auto_schema(
        operation_description="Create pet with multiple images",
        request_body=serializer.PetSwaggerSerializer,
        manual_parameters=[
            openapi.Parameter(
                name="uploaded_images",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description="Upload pet images (multiple allowed)",
                required=False,
            ),
        ],
        consumes=["multipart/form-data"],
        responses={201: serializer.PetSwaggerSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer_loc = self.get_serializer(data=request.data)
        serializer_loc.is_valid(raise_exception=True)
        pet = serializer_loc.save(owner=request.user)

        images = request.FILES.getlist("uploaded_images")
        PetImage.objects.bulk_create([
            PetImage(pet=pet, image=image)
            for image in images
        ])

        return Response(
            serializer.PetSerializer(pet).data,
            status=status.HTTP_201_CREATED
        )


    @action(detail=True, methods=['get'], url_path='detail', serializer_class=serializer.PetDetailSerializer)
    def get_pet_detail(self, request, pk):
        pet = get_object_or_404(Pet, pk=pk)
        data = self.get_serializer(pet).data
        return Response(data=data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='by-owner', serializer_class=serializer.PetListSerializer)
    def get_pets_by_owner(self, request):
        pets = Pet.objects.filter(owner=request.user).select_related('owner', 'breed')
        data = self.get_serializer(pets, many=True).data
        return Response(data=data, status=status.HTTP_200_OK)
    

def get_and_authenticate_user(email, password):
    user = authenticate(username=email, password=password)
    if user is None:
        raise serializers.ValidationError("Invalid username/password. Please try again!")
    return user


class PetImagesViewSet(viewsets.GenericViewSet, mixins.DestroyModelMixin,  mixins.CreateModelMixin):
    queryset = PetImage.objects.all()
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = serializer.PetImageSerializer
    permission_classes = [IsAuthenticated]

class AuthViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = serializer.EmptySerializer


    @action(detail=False, methods=['GET'], url_path='validate-user', serializer_class=serializer.EmptySerializer)
    def get_user_from_token(self, request):
        user = request.user
        if user.is_authenticated:
            data = serializer.UserSerializer(user).data
            return Response(data=data, status=status.HTTP_200_OK)
        else:
            return Response(data={'user': None}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['POST', ],url_path='login',  serializer_class=serializer.LoginSerializer)
    def login(self, request):
        user = get_and_authenticate_user(email=request.data['email'], password=request.data['password'])
        user.last_login = timezone.now()
        user.save()
        data = serializer.LoginResponseUserSerializer(user).data  
        token, created = Token.objects.get_or_create(user=user)
        return Response(data={'user': data, 'token': token.key}, status=status.HTTP_200_OK)
    



class PaypalPaymentView(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.DestroyModelMixin, mixins.RetrieveModelMixin):
    """
    endpoint for create payment url
    """
    queryset = PayPalPayment.objects.all()
    serializer_class = serializer.PayPalPaymentSerializer
    @action(detail=False, methods=['POST'], url_path='create-link', serializer_class=serializer.CreatePaypalLinkSerializer)
    def create_payment_link(self, request):
        resp=make_paypal_payment(amount=request.data['amount'],description=request.data['description'], currency="USD",return_url="https://ibexbuildersworkhub.netlify.app/payment-success",cancel_url="https://ibexbuildersworkhub.netlify.app/payment-cancel")

        PayPalPayment.objects.create(
            amount = request.data['amount'],
            created_by = request.user,
            client = request.data.get('client', None),
            response = resp,
            PayementId = resp['id'],
            type  ='PayPal',
            description = request.data['description'],
            checkoutLink = resp['links'][1]['href']
            )
        if status:
            # handel_subscribtion_paypal(plan=plan,user_id=request.user,payment_id=payment_id)
            return Response({"success":True,"msg":"payment link has been successfully created","resp": resp},status=201)
        else:
            return Response({"success":False,"msg":"Authentication or payment failed"},status=400)
        
    
    @action(detail=False, methods=['GET'], url_path='payments', serializer_class=serializer.CreatePaypalLinkSerializer)
    def get_all_payments(self, request):

        payments = get_all_paypal_payments()
        return Response(data=payments,status=201)

    
    @action(detail=False, methods=['GET'], url_path='payment/(?P<payId>[^/.]+)', serializer_class=serializer.CreatePaypalLinkSerializer)
    def get_payment_by_id(self, request, payId):

        payment=get_paypal_payment_by_id(payment_id=payId)
                
        return Response(data=payment,status=201)
    

    @action(detail=False, methods=['GET'], url_path='execute-payment/(?P<payId>[^/.]+)', serializer_class=serializer.CreatePaypalLinkSerializer)
    def execute_payment(self, request, payId):

        payment=get_paypal_payment_by_id(payment_id=payId)
        payer  = payment.get('payer', None)
        if payer:
            execute_paypal_payment(payment_id=payment['id'], payer_id= payment['payer']['payer_info']['payer_id'])
            payment=get_paypal_payment_by_id(payment_id=payId)
            PayPalPayment.objects.filter(PayementId = payId).update(response = payment, status = 'approved')
        else:
            return Response(data='payment is not approved yet',status=400)
        
        return Response(data=payment,status=201)
    


    @action(detail=False, methods=['GET'], url_path='success/(?P<payId>[^/.]+)', serializer_class=serializer.CreatePaypalLinkSerializer)
    def success_payment(self, request, payId):

        payment=get_paypal_payment_by_id(payment_id=payId)
        payer  = payment.get('payer', None)
        if payer:
            PayPalPayment.objects.filter(
                Q(PayementId=payId) & (Q(status='created') | Q(status='cancel'))
            ).update(response=payment, status='success')
        else:
            return Response(data='payer not pay the amount yet',status=400)
        
        return Response(data=payment,status=201)
    

    @action(detail=False, methods=['GET'], url_path='cancel/(?P<payId>[^/.]+)', serializer_class=serializer.CreatePaypalLinkSerializer)
    def cancel_payment(self, request, payId):

        payment=get_paypal_payment_by_id(payment_id=payId)
        PayPalPayment.objects.filter(PayementId = payId, status = 'created').update(response = payment, status = 'cancel')        
        return Response(data=payment,status=201)


    @action(detail=False, methods=['POST'], url_path='webhook',)
    def payment_webhook(self, request):

        payload = json.loads(request.body.decode('utf-8'))

        # Check the event type (e.g., payment sale completed)
        event_type = payload.get('event_type')

        # if event_type == 'PAYMENT.SALE.COMPLETED':
            # Extract payment ID and other relevant data
        resource = payload.get('resource')
        payment_id = resource.get('parent_payment')  # Get the payment ID
        status = resource.get('state')  # Check if it's 'completed'
        payment_record = PayPalPayment.objects.get(PayementId=payment_id)
        payment_record.status = status  # Update the status to completed
        payment_record.response = resource  # Store the entire resource as the response
        payment_record.save()
        
        return Response(data='payment status updated',status=201)
    
    @action(detail=False, methods=['POST'], url_path='stripe-webhook')
    def stripe_webhook(self, request):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        event = None

        # if sig_header:
        #     # Verify the signature header exists
        #     try:
        #         event = stripe.Webhook.construct_event(
        #             payload, sig_header, endpoint_secret
        #         )
        #     except ValueError:
        #         # Invalid payload
        #         return Response(data='Invalid payload', status=400)
        #     except Exception as e:
        #         # Invalid signature
        #         return Response(data=f'Signature verification failed {str(e)} ', status=400)
        # else:
        #     # Skip signature verification for testing purposes
        #     print("No signature header found, skipping signature verification.")
        try:
            event = stripe.Event.construct_from(
                json.loads(payload), stripe.api_key
            )
        except Exception:
            return Response(data='Invalid payload', status=400)

        # Process the event based on the type
        payment_status = None

        if event['type'] == 'payment_intent.succeeded':
            payment_status = 'succeeded'
        elif event['type'] == 'payment_intent.payment_failed':
            payment_status = 'failed'
        elif event['type'] == 'payment_intent.canceled':
            payment_status = 'canceled'
        elif event['type'] == 'payment_intent.processing':
            payment_status = 'processing'
        elif event['type'] == 'payment_intent.requires_action':
            payment_status = 'requires_action'
        elif event['type'] == 'payment_intent.created':
            payment_status = 'created'
        else:
            payment_status = 'unknown'  # For other unhandled event types
        print("event", event)
        # Extract payment details
        payment_intent = event['data']['object']
        payment_id = payment_intent['id']  # Extract the payment intent ID
        checkout_sessions = stripe.checkout.Session.list(payment_intent=payment_id)
       
        # Update the PayPalPayment object with the received status
        # Ensure PayPalPayment model has the necessary fields (PayementId, response, status)
        checkout_session_id = '123'
        if checkout_sessions.data:
            checkout_session = checkout_sessions.data[0]  # Get the first session
            checkout_session_id = checkout_session.id
            print("Checkout Session ID:", checkout_session_id)
        rows = PayPalPayment.objects.filter(PayementId=checkout_session_id).update(
            response=payment_intent,  # You can serialize this to a JSONField
            status=payment_status
        )
        print("Updated rows:", rows)

        return Response(data=f'{checkout_session_id} Payment status updated: {payment_status}, rows updated {rows}', status=201)
   
    @action(detail=False, methods=['POST'], url_path='stripe-session', serializer_class= serializer.CreatePaypalLinkSerializer)
    def create_stripe_session(self, request):

        domain_url = 'https://ibexbuildersworkhub.netlify.app/'
        stripe.api_key = settings.STRIPE_SECRET_KEY
        client = request.data.get('client', None)
        clientQuery = None

        # Fetch the User object based on client id, if provided
        if client:
            clientQuery = User.objects.get(id=client)

        try:
            original_amount = float(request.data['amount'])

            # Stripe fee calculations (example: 2.9% + $0.30)
            stripe_fee_percentage = 0.029  
            stripe_fixed_fee = 0.30  
            # $0.30 fixed fee
            # 2.9% for card payments

            # Calculate total amount including fees
            total_amount = original_amount + (original_amount * stripe_fee_percentage) + stripe_fixed_fee

            # Convert to cents
            unit_amount = int(original_amount * 100)

            # Create the Stripe checkout session with the modified amount
            checkout_session = stripe.checkout.Session.create(
                success_url=domain_url + 'payment-success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'payment-cancel/',
                payment_method_types=['card', 'us_bank_account'],
                customer_email=clientQuery.email if clientQuery else None,
                mode='payment',


                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': request.data['description'],
                            },
                            'unit_amount': unit_amount,  
                        },
                        'quantity': 1,
                    }
                ]
            )

            # Create PayPalPayment object, assigning clientQuery (the User instance)
            createdObject = PayPalPayment.objects.create(
                amount=request.data['amount'],
                created_by=request.user,
                client=clientQuery,  # Pass the User instance here
                response=checkout_session,
                PayementId=checkout_session['id'],
                type='Stripe',
                description = request.data['description'],
                checkoutLink = checkout_session['url']
            )

            print(checkout_session)
            return Response({'session': checkout_session, 'url': checkout_session['url']})
        except Exception as e:
            return Response({'error': str(e)})


    @action(detail=False, methods=['POST'], url_path='stripe-session-new', serializer_class= serializer.CreatePaypalLinkNewSerializer)
    def create_stripe_session_new(self, request):

        domain_url = 'https://ibexbuildersworkhub.netlify.app/'
        stripe.api_key = settings.STRIPE_SECRET_KEY
        client = request.data.get('client', None)
        itemsList = request.data.get('itemsList', [])
        enableTax = request.data.get('enableTax', False)
        payment_method = request.data.get('payment_method', 'card')  # Default to card if not specified

        clientQuery = None

        if isinstance(itemsList, str):
            try:
                itemsList = json.loads(itemsList)  # Convert the string into JSON
            except json.JSONDecodeError:
                itemsList = [] 

        # Fetch the User object based on client id, if provided
        if client:
            clientQuery = User.objects.get(id=client)

        try:
            lineItems = []
            total_amount = 0
            for item in itemsList:
                print("insode list", item)
                total_amount += item['amount'] * item['quantity']
                lineItems.append(
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': item['title'],
                            },
                            'unit_amount': int(item['amount'] * 100),  # Amount in cents with fees included
                        },
                        'quantity': item['quantity'],
                    }
                )

            fee = 0

            if payment_method == 'card':
                # Card fees: 2.9% + 30 cents
                fee = (total_amount * 0.029) + 0.30
            elif payment_method == 'us_bank_account':
                # ACH fees: 0.8%, capped at $5
                fee = min(total_amount * 0.008, 5)

            # Convert fee to cents and round up
            fee_in_cents = math.ceil(fee * 100)

            # Add the fee as a separate line item


            # if request.data.get('description'):
            #     lineItems.insert(0, {
            #         'price_data': {
            #             'currency': 'usd',
            #             'product_data': {
            #                 'name': request.data['description'],  # This will be shown at the top
            #             },
            #             'unit_amount': 0,  # No charge for this item
            #         },
            #         'quantity': 1,
            #     })
            formatted_payment_method = payment_method.replace('_', ' ').title()

            if fee_in_cents > 0:
                lineItems.append(
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f'{formatted_payment_method} Transaction Fee',
                            },
                            'unit_amount': fee_in_cents,
                        },
                        'quantity': 1,
                    }
                )

            # Create the Stripe checkout session with the modified amount
            checkout_session = stripe.checkout.Session.create(
                customer_creation="always",
                success_url=domain_url + 'payment-success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'payment-cancel/',
                payment_method_types= [payment_method] if fee else  ['card','us_bank_account'],
            
                customer_email=clientQuery.email if clientQuery else None,
                mode='payment',
                automatic_tax={'enabled': enableTax},
                line_items=lineItems,
                payment_intent_data={"setup_future_usage": "off_session",  "description": request.data.get('description', None)},
                
            )

            # Create PayPalPayment object, assigning clientQuery (the User instance)
            createdObject = PayPalPayment.objects.create(
                amount= total_amount,
                created_by=request.user,
                client=clientQuery,  # Pass the User instance here
                response=checkout_session,
                PayementId=checkout_session['id'],
                type='Stripe',
                description = request.data.get('description', None),
                checkoutLink = checkout_session['url'],
                itemsList = itemsList,
                enableTax = enableTax
            )

            print(checkout_session)
            return Response({'session': checkout_session, 'url': checkout_session['url']})
        except Exception as e:
            return Response({'error': str(e)})

    



    
    

    # @action(detail=False, methods=['GET'], url_path='payment/(?P<payId>[^/.]+)', serializer_class=serializer.CreatePaypalLinkSerializer)
    # def get_payment_by_id(self, request, payId):

    #     payment=get_paypal_payment_by_id(payment_id=payId)
    #     return Response(data=payment,status=201)
       






class PaypalValidatePaymentView(APIView):
    """
    endpoint for validate payment 
    """
    # permission_classes=[IsAuthenticated,]

    def post(self, request, *args, **kwargs):
        # payment_id=request.data.get("payment_id")
        payment_id= 'PAYID-M3AGIAA4AL50455CR637712P'
        payment_status=get_paypal_payment_by_id(payment_id=payment_id)
        if payment_status:
            # your business logic 
             
            return Response({"success":True,"msg":"payment improved"},status=200)
        else:
            return Response({"success":False,"msg":"payment failed or cancelled"},status=200)
    