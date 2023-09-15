from flask import Blueprint, request, jsonify, g
import paypalrestsdk
import os
import requests

paypal_bp = Blueprint('paypal', __name__)

paypalrestsdk.configure({
    "mode": "sandbox",  # sandbox or live
    "client_id": os.environ['CLIENT_ID'],
    "client_secret": os.environ['CLIENT_SECRET']})


def get_access_token():
    client_id = os.environ['CLIENT_ID']
    client_secret = os.environ['CLIENT_SECRET']

    token_url = 'https://api-m.sandbox.paypal.com/v1/oauth2/token'  # PayPal OAuth token endpoint (sandbox)

    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'en_US',
    }

    data = {
        'grant_type': 'client_credentials',
    }

    response = requests.post(token_url, headers=headers, auth=(client_id, client_secret), data=data)

    if response.status_code == 200:
        return response.json()['access_token']
    else:
        return None
    

@paypal_bp.post('/payment')
def payment():
    try:
        data = request.json
    except:
        return jsonify({"error":"Please Enter Valid Json Formant"}),400
    if not data.get("payer_name"):
        return jsonify({"error":"Please Enter Payer Name"}),400
    if not data.get("sku"):
        return jsonify({"error":"Please Enter sku"}),400
    if not data.get("price"):
        return jsonify({"error":"Please Enter Price"}),400
    if not data.get("currency"):
        return jsonify({"error":"Please Enter Currency"}),400
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"},
        "redirect_urls": {
            "return_url": "http://localhost:3000/v1/paypal/payment/execute",  # Change this URL
            "cancel_url": "http://localhost:3000/v1/paypal/payment"},
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": data.get("payer_name"),
                    "sku": data.get("sku"),
                    "price": data.get("price"),
                    "currency": data.get("currency"),
                    "quantity": 1}]},
            "amount": {
                "total": data.get("price"),
                "currency": data.get("currency")},
            "description": "This is the payment transaction description."}]})

    if payment.create():
        for link in payment.links:
            if link.method == "REDIRECT":
                approval_url = link.href
                # print('Payment approval URL:', approval_url)
                return jsonify({"approval_url": approval_url})
    else:
        print(payment.error)

    return jsonify({'error': 'Failed to create payment'})


@paypal_bp.post('/payment/execute')
def execute():
    success = False
    payment_id = request.args.get('paymentId')
    payer_id = request.args.get('PayerID')
    try:
        if payment_id and payer_id:
            payment = paypalrestsdk.Payment.find(payment_id)
            

            if payment.execute({'payer_id': payer_id}):
                transaction_id = payment.id
                tracking_info = {
                    'shipping_status': 'shipped',
                    'tracking_number': '123456789',
                    'estimated_delivery_date': '2023-08-31'
                }
                
                # Call the add_tracking_info endpoint to associate the tracking_info with the transaction
                response = requests.post('http://localhost:3000/payment/track', json={
                    'transaction_id': transaction_id,
                    'tracking_info': tracking_info
                })
                print(response.text)
                return jsonify({'success': True, 'transaction_id': transaction_id})
            else:
                return jsonify({'success': False, 'message': 'Payment execution failed'})

    except paypalrestsdk.exceptions.ResourceNotFound:
        return jsonify({'success': False, 'message': 'Payment not found'})


@paypal_bp.post('/payment/track')
def add_tracking_info():
    # Replace with your PayPal API credentials
    client_id = os.environ['CLIENT_ID']
    client_secret = os.environ['CLIENT_SECRET']
    
    # PayPal API endpoint
    endpoint = 'https://api-m.paypal.com/v1/shipping/trackers-batch'
    
    # Example tracking data in JSON format
    tracking_data = request.json
    
    # Set up headers
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {(client_id, client_secret)}'
    }
    
    # Make the API request
    response = requests.post(endpoint, json=tracking_data, headers=headers)
    
    if response.status_code == 201:
        return jsonify({'message': 'Tracking information added successfully.'}), 201
    else:
        return jsonify({'error': 'Failed to add tracking information.'})
    
