"""Test script to debug Zoho API call"""
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
print("Getting access token...")
token_response = requests.post(
    f'https://accounts.zoho.{ZOHO_REGION}/oauth/v2/token',
    params={
        'refresh_token': ZOHO_REFRESH_TOKEN,
        'client_id': ZOHO_CLIENT_ID,
        'client_secret': ZOHO_CLIENT_SECRET,
        'grant_type': 'refresh_token'
    }
)
token_data = token_response.json()
access_token = token_data['access_token']
print(f"Access token: {access_token[:20]}...")
print(f"Scope: {token_data.get('scope', 'N/A')}")

headers = {
    'Authorization': f'Zoho-oauthtoken {access_token}'
}

# Test different fields parameters
test_params = [
    {'page': 1, 'per_page': 1},
    {'page': 1, 'per_page': 1, 'fields': 'All'},
    {'page': 1, 'per_page': 1, 'fields': 'all'},
]

for i, params in enumerate(test_params, 1):
    print(f"\n{'='*60}")
    print(f"Test {i}: Params = {params}")
    print(f"{'='*60}")
    
    url = f'https://www.zohoapis.{ZOHO_REGION}/crm/v3/Leads'
    response = requests.get(url, headers=headers, params=params)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if data.get('data'):
            print(f"Number of records: {len(data['data'])}")
            print(f"\nFirst record:")
            print(json.dumps(data['data'][0], indent=2))
            print(f"\nNumber of fields in first record: {len(data['data'][0])}")
    else:
        print(f"Error: {response.text}")
