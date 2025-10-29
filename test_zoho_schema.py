"""
Test what fields Zoho returns for a module
"""
import os
import json
from dotenv import load_dotenv
from sync_zoho_to_airtable import ZohoCRMClient

load_dotenv()

client = ZohoCRMClient()

# Get field definitions for Leads
print("Fetching Leads field definitions from Zoho...")
fields = client.get_module_fields('Leads')

print(f"\nFound {len(fields)} fields in Leads module\n")
print("="*80)

# Show a few sample fields with all their properties
for i, field in enumerate(fields[:5], 1):
    print(f"\nField {i}:")
    print(json.dumps(field, indent=2, default=str))
    print("-"*80)

# Show just the key info for all fields
print("\n" + "="*80)
print("ALL FIELDS SUMMARY:")
print("="*80)
for field in fields:
    api_name = field.get('api_name', 'N/A')
    data_type = field.get('data_type', 'N/A')
    field_label = field.get('field_label', 'N/A')
    system_field = field.get('system_mandatory', False)
    print(f"{api_name:30} | {data_type:20} | {field_label:30} | System: {system_field}")
