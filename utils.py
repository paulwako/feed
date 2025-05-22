import httpx
import os
from twilio.rest import Client

# Utility function to parse the payment confirmation message.
def parse_payment_json(data: dict):
    transaction_id = data.TransID
    firstname = data.FirstName
    secondname = data.MiddleName or ""
    lastname = data.LastName or ""
    phone = data.MSISDN
    
    
    return transaction_id, firstname, secondname, lastname, phone

# Function to send WhatsApp message using the WhatsApp Business API.
async def send_whatsapp_message(phone: str, firstname: str):
    try:
            
        url = "https://graph.facebook.com/v16.0/482516058280077/messages"  
        
        token = os.environ.get('WHATSAPP_API_TOKEN')
        if not token:
            print("WHATSAPP_API_TOKEN environment variable not set")
            return
            
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {
                "body": (
                    f"Hi {firstname}, thank you for your payment! "
                    "Could you please rate our service on a scale of 1 to 5? "
                    "Also, let us know if you're comfortable providing additional feedback about our business."
                )
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"Sending WhatsApp message to {phone}")
            response = await client.post(url, headers=headers, json=payload)
            print(f"WhatsApp API response status: {response.status_code}")
            print(f"WhatsApp API response body: {response.text}")
            
            if response.status_code != 200:
                print(f"Failed to send WhatsApp message: {response.text}")
            else:
                print(f"Successfully sent WhatsApp message to {phone}")
                
    except Exception as e:
        print(f"Exception in send_whatsapp_message: {str(e)}")
        



async def send_whatsapp_message_twilio(phone: str, firstname: str):
    try:
        # Get Twilio credentials from environment variables
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        from_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')
        
        # Check if credentials are available
        if not all([account_sid, auth_token, from_number]):
            print("Twilio credentials not set. Please check environment variables.")
            return
        
        # Format the phone number for WhatsApp
        to_number = f"whatsapp:{phone}"
        from_whatsapp = f"whatsapp:{from_number}"
        
        # Prepare message content
        message_body = (
            f"Hi {firstname}, thank you for your payment! "
            "Could you please rate our service on a scale of 1 to 5? "
            "Also, let us know if you're comfortable providing additional feedback about our business."
        )
        
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Send WhatsApp message
        print(f"Sending WhatsApp message to {phone}")
        message = client.messages.create(
            body=message_body,
            from_=from_whatsapp,
            to=to_number
        )
        
        # Print success information
        print(f"Message sent successfully! SID: {message.sid}")
        
    except Exception as e:
        print(f"Exception in send_whatsapp_message: {str(e)}")
        
    return
        