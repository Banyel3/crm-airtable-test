"""
Debug script to compare Zoho fields with what's being synced to Airtable
"""
import os
import sys
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from sync_zoho_to_airtable import ZohoCRMClient, AirtableClient, convert_zoho_to_airtable

load_dotenv()

# Initialize clients
zoho_client = ZohoCRMClient()
airtable_client = AirtableClient()

print("="*80)
print("ZOHO ACCOUNTS MODULE - FIELD ANALYSIS")
print("="*80)

# Get field definitions from Zoho
print("\n1. Fetching field definitions from Zoho CRM...")
zoho_fields = zoho_client.get_module_fields('Accounts')
print(f"   Found {len(zoho_fields)} fields in Zoho")

# Get actual records
print("\n2. Fetching sample records from Zoho...")
zoho_records = zoho_client.get_all_records('Accounts')[:1]  # Just get first record
if zoho_records:
    print(f"   Fetched {len(zoho_records)} sample record(s)")
    sample_record = zoho_records[0]
    
    print("\n3. Fields in the actual Zoho record:")
    print("-" * 80)
    for key, value in sorted(sample_record.items()):
        value_type = type(value).__name__
        value_preview = str(value)[:60] if value else "None"
        print(f"   {key:30} = {value_preview:40} ({value_type})")
    
    # Build field type map
    print("\n4. Building field type map for Airtable...")
    field_type_map = {}
    for zoho_field in zoho_fields:
        field_name = zoho_field.get('api_name', '').lstrip('$')
        if field_name and field_name != 'id':
            field_type_map[field_name] = airtable_client.map_zoho_type_to_airtable(zoho_field)
    
    print(f"   Created type mappings for {len(field_type_map)} fields")
    
    # Convert to Airtable format
    print("\n5. Converting to Airtable format...")
    airtable_records = convert_zoho_to_airtable(zoho_records, field_type_map)
    
    if airtable_records:
        airtable_fields = airtable_records[0].get('fields', {})
        print(f"   Converted record has {len(airtable_fields)} fields")
        
        print("\n6. Fields that will be sent to Airtable:")
        print("-" * 80)
        for key, value in sorted(airtable_fields.items()):
            value_type = type(value).__name__
            value_preview = str(value)[:60] if value else "None"
            expected_type = field_type_map.get(key, {}).get('type', 'unknown')
            print(f"   {key:30} = {value_preview:40} ({value_type}) -> {expected_type}")
        
        print("\n7. COMPARISON - Fields in Zoho but NOT converted to Airtable:")
        print("-" * 80)
        zoho_keys = set(sample_record.keys())
        airtable_keys = set(airtable_fields.keys())
        
        # Remove $ prefix for comparison
        zoho_keys_clean = {k.lstrip('$') for k in zoho_keys}
        
        missing = zoho_keys_clean - airtable_keys - {'id'}
        if missing:
            for key in sorted(missing):
                original_key = key if key in sample_record else f"${key}"
                value = sample_record.get(original_key, sample_record.get(key))
                print(f"   {key:30} = {str(value)[:60]}")
        else:
            print("   (None - all fields are being converted)")
        
        print("\n8. Sample converted record (JSON):")
        print("-" * 80)
        print(json.dumps(airtable_records[0], indent=2)[:2000])
        
else:
    print("   No records found!")

print("\n" + "="*80)
