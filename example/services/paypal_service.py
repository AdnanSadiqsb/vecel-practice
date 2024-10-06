import requests
import json
# from decouple import config
from django.conf import settings
base_url =settings.PAYPAL_BASE_URL
def make_paypal_payment(amount, description, currency, return_url, cancel_url):

    payment_url = base_url + '/v1/payments/payment'
    access_token = get_paypal_access_token()

    # Create payment payload
    payment_payload = {
        'intent': 'sale',
        'payer': {'payment_method': 'paypal'},
        'transactions': [{
            'amount': {'total': str(amount), 'currency': currency},
            'description': description
        }],
        'redirect_urls': {
            'return_url': return_url,
            'cancel_url': cancel_url
        }
    }

    # Create payment request
    payment_headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    payment_response = requests.post(payment_url, data=json.dumps(payment_payload), headers=payment_headers)
    print(payment_response.text)
    if payment_response.status_code != 201:
        raise Exception('something went wrong while creating link')

    return payment_response.json()

def get_all_paypal_payments():

    access_token = get_paypal_access_token()
    headers = {
    'Authorization':  f'Bearer {access_token}',
    }
    payment_url = base_url + '/v1/payments/payment'
    params = (
        ('count', '10'),
        ('start_index', '0'),
        ('sort_by', 'create_time'),
        ('sort_order', 'desc'),
    )


    response = requests.get(payment_url, headers=headers)

    print(response.text)
    if response.status_code != 200:
        raise Exception('Error while getting all payments.')
    return response.json()


def get_paypal_access_token():
    client_id = settings.PAYPAL_ID
    secret = settings.PAYPAL_SECRET
    

    token_url = base_url + '/v1/oauth2/token'
    token_payload = {'grant_type': 'client_credentials'}
    token_headers = {'Accept': 'application/json', 'Accept-Language': 'en_US'}
    token_response = requests.post(token_url, auth=(client_id, secret), data=token_payload, headers=token_headers)

    if token_response.status_code != 200:
        raise Exception('Failed to authenticate with PayPal API.')

    access_token = token_response.json()['access_token']
    print("access token", access_token)
    return access_token


def get_paypal_payment_by_id(payment_id):

    payment_url = base_url + '/v1/payments/payment'
    # Request an access token
    access_token = get_paypal_access_token()
    # Retrieve payment details
    payment_headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    payment_details_url = f'{payment_url}/{payment_id}'
    payment_details_response = requests.get(payment_details_url, headers=payment_headers)
    if payment_details_response.status_code != 200:
        raise Exception('Failed to retrieve PayPal payment details.')

    return payment_details_response.json()
    # if payment_status == 'approved':
        # Payment is successful, process the order
        # Retrieve additional payment details if needed
        # payer_email = payment_details_response.json()['payer']['payer_info']['email']
        # ... process the order ...
        # return True
    # else:
        # Payment failed or was canceled
        # return False




def execute_paypal_payment(payment_id, payer_id):
    payment_execute_url = f'{base_url}/v1/payments/payment/{payment_id}/execute'
    
    # Access token retrieved earlier
    access_token = get_paypal_access_token()
    
    # Prepare headers
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    # Prepare body for the execute request
    execute_payload = {
        "payer_id": payer_id
    }
    
    # Execute payment
    response = requests.post(payment_execute_url, headers=headers, json=execute_payload)
    
    if response.status_code != 200:
        raise Exception(f"Payment execution failed: {response.text}")
    
    return response.json()