@paypal_bp.post('/create-product')
def create_product():
    try:
        access_token = get_access_token()
        try:
            data = request.json
        except:
            return jsonify({"error":"Please Enter Valid Json Formant"}),400
        if not data.get("name"):
            return jsonify({"error":"Please Enter Name"}),400
        if not data.get("description"):
            return jsonify({"error":"Please Enter Description"}),400
        if not data.get("type"):
            return jsonify({"error":"Please Enter Type"}),400
        if not data.get("category"):
            return jsonify({"error":"Please Enter Category"}),400
        if not data.get("image_url"):
            return jsonify({"error":"Please Enter Image Url"}),400
        if not data.get("home_url"):
            return jsonify({"error":"Please Enter Home Url"}),400

        if access_token is None:
            return jsonify({'error': 'Failed to obtain access token'}), 500
        # Extract the JSON data from the request
        product_data = {
            "name": data.get("name"),
            "description": data.get("description"),
            "type": data.get("type"),
            "category": data.get("category"),
            "image_url": data.get("image_url"),
            "home_url": data.get("home_url")
        }
        # print("---------------------->",product_data)

        # PayPal API endpoint
        paypal_api_url = 'https://api-m.sandbox.paypal.com/v1/catalogs/products'

        # PayPal API headers
        headers = {
            'Authorization': f'Bearer {access_token}',
            # 'X-PAYPAL-SECURITY-CONTEXT': '{"consumer":{"accountNumber":1181198218909172527,"merchantId":"5KW8F2FXKX5HA"},"merchant":{"accountNumber":1659371090107732880,"merchantId":"2J6QB8YJQSJRJ"},"apiCaller":{"clientId":"AdtlNBDhgmQWi2xk6edqJVKklPFyDWxtyKuXuyVT-OgdnnKpAVsbKHgvqHHP","appId":"APP-6DV794347V142302B","payerId":"2J6QB8YJQSJRJ","accountNumber":"1659371090107732880"},"scopes":["https://api-m.paypal.com/v1/subscription/.*","https://uri.paypal.com/services/subscription","openid"]}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'PayPal-Request-Id': data.get("PayPal-Request-Id"),
            'Prefer': 'return=representation',
        }

        # Make the POST request to PayPal API
        response = requests.post(paypal_api_url, headers=headers, json=product_data)

        # Return the response from PayPal API as JSON
        return jsonify(response.json())

    except Exception as e:
        return jsonify({'error': str(e)})
    
@paypal_bp.post('/update-product/<product_id>')
def update_product(product_id):
    # try:
        # Obtain the access token
        access_token = get_access_token()

        if access_token is None:
            return jsonify({'error': 'Failed to obtain access token'}), 500

        # PayPal API headers
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json', 
            'Prefer': 'return=representation',
        }
        data_get = request.json
        
        if not data_get.get("path"):
            return jsonify({'error':"Please Enter Path"})
        if not data_get.get("value"):
            return jsonify({'error':"Please Enter Value"})
        # Request data for updating the description
        data = [
            {
                "op": "replace",
                "path": data_get.get("path"),
                "value": data_get.get("value")
            }
        ]

        # PayPal API endpoint for updating a product
        paypal_api_url = f'https://api-m.sandbox.paypal.com/v1/catalogs/products/{product_id}'

        # Make the PATCH request to update the product description
        response = requests.patch(paypal_api_url, headers=headers, data=data)

        if response.status_code == 204:
            return jsonify({'message': 'Product description updated successfully'}), 204
        else:
            return jsonify({'error': 'Failed to update product description', 'details': response.text}), response.status_code

    # except Exception as e:
    #     return jsonify({'error': str(e)})
    


# text = "Hello, world!"

# # Encode the string using UTF-16 encoding
# encoded_bytes = text.encode('utf-16')

# print("Encoded Bytes:", encoded_bytes)

# # Decode the encoded bytes back to a string using UTF-16 encoding
# decoded_text = encoded_bytes.decode('utf-16')

# print("Decoded Text:", decoded_text)
