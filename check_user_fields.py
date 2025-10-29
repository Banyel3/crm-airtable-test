"""
Check what fields are in Zoho Users data
"""
import os
from dotenv import load_dotenv
from sync_zoho_to_airtable import ZohoCRMClient
import json

load_dotenv()

client = ZohoCRMClient()
users = client.get_users()

if users:
    print("Sample User Record:")
    print("="*80)
    print(json.dumps(users[0], indent=2, default=str))
    
    print("\n" + "="*80)
    print("All Fields in User Record:")
    print("="*80)
    for key, value in users[0].items():
        print(f"{key}: {type(value).__name__} = {str(value)[:100]}")
