                """
Quick script to check the Account_Number field definition from Zoho
"""
import os
import sys
from dotenv import load_dotenv

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Import the ZohoCRMClient
from sync_zoho_to_airtable import ZohoCRMClient, AirtableClient

load_dotenv()

# Initialize client
zoho_client = ZohoCRMClient()
airtable_client = AirtableClient()

# Get field definitions for Accounts module
print("Fetching Accounts field definitions from Zoho CRM...")
fields = zoho_client.get_module_fields('Accounts')

# Find Account_Number field
for field in fields:
    if field.get('api_name') == 'Account_Number':
        print("\n" + "="*60)
        print("Account_Number field definition:")
        print("="*60)
        print(f"Field Name: {field.get('field_label')}")
        print(f"API Name: {field.get('api_name')}")
        print(f"Data Type: {field.get('data_type')}")
        print(f"JSON Type: {field.get('json_type')}")
        print(f"Required: {field.get('required')}")
        print(f"Read Only: {field.get('read_only')}")
        print(f"Unique: {field.get('unique', {})}")
        print("\nFull field definition:")
        import json
        print(json.dumps(field, indent=2))
        
        # Check what Airtable type it maps to
        print("\n" + "="*60)
        print("Airtable mapping:")
        print("="*60)
        airtable_config = airtable_client.map_zoho_type_to_airtable(field)
        print(json.dumps(airtable_config, indent=2))
        break
else:
    print("\n⚠️  Account_Number field not found in Accounts module")
    print("\nAll fields in Accounts module:")
    for field in fields:
        print(f"  - {field.get('api_name')} ({field.get('data_type')})")
