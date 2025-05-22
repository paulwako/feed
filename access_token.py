import os
import base64
import requests
from fastapi import HTTPException

# function to get access token
def get_access_token():
    try:
        consumer_key = os.environ.get('MPESA_CONSUMER_KEY')
        consumer_secret = os.environ.get('MPESA_CONSUMER_SECRET')
        
        if not consumer_key or not consumer_secret:
            print("Error: M-Pesa credentials not found in environment variables")
            raise HTTPException(status_code=500, detail="M-Pesa credentials not configured properly")
        
        url = "https://api.safaricom.co.ke/oauth/v2/generate?grant_type=client_credentials"
        payload = f"{consumer_key}:{consumer_secret}"
        encoded = base64.b64encode(payload.encode()).decode()

        response = requests.request("GET", url, headers = { 'Authorization': 'Basic {}'.format(encoded)})
        print(response.text.encode('utf8'))
        
        
        print(f"Response status code: {response.status_code}")
        print(f"Response body: {response.text[:100]}...") 
        
        # Check for errors
        response.raise_for_status()
        
        # Parse and return the access token
        data = response.json()
        if 'access_token' in data:
            print("Successfully retrieved access token")
            return data['access_token']
        else:
            print(f"No access token in response. Full response: {data}")
            raise HTTPException(status_code=500, detail="Invalid response format from Mpesa API")
        
    except requests.exceptions.RequestException as e:
        print(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to authenticate with Mpesa API: {str(e)}")
    except KeyError as e:
        print(f"Key error in response: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected response format from Mpesa API")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")