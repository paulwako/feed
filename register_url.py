from fastapi import HTTPException
import os
import requests
import json
from access_token import get_access_token


def register_confirmation_url():
    try:
        # Get the access token
        token = get_access_token()
        
        # Set up headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Get necessary credentials
        shortcode = os.environ.get('MPESA_SHORTCODE')
        passkey = os.environ.get('MPESA_PASSKEY')
        
        # remove any trailing semicolons or commas
        confirmation_url = os.environ.get('CONFIRMATION_URL')
        if confirmation_url and (confirmation_url.endswith(';') or confirmation_url.endswith(',')):
            confirmation_url = confirmation_url.rstrip(';,')
            
        validation_url = os.environ.get('VALIDATION_URL')
        if validation_url and (validation_url.endswith(';') or validation_url.endswith(',')):
            validation_url = validation_url.rstrip(';,')
            
        
        # Validate required parameters
        if not shortcode or not confirmation_url or not validation_url:
            print("Error: M-Pesa shortcode, confirmation URL, or validation URL not found in environment variables")
            raise HTTPException(status_code=500, detail="M-Pesa configuration not complete")
    
        
        # Prepare the request payload 
        data = {
            "ShortCode": shortcode,
            "ResponseType": "Completed",
            "ConfirmationURL": confirmation_url,
            "ValidationURL": validation_url
        }
        
        # Production URL for C2B URL registration
        register_url = "https://api.safaricom.co.ke/mpesa/c2b/v2/registerurl"
        
        # Make the API request
        response = requests.post(
            register_url,
            json=data,
            headers=headers
        )
        
        print(f"Register URL response status: {response.status_code}")
        print(f"Register URL response: {response.text}")
        
        # Handle unsuccessful responses without raising exception immediately
        if response.status_code != 200:
            print(f"URL registration failed with status {response.status_code}")
            print(f"Response content: {response.text}")
            
            # Check for the specific "URLs already registered" error
            try:
                response_data = response.json()
                if (response.status_code == 500 and 
                    response_data.get("errorCode") == "500.003.1001" and 
                    "URLs are already registered" in response_data.get("errorMessage", "")):
                    
                    print("URLs are already registered - this is not an error, continuing...")
                    return {
                        "status": "success", 
                        "message": "URLs are already registered",
                        "responseData": response_data
                    }
            except (ValueError, json.JSONDecodeError):
                pass
                
            # If token issue, try to re-authenticate and try again
            if response.status_code == 401:
                print("Authentication error - trying again with fresh token")
                
                new_token = get_access_token()
                # Update the header
                headers["Authorization"] = f"Bearer {new_token}"
                
                # Make the second attempt
                retry_response = requests.post(
                    register_url,
                    json=data,
                    headers=headers
                )
                
                print(f"Retry response status: {retry_response.status_code}")
                print(f"Retry response: {retry_response.text}")
                
                if retry_response.status_code == 200:
                    return retry_response.json()
                else:
                    try:
                        retry_data = retry_response.json()
                        if (retry_response.status_code == 500 and 
                            retry_data.get("errorCode") == "500.003.1001" and 
                            "URLs are already registered" in retry_data.get("errorMessage", "")):
                            
                            print("URLs are already registered - this is not an error, continuing...")
                            return {
                                "status": "success", 
                                "message": "URLs are already registered",
                                "responseData": retry_data
                            }
                    except (ValueError, json.JSONDecodeError):
                        pass
                    
                    retry_response.raise_for_status()
            else:
                response.raise_for_status()
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Failed to register confirmation URL: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"Error response: {e.response.text}")
            try:
                error_data = json.loads(e.response.text)
                if (e.response.status_code == 500 and 
                    error_data.get("errorCode") == "500.003.1001" and 
                    "URLs are already registered" in error_data.get("errorMessage", "")):
                    
                    print("URLs are already registered - this is not an error")
                    return {
                        "status": "success", 
                        "message": "URLs are already registered",
                        "responseData": error_data
                    }
            except (ValueError, json.JSONDecodeError):
                pass
                
        raise HTTPException(status_code=500, detail=f"Failed to register confirmation URL: {str(e)}")
    
    except json.JSONDecodeError as e:
        print(f"Failed to parse response: {str(e)}")
        raise HTTPException(status_code=500, detail="Invalid response from Safaricom API")
    
    except Exception as e:
        print(f"Unexpected error during URL registration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")