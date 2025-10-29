"""Debug script to see what data is being sent to Airtable"""
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path to import from sync script
sys.path.insert(0, os.path.dirname(__file__))

from sync_zoho_to_airtable import ZohoCRMClient, convert_zoho_to_airtable
import json

load_dotenv()

# Initialize Zoho client
zoho_client = ZohoCRMClient()

# Fetch one lead
print("Fetching Leads from Zoho...")
leads = zoho_client.get_all_records('Leads')

if leads:
    print(f"\nFound {len(leads)} leads")
    print("\n" + "="*60)
    print("FIRST LEAD - RAW DATA FROM ZOHO:")
    print("="*60)
    print(json.dumps(leads[0], indent=2, default=str))
    
    print("\n" + "="*60)
    print("CONVERTED DATA FOR AIRTABLE:")
    print("="*60)
    converted = convert_zoho_to_airtable([leads[0]])
    print(json.dumps(converted[0], indent=2, default=str))
    
    print("\n" + "="*60)
    print("FIELD NAMES AND VALUES:")
    print("="*60)
    if converted and 'fields' in converted[0]:
        for key, value in converted[0]['fields'].items():
            print(f"  {key}: {value} (type: {type(value).__name__})")
    else:
        print("  No fields found!")
else:
    print("No leads found")
