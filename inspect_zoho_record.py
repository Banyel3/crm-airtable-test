"""
Script to inspect a single Zoho record and see all its fields and relationships
"""
import os
import json
from dotenv import load_dotenv
from sync_zoho_to_airtable import ZohoCRMClient

load_dotenv()

# Initialize client
zoho_client = ZohoCRMClient()

# Fetch one record from Accounts
print("Fetching a sample Account record from Zoho CRM...")
records, info = zoho_client.get_records('Accounts', page=1, per_page=1)

if records and len(records) > 0:
    record = records[0]
    
    print("\n" + "="*80)
    print("FULL ZOHO RECORD STRUCTURE")
    print("="*80)
    print(json.dumps(record, indent=2, default=str))
    
    print("\n" + "="*80)
    print("FIELD ANALYSIS")
    print("="*80)
    
    for key, value in record.items():
        value_type = type(value).__name__
        
        if isinstance(value, dict):
            print(f"\n{key}: {value_type}")
            print(f"  Keys: {list(value.keys())}")
            if 'id' in value and 'name' in value:
                print(f"  ** RELATIONSHIP DETECTED: {value.get('name')} (ID: {value.get('id')})")
        elif isinstance(value, list):
            print(f"\n{key}: {value_type} (length: {len(value)})")
            if value and isinstance(value[0], dict):
                print(f"  First item keys: {list(value[0].keys())}")
                print(f"  ** RELATIONSHIP LIST DETECTED")
        else:
            # Show value preview
            value_preview = str(value)[:100]
            print(f"\n{key}: {value_type} = {value_preview}")
    
    print("\n" + "="*80)
    print("SYSTEM FIELDS (starting with $)")
    print("="*80)
    system_fields = {k: v for k, v in record.items() if k.startswith('$')}
    for key, value in system_fields.items():
        print(f"  {key}: {type(value).__name__}")
    
    print("\n" + "="*80)
    print("LOOKUP/RELATIONSHIP FIELDS (dict with id/name)")
    print("="*80)
    relationship_fields = {k: v for k, v in record.items() 
                          if isinstance(v, dict) and 'id' in v and 'name' in v}
    for key, value in relationship_fields.items():
        print(f"  {key}: {value.get('name')} (Module: {value.get('module', 'Unknown')})")
    
else:
    print("No records found in Accounts")
