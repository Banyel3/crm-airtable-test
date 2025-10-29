"""Test fetching with specific field names"""
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

ZOHO_CLIENT_ID = os.getenv('CRM_CLIENTID')
ZOHO_CLIENT_SECRET = os.getenv('CRM_CLIENTSECRET')
ZOHO_REFRESH_TOKEN = os.getenv('CRM_REFRESH_TOKEN')
ZOHO_REGION = os.getenv('ZOHO_REGION', 'com')

# Get access token
token_response = requests.post(
    f'https://accounts.zoho.{ZOHO_REGION}/oauth/v2/token',
    params={
        'refresh_token': ZOHO_REFRESH_TOKEN,
        'client_id': ZOHO_CLIENT_ID,
        'client_secret': ZOHO_CLIENT_SECRET,
        'grant_type': 'refresh_token'
    }
)
access_token = token_response.json()['access_token']

headers = {'Authorization': f'Zoho-oauthtoken {access_token}'}

# Get the specific lead record with all details
print("Fetching full lead details...")
lead_id = "7063399000000594201"
url = f'https://www.zohoapis.{ZOHO_REGION}/crm/v3/Leads/{lead_id}'

response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("\nFull Lead Record:")
    print(json.dumps(data, indent=2))
else:
    print(f"Error: {response.text}")
