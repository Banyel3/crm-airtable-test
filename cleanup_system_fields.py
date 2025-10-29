"""
Cleanup script to remove Zoho system fields from Airtable tables
These are fields that start with $ in Zoho and shouldn't be synced
"""

import os
from dotenv import load_dotenv
from sync_zoho_to_airtable import AirtableClient

load_dotenv()

# List of system field names to remove (without the $ prefix)
SYSTEM_FIELDS_TO_REMOVE = [
    'currency_symbol',
    'field_states',
    'sharing_permission',
    'state',
    'process_flow',
    'locked_for_me',
    'approval',
    'wizard_connection_path',
    'editable',
    'zia_owner_assignment',
    'is_duplicate',
    'review_process',
    'layout_id',
    'review',
    'zia_visions',
    'orchestration',
    'in_merge',
    'approval_state',
    'pathfinder',
]

def cleanup_system_fields(table_name):
    """Remove system fields from a specific table"""
    client = AirtableClient()
    
    print(f"\nAnalyzing table: {table_name}")
    print("="*60)
    
    # Get existing fields
    existing_fields = client.get_existing_fields(table_name)
    
    # Find system fields that exist
    fields_to_check = []
    for field_name in existing_fields:
        if field_name in SYSTEM_FIELDS_TO_REMOVE:
            fields_to_check.append(field_name)
    
    if not fields_to_check:
        print(f"✓ No system fields found in {table_name}")
        return
    
    print(f"Found {len(fields_to_check)} system fields:")
    for field in fields_to_check:
        print(f"  - {field}")
    
    # Ask for confirmation
    print(f"\n⚠️  WARNING: This will DELETE these fields from Airtable!")
    confirm = input(f"Delete these {len(fields_to_check)} fields from {table_name}? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Cancelled.")
        return
    
    print("\nNote: Automatic field deletion requires additional Airtable API permissions.")
    print("Please delete these fields manually in Airtable:")
    print(f"  1. Go to: https://airtable.com/{client.base_id}")
    print(f"  2. Open the '{table_name}' table")
    print(f"  3. Delete these fields:")
    for field in fields_to_check:
        print(f"     - {field}")

def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║     Airtable System Fields Cleanup Utility                ║
╚═══════════════════════════════════════════════════════════╝

This script helps identify Zoho system fields that shouldn't
be in your Airtable tables.
    """)
    
    client = AirtableClient()
    
    # Get all tables
    tables = client.get_base_schema()
    
    if not tables:
        print("Could not retrieve tables from Airtable")
        return
    
    print(f"Found {len(tables)} tables in your Airtable base:\n")
    for i, table in enumerate(tables, 1):
        print(f"  {i}. {table['name']}")
    
    print("\nOptions:")
    print("  1. Check all tables")
    print("  2. Check specific table")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == '1':
        for table in tables:
            cleanup_system_fields(table['name'])
    elif choice == '2':
        table_num = input(f"Enter table number (1-{len(tables)}): ").strip()
        try:
            idx = int(table_num) - 1
            if 0 <= idx < len(tables):
                cleanup_system_fields(tables[idx]['name'])
            else:
                print("Invalid table number")
        except ValueError:
            print("Invalid input")
    else:
        print("Invalid choice")

if __name__ == '__main__':
    main()
