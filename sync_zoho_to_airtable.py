"""
Script to sync data from Zoho CRM to Airtable
Fetches all modules and records from Zoho CRM and imports them into Airtable
"""

import os
import sys
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from pyairtable import Api

# Load environment variables
load_dotenv()

# Zoho CRM Configuration
ZOHO_CLIENT_ID = os.getenv('CRM_CLIENTID')
ZOHO_CLIENT_SECRET = os.getenv('CRM_CLIENTSECRET')
ZOHO_REFRESH_TOKEN = os.getenv('CRM_REFRESH_TOKEN')  # You'll need to add this
ZOHO_REGION = os.getenv('ZOHO_REGION', 'com')  # Default to .com (US datacenter)

# Airtable Configuration
AIRTABLE_API_KEY = os.getenv('AIRTABLE_PERSONALKEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')  # You'll need to add this

# API Endpoints
ZOHO_TOKEN_URL = f'https://accounts.zoho.{ZOHO_REGION}/oauth/v2/token'
ZOHO_API_BASE = f'https://www.zohoapis.{ZOHO_REGION}/crm/v8'


class ZohoCRMClient:
    """Client for interacting with Zoho CRM API"""
    
    def __init__(self):
        self.access_token = None
        self.token_expiry = None
        
    def get_access_token(self):
        """Get or refresh the access token"""
        if self.access_token and self.token_expiry and time.time() < self.token_expiry:
            return self.access_token
            
        print("Refreshing Zoho access token...")
        params = {
            'refresh_token': ZOHO_REFRESH_TOKEN,
            'client_id': ZOHO_CLIENT_ID,
            'client_secret': ZOHO_CLIENT_SECRET,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(ZOHO_TOKEN_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data['access_token']
            self.token_expiry = time.time() + data.get('expires_in', 3600) - 60
            
            # Check scope
            if 'scope' in data:
                print(f"Token scope: {data['scope']}")
            
            print("Access token refreshed successfully")
            return self.access_token
        except requests.exceptions.HTTPError as e:
            print(f"\nError refreshing token: {e}")
            print(f"Response: {response.text if response else 'No response'}")
            raise
    
    def get_module_fields(self, module_name):
        """Get field definitions for a module
        
        Special handling for Users which doesn't have a fields metadata endpoint
        """
        # Fetch field definitions from Zoho
        url = f'{ZOHO_API_BASE}/settings/fields?module={module_name}'
        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            data = response.json()
            fields = data.get('fields', [])
            
            if fields:
                print(f"\n  Found {len(fields)} fields in Zoho schema for {module_name}")
                print(f"  Fields:")
                for field in fields:
                    field_name = field.get('api_name', 'N/A')
                    field_type = field.get('data_type', 'N/A')
                    field_label = field.get('field_label', 'N/A')
                    print(f"    - {field_name} ({field_type}) - {field_label}")
            
            return fields
        except Exception as e:
            print(f"  Warning: Could not fetch field definitions: {e}")
            return []
    
    def get_headers(self):
        """Get headers for API requests"""
        return {
            'Authorization': f'Zoho-oauthtoken {self.get_access_token()}',
            'Content-Type': 'application/json'
        }
    
    def get_modules(self):
        """Get all available modules in Zoho CRM"""
        url = f'{ZOHO_API_BASE}/settings/modules'
        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            
            data = response.json()
            if data.get('modules'):
                # Filter only API-supported modules
                return [m for m in data['modules'] if m.get('api_supported')]
            return []
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print("\n" + "="*60)
                print("AUTHENTICATION ERROR - Invalid or Insufficient Scope")
                print("="*60)
                print("\nYour refresh token doesn't have the required permissions.")
                print("\nPlease generate a NEW refresh token with the correct scope:")
                print("\n1. Visit this URL in your browser:")
                print(f"\nhttps://accounts.zoho.{ZOHO_REGION}/oauth/v2/auth?scope=ZohoCRM.modules.ALL,ZohoCRM.settings.ALL,ZohoCRM.users.READ&client_id={ZOHO_CLIENT_ID}&response_type=code&access_type=offline&redirect_uri=http://localhost")
                print("\n2. After authorization, copy the CODE from the redirect URL")
                print("\n3. Run this command in PowerShell:")
                print(f"\n$body = @{{ grant_type = 'authorization_code'; client_id = '{ZOHO_CLIENT_ID}'; client_secret = '{ZOHO_CLIENT_SECRET}'; redirect_uri = 'http://localhost'; code = 'YOUR_CODE_HERE' }}; Invoke-RestMethod -Method POST -Uri 'https://accounts.zoho.{ZOHO_REGION}/oauth/v2/token' -Body $body")
                print("\n4. Copy the 'refresh_token' value and update it in your .env file")
                print("="*60 + "\n")
            raise
    
    def get_records(self, module_name, page=1, per_page=200):
        """Get records from a specific module with pagination"""
        # First, get the list of record IDs
        url = f'{ZOHO_API_BASE}/{module_name}'
        params = {
            'page': page,
            'per_page': per_page,
            'fields': 'All'
        }
        
        try:
            response = requests.get(url, headers=self.get_headers(), params=params)
            response.raise_for_status()
            
            data = response.json()
            record_ids = [r['id'] for r in data.get('data', [])]
            
            # If we got IDs, fetch full details for each record
            if record_ids:
                print(f"  Fetching full details for {len(record_ids)} records...")
                full_records = []
                
                # Fetch details in smaller batches to avoid rate limits
                for i, record_id in enumerate(record_ids):
                    detail_url = f'{ZOHO_API_BASE}/{module_name}/{record_id}'
                    detail_response = requests.get(detail_url, headers=self.get_headers())
                    detail_response.raise_for_status()
                    
                    detail_data = detail_response.json()
                    if detail_data.get('data'):
                        full_records.extend(detail_data['data'])
                    
                    # Small delay to avoid rate limiting
                    if (i + 1) % 10 == 0:
                        time.sleep(0.5)
                
                return full_records, data.get('info', {})
            else:
                return [], data.get('info', {})
                
        except requests.exceptions.HTTPError as e:
            print(f"\n  HTTP Error: {e}")
            if e.response:
                print(f"  Response Status: {e.response.status_code}")
                print(f"  Response Body: {e.response.text}")
            raise    
    
    def get_users(self):
        """Get users from Zoho CRM (uses different API endpoint)"""
        url = f'{ZOHO_API_BASE}/users'
        params = {
            'type': 'AllUsers'
        }
        
        try:
            response = requests.get(url, headers=self.get_headers(), params=params)
            response.raise_for_status()
            
            data = response.json()
            users = data.get('users', [])
            
            print(f"  Fetched {len(users)} users from Zoho CRM")
            return users
            
        except requests.exceptions.HTTPError as e:
            print(f"  Warning: Could not fetch users: {e}")
            if e.response:
                print(f"  Response: {e.response.text}")
            return []
    
    def get_all_records(self, module_name):
        """Get all records from a module (handles pagination)
        
        Special handling for Users module which uses a different API endpoint
        """
        # Special case: Users module uses different API
        if module_name == 'Users':
            return self.get_users()
        
        all_records = []
        page = 1
        more_records = True
        
        print(f"Fetching records from {module_name}...")
        
        while more_records:
            try:
                records, info = self.get_records(module_name, page=page)
                if records:
                    all_records.extend(records)
                    print(f"  Fetched page {page}: {len(records)} records (Total: {len(all_records)})")
                    
                    # Check if there are more pages
                    more_records = info.get('more_records', False)
                    page += 1
                else:
                    more_records = False
                    
                # Rate limiting - be nice to the API
                time.sleep(0.5)
                
            except requests.exceptions.HTTPError as e:
                print(f"  Error fetching page {page}: {str(e)}")
                if e.response:
                    try:
                        error_data = e.response.json()
                        print(f"  Zoho API Error: {error_data}")
                    except:
                        print(f"  Response text: {e.response.text}")
                break
            except Exception as e:
                print(f"  Unexpected error on page {page}: {str(e)}")
                break
        
        print(f"Total records fetched from {module_name}: {len(all_records)}")
        return all_records


class AirtableClient:
    """Client for interacting with Airtable API"""
    
    def __init__(self):
        if not AIRTABLE_API_KEY:
            raise ValueError("AIRTABLE_PERSONALKEY not found in .env file")
        if not AIRTABLE_BASE_ID:
            raise ValueError("AIRTABLE_BASE_ID not found in .env file")
            
        self.api = Api(AIRTABLE_API_KEY)
        self.base_id = AIRTABLE_BASE_ID
        self.base = None
        
        # Mapping of Zoho ID to Airtable record ID for linking
        # Format: {module_name: {zoho_id: airtable_record_id}}
        self.id_mapping = {}
    
    def map_zoho_type_to_airtable(self, zoho_field):
        """Map Zoho field type to Airtable field type"""
        zoho_type = zoho_field.get('data_type', 'text')
        
        # Map Zoho types to Airtable types
        type_mapping = {
            'text': 'singleLineText',
            'textarea': 'multilineText',
            'email': 'email',
            'phone': 'phoneNumber',
            'website': 'url',
            'picklist': 'singleSelect',
            'multiselectpicklist': 'multipleSelects',
            'boolean': 'singleLineText',  # Use text for booleans (Yes/No)
            'integer': 'number',
            'bigint': 'number',
            'double': 'number',
            'currency': 'currency',
            'date': 'date',
            'datetime': 'dateTime',
            'lookup': 'singleLineText',
            'ownerlookup': 'singleLineText',
            'userlookup': 'singleLineText',
            'fileupload': 'multilineText',
            'profileimage': 'multilineText',
        }
        
        airtable_type = type_mapping.get(zoho_type.lower(), 'singleLineText')
        
        # Build field config
        field_config = {'type': airtable_type}
        
        # Add options for currency fields
        if airtable_type == 'currency':
            field_config['options'] = {
                'precision': 2,
                'symbol': '$'
            }
        
        # Add options for number fields
        elif airtable_type == 'number':
            field_config['options'] = {
                'precision': 0 if zoho_type.lower() in ['integer', 'bigint'] else 2
            }
        
        # Add options for date fields
        elif airtable_type == 'date':
            field_config['options'] = {
                'dateFormat': {
                    'name': 'iso',
                    'format': 'YYYY-MM-DD'
                }
            }
        
        # Add options for dateTime fields
        elif airtable_type == 'dateTime':
            field_config['options'] = {
                'dateFormat': {
                    'name': 'iso',
                    'format': 'YYYY-MM-DD'
                },
                'timeFormat': {
                    'name': '24hour',
                    'format': 'HH:mm'
                },
                'timeZone': 'utc'
            }
        
        # Add options for singleSelect fields (picklist)
        elif airtable_type == 'singleSelect':
            # Get pick_list_values from zoho_field
            choices = []
            if 'pick_list_values' in zoho_field:
                pick_list = zoho_field['pick_list_values']
                # Extract just the display_value or actual_value
                for item in pick_list:
                    if isinstance(item, dict):
                        value = item.get('display_value') or item.get('actual_value')
                        if value:
                            choices.append({'name': value})
                    elif isinstance(item, str):
                        choices.append({'name': item})
            
            # If no choices found, add a default one (Airtable requires at least one choice)
            if not choices:
                choices = [{'name': 'None'}]
            
            field_config['options'] = {'choices': choices}
        
        # Add options for multipleSelects fields
        elif airtable_type == 'multipleSelects':
            # Get pick_list_values from zoho_field
            choices = []
            if 'pick_list_values' in zoho_field:
                pick_list = zoho_field['pick_list_values']
                # Extract just the display_value or actual_value
                for item in pick_list:
                    if isinstance(item, dict):
                        value = item.get('display_value') or item.get('actual_value')
                        if value:
                            choices.append({'name': value})
                    elif isinstance(item, str):
                        choices.append({'name': item})
            
            # If no choices found, add a default one (Airtable requires at least one choice)
            if not choices:
                choices = [{'name': 'None'}]
            
            field_config['options'] = {'choices': choices}
        
        return field_config
    
    def get_base_schema(self):
        """Get the base schema to see available tables"""
        try:
            # Use the Airtable Web API to get base schema
            url = f'https://api.airtable.com/v0/meta/bases/{self.base_id}/tables'
            headers = {'Authorization': f'Bearer {AIRTABLE_API_KEY}'}
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('tables', [])
            else:
                print(f"  Warning: Could not fetch base schema: {response.status_code}")
                return []
        except Exception as e:
            print(f"  Warning: Error fetching base schema: {e}")
            return []
    
    def create_field_if_not_exists(self, table_name, field_name, field_config=None):
        """Create a field in the table if it doesn't exist"""
        if field_config is None:
            field_config = {'type': 'singleLineText'}
            
        try:
            url = f'https://api.airtable.com/v0/meta/bases/{self.base_id}/tables'
            headers = {'Authorization': f'Bearer {AIRTABLE_API_KEY}'}
            
            # Get the table ID and existing fields
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return False
            
            tables = response.json().get('tables', [])
            table_id = None
            existing_fields = []
            existing_field_names_lower = {}  # Map lowercase names to actual names
            
            for table in tables:
                if table['name'] == table_name:
                    table_id = table['id']
                    existing_fields = [f['name'] for f in table.get('fields', [])]
                    # Create case-insensitive mapping
                    for fname in existing_fields:
                        existing_field_names_lower[fname.lower()] = fname
                    break
            
            if not table_id:
                print(f"  Warning: Table {table_name} not found")
                return False
            
            # Check if field already exists (exact match)
            if field_name in existing_fields:
                return True
            
            # Check if field exists with different case (e.g., "State" vs "state")
            if field_name.lower() in existing_field_names_lower:
                # Field already exists with different casing, don't create duplicate
                return True
            
            # Create the field with proper type configuration
            create_url = f'https://api.airtable.com/v0/meta/bases/{self.base_id}/tables/{table_id}/fields'
            field_data = {'name': field_name}
            field_data.update(field_config)  # Merge the field config (type and options)
            
            create_response = requests.post(create_url, headers={**headers, 'Content-Type': 'application/json'}, json=field_data)
            
            if create_response.status_code in [200, 201]:
                return True
            else:
                error_data = create_response.json() if create_response.text else {}
                error_type = error_data.get('error', {}).get('type', '')
                
                # If it's a duplicate error, that's actually fine - field exists
                if error_type == 'DUPLICATE_OR_EMPTY_FIELD_NAME':
                    return True
                    
                print(f"  Warning: Could not create field '{field_name}': {create_response.text}")
                return False
                
        except Exception as e:
            print(f"  Warning: Error creating field '{field_name}': {e}")
            return False
    
    def ensure_fields_exist(self, table_name, field_definitions):
        """Ensure all fields exist in the table with correct types
        
        Args:
            table_name: Name of the Airtable table
            field_definitions: Dict mapping field names to field configs {name: {type: ..., options: ...}}
        """
        print(f"  Checking/creating fields in Airtable table '{table_name}'...")
        
        # Get existing fields once to avoid repeated API calls
        existing_fields = set(self.get_existing_fields(table_name))
        existing_fields_lower = {f.lower(): f for f in existing_fields}
        
        fields_to_create = []
        skipped_exact = 0
        skipped_case = 0
        
        for field_name, field_config in field_definitions.items():
            # Skip if exact match exists
            if field_name in existing_fields:
                skipped_exact += 1
                continue
            # If case-insensitive match exists, skip
            if field_name.lower() in existing_fields_lower:
                skipped_case += 1
                continue
            # This is a truly new field
            fields_to_create.append((field_name, field_config))
        
        if not fields_to_create:
            print(f"  All {len(field_definitions)} fields already exist ({skipped_exact} exact, {skipped_case} case-insensitive)")
            return True
        
        print(f"  Creating {len(fields_to_create)} new fields with proper types...")
        created_count = 0
        
        for field_name, field_config in fields_to_create:
            if self.create_field_if_not_exists(table_name, field_name, field_config):
                created_count += 1
            time.sleep(0.15)  # Rate limiting
        
        print(f"  Created {created_count} new fields, {skipped_exact + skipped_case} already existed")
        return True
    
    def get_existing_fields(self, table_name):
        """Get existing field names from a table"""
        try:
            tables = self.get_base_schema()
            for table in tables:
                if table['name'] == table_name:
                    return [field['name'] for field in table.get('fields', [])]
            return []
        except Exception as e:
            print(f"  Warning: Could not get existing fields: {e}")
            return []
    
    def table_exists(self, table_name):
        """Check if a table exists in the base"""
        tables = self.get_base_schema()
        table_names = [t['name'] for t in tables]
        return table_name in table_names
    
    def create_table(self, table_name, fields=None):
        """Create a new table in Airtable
        
        Args:
            table_name: Name of the table to create
            fields: Optional list of field definitions. If not provided, creates with default Name field
        
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f'https://api.airtable.com/v0/meta/bases/{self.base_id}/tables'
            headers = {
                'Authorization': f'Bearer {AIRTABLE_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            # Default: Create table with a basic primary field
            # We'll add other fields later using the field creation logic
            table_data = {
                'name': table_name,
                'fields': fields if fields else [
                    {
                        'name': 'Name',
                        'type': 'singleLineText'
                    }
                ]
            }
            
            response = requests.post(url, headers=headers, json=table_data)
            
            if response.status_code in [200, 201]:
                print(f"  ✓ Created table '{table_name}' in Airtable")
                return True
            else:
                print(f"  ✗ Failed to create table '{table_name}': {response.status_code}")
                print(f"    Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"  ✗ Error creating table '{table_name}': {e}")
            return False
    
    def create_or_get_table(self, table_name):
        """Get a table object, creating it if it doesn't exist"""
        if not self.table_exists(table_name):
            print(f"  Table '{table_name}' doesn't exist. Creating it...")
            self.create_table(table_name)
            # Give Airtable a moment to process the table creation
            time.sleep(1)
        
        return self.api.table(self.base_id, table_name)
    
    def batch_create_records(self, table_name, records, batch_size=10, zoho_records=None):
        """Create records in batches, handling field creation dynamically
        
        Args:
            table_name: Name of the Airtable table
            records: List of records to create (Airtable format)
            batch_size: Number of records per batch
            zoho_records: Original Zoho records (to extract IDs for mapping)
        """
        if not records:
            return []
        
        # Get existing fields and create a case-insensitive mapping
        existing_fields = self.get_existing_fields(table_name)
        field_mapping = {f.lower(): f for f in existing_fields}
        
        table = self.create_or_get_table(table_name)
        created_records = []
        
        # Initialize ID mapping for this module if not exists
        if table_name not in self.id_mapping:
            self.id_mapping[table_name] = {}
        
        # Airtable allows max 10 records per batch
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            try:
                # Extract fields and map to existing Airtable field names
                batch_data = []
                for idx, record in enumerate(batch):
                    record_fields = record['fields'] if isinstance(record, dict) and 'fields' in record else record
                    
                    # Map fields to existing Airtable fields (case-insensitive)
                    mapped_fields = {}
                    for key, value in record_fields.items():
                        # Try to find matching field (case-insensitive)
                        if key in existing_fields:
                            # Exact match
                            mapped_fields[key] = value
                        elif key.lower() in field_mapping:
                            # Case-insensitive match
                            mapped_fields[field_mapping[key.lower()]] = value
                        # else: skip field that doesn't exist
                    
                    if mapped_fields:  # Only add if we have fields
                        batch_data.append(mapped_fields)
                
                if batch_data:
                    result = table.batch_create(batch_data)
                    created_records.extend(result)
                    
                    # Store Zoho ID to Airtable ID mapping if we have original Zoho records
                    if zoho_records:
                        batch_start = i
                        for idx, airtable_record in enumerate(result):
                            zoho_record_idx = batch_start + idx
                            if zoho_record_idx < len(zoho_records):
                                zoho_id = zoho_records[zoho_record_idx].get('id')
                                if zoho_id:
                                    self.id_mapping[table_name][zoho_id] = airtable_record['id']
                    
                    print(f"  Created batch {i//batch_size + 1}: {len(batch_data)} records")
                time.sleep(0.2)  # Rate limiting
            except Exception as e:
                error_msg = str(e)
                print(f"  Error creating batch: {error_msg}")
                
                # Handle specific error types
                if 'INVALID_MULTIPLE_CHOICE_OPTIONS' in error_msg:
                    import re
                    # Extract the option that failed
                    option_match = re.search(r'select option "([^"]+)"', error_msg)
                    if option_match:
                        option = option_match.group(1)
                        print(f"  ⚠️  Cannot add option '{option}' to select field")
                        print(f"  💡 Solution: In Airtable, convert any Single/Multiple Select fields to 'Single line text' type")
                        print(f"      Or manually add the option '{option}' to the select field's choices")
                
                # Try to extract which field is causing the issue
                elif 'INVALID_VALUE_FOR_COLUMN' in error_msg:
                    import re
                    field_match = re.search(r'Field "([^"]+)"', error_msg)
                    if field_match:
                        problem_field = field_match.group(1)
                        print(f"  ⚠️  Problem field: {problem_field}")
                        
                        # Show sample value being sent for this field
                        if batch_data and problem_field in batch_data[0]:
                            sample_value = batch_data[0][problem_field]
                            print(f"  Sample value: {repr(sample_value)} (type: {type(sample_value).__name__})")
                            print(f"  💡 Tip: The field '{problem_field}' might already exist in Airtable with a different type.")
                            print(f"      Delete the field in Airtable and run the script again to recreate it with the correct type.")
                
                # Try to print more details
                if hasattr(e, 'response'):
                    try:
                        print(f"  Response: {e.response.json()}")
                    except:
                        pass
                # Continue with next batch
                
        return created_records
    
    def clear_table(self, table_name):
        """Clear all records from a table"""
        try:
            table = self.create_or_get_table(table_name)
            all_records = table.all()
            
            if all_records:
                record_ids = [r['id'] for r in all_records]
                # Delete in batches of 10
                for i in range(0, len(record_ids), 10):
                    batch_ids = record_ids[i:i + 10]
                    table.batch_delete(batch_ids)
                    time.sleep(0.2)
                    
                print(f"  Cleared {len(all_records)} records from {table_name}")
        except Exception as e:
            print(f"  Error clearing table {table_name}: {str(e)}")


def convert_zoho_to_airtable(zoho_records, field_type_map=None, relationships=None, module_name=None):
    """Convert Zoho CRM records to Airtable format
    
    Args:
        zoho_records: List of records from Zoho CRM
        field_type_map: Dict mapping field names to their Airtable type configs
        relationships: Dict mapping field names to related module names (for linked records)
        module_name: Name of the module being converted (for module-specific handling)
    """
    airtable_records = []
    
    # Skip system fields (starting with $) but preserve the ID field
    # We'll store it as Zoho_ID for linking purposes
    
    if field_type_map is None:
        field_type_map = {}
    
    if relationships is None:
        relationships = {}
    
    # Module-specific field blacklists (fields to skip entirely)
    field_blacklists = {
        'Users': {
            'offset',  # Timezone offset - problematic field
            'time_zone',  # Complex timezone object
            'Microsoft',  # Boolean flag
            'country_locale',  # Locale string
        }
    }
    
    blacklisted_fields = field_blacklists.get(module_name, set())
    
    for record in zoho_records:
        # Create a flattened version of the record
        fields = {}
        
        # Include ALL fields from Zoho - true mirror
        
        for key, value in record.items():
            # Skip blacklisted fields for this module (known problematic fields only)
            if key in blacklisted_fields:
                continue
            
            # Skip None values (empty fields)
            if value is None:
                continue
            
            # Convert field name - remove $ prefix if present (Airtable doesn't allow $)
            if key.startswith('$'):
                clean_key = key.lstrip('$')
            else:
                clean_key = key
            
            # Get the expected Airtable type for this field
            field_config = field_type_map.get(clean_key, {})
            expected_type = field_config.get('type', 'singleLineText')
                
            # Handle different data types based on expected Airtable type
            if isinstance(value, bool):
                # Convert boolean to text to avoid checkbox type issues
                fields[clean_key] = "Yes" if value else "No"
            elif isinstance(value, dict):
                # For nested objects (like Owner, Created_By), just extract the name
                if 'name' in value:
                    fields[clean_key] = value['name']
                elif 'id' in value and 'name' not in value:
                    # Just store the ID as text
                    fields[clean_key] = str(value.get('id', ''))
                else:
                    # Convert dict to string
                    fields[clean_key] = str(value)
            elif isinstance(value, list):
                # For arrays, store as comma-separated or JSON
                if not value:  # Skip empty lists
                    continue
                if isinstance(value[0], dict):
                    # Extract names if available
                    names = [v.get('name', str(v)) for v in value]
                    fields[clean_key] = ', '.join(names)
                else:
                    fields[clean_key] = ', '.join([str(v) for v in value])
            elif isinstance(value, (int, float)):
                # Handle numbers based on expected type
                if expected_type in ['number', 'currency']:
                    # Keep as number for number/currency fields
                    fields[clean_key] = value
                elif expected_type == 'singleLineText':
                    # Convert to string for text fields
                    fields[clean_key] = str(value)
                else:
                    # Default: keep as number
                    fields[clean_key] = value
            elif isinstance(value, str):
                # String value - may need conversion based on expected type
                if expected_type in ['number', 'currency']:
                    # Convert numeric strings to actual numbers
                    try:
                        # Try to convert to number
                        if '.' in value or 'e' in value.lower():
                            fields[clean_key] = float(value)
                        else:
                            fields[clean_key] = int(value)
                    except (ValueError, AttributeError):
                        # If conversion fails, skip the field
                        pass
                else:
                    # Keep as string for text fields
                    fields[clean_key] = value
            else:
                # Convert anything else to string
                fields[clean_key] = str(value)
        
        airtable_records.append({'fields': fields})
    
    return airtable_records


def sync_module_recursive(zoho_client, airtable_client, module_name, clear_existing=False, synced_modules=None, depth=0):
    """Recursively sync a module and its dependencies from Zoho to Airtable
    
    Args:
        zoho_client: Zoho CRM client
        airtable_client: Airtable client
        module_name: Name of the module to sync
        clear_existing: Whether to clear existing records
        synced_modules: Set of already synced modules (to avoid circular dependencies)
        depth: Current recursion depth (for indentation)
    
    Returns:
        Number of records synced
    """
    if synced_modules is None:
        synced_modules = set()
    
    # Check if already synced
    if module_name in synced_modules:
        print(f"{'  ' * depth}↩ Module '{module_name}' already synced, skipping")
        return 0
    
    indent = '  ' * depth
    print(f"\n{indent}{'='*60}")
    print(f"{indent}Syncing module: {module_name} (depth: {depth})")
    print(f"{indent}{'='*60}")
    
    try:
        # Check if table exists in Airtable, create if it doesn't
        if not airtable_client.table_exists(module_name):
            print(f"{indent}⚠️  Table '{module_name}' does not exist in Airtable.")
            print(f"{indent}📝 Creating table '{module_name}' automatically...")
            
            if not airtable_client.create_table(module_name):
                print(f"{indent}✗ Failed to create table '{module_name}'.")
                print(f"{indent}   Please create it manually at: https://airtable.com/{AIRTABLE_BASE_ID}")
                return 0
            
            print(f"{indent}✓ Table '{module_name}' created successfully!")
        
        # Fetch field definitions from Zoho to get correct data types
        print(f"{indent}Fetching field definitions from Zoho CRM...")
        zoho_fields = zoho_client.get_module_fields(module_name)
        
        # Create field type mapping - Include ALL fields from Zoho (including system fields)
        # This creates a true 1:1 mirror of the Zoho table
        field_type_map = {}
        for zoho_field in zoho_fields:
            field_name = zoho_field.get('api_name', '')
            
            # Include ALL fields - no filtering
            # Convert $ prefix to avoid Airtable field name issues ($ is not allowed)
            if field_name.startswith('$'):
                # Remove the $ prefix for Airtable compatibility
                clean_field_name = field_name.lstrip('$')
            else:
                clean_field_name = field_name
            
            # Add to field type map
            if clean_field_name:
                field_type_map[clean_field_name] = airtable_client.map_zoho_type_to_airtable(zoho_field)
        
        # Fetch records from Zoho
        zoho_records = zoho_client.get_all_records(module_name)
        
        if not zoho_records:
            print(f"{indent}No records found in {module_name}")
            synced_modules.add(module_name)
            return 0
        
        # Simple conversion - no relationship detection, no extra fields
        # Just pure 1:1 mapping from Zoho to Airtable
        print(f"{indent}Converting {len(zoho_records)} records to Airtable format...")
        airtable_records = convert_zoho_to_airtable(zoho_records, field_type_map, relationships={}, module_name=module_name)
        
        # Use ONLY the field definitions from Zoho metadata (no extra fields)
        # This ensures we only create fields that exist in Zoho
        print(f"{indent}Using field schema from Zoho CRM (no extra fields)...")
        field_definitions = field_type_map.copy()  # Use exact fields from Zoho
        
        # Ensure all fields exist in Airtable with correct types
        if field_definitions:
            airtable_client.ensure_fields_exist(module_name, field_definitions)
        
        # Clear existing records if requested
        if clear_existing:
            print(f"{indent}Clearing existing records from {module_name}...")
            airtable_client.clear_table(module_name)
        
        # Import to Airtable
        print(f"{indent}Importing {len(airtable_records)} records to Airtable...")
        created = airtable_client.batch_create_records(module_name, airtable_records, zoho_records=zoho_records)
        
        # Mark this module as synced
        synced_modules.add(module_name)
        
        print(f"{indent}✓ Successfully synced {len(created)} records to {module_name}")
        return len(created)
        
    except Exception as e:
        print(f"{indent}✗ Error syncing {module_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0


def sync_module(zoho_client, airtable_client, module_name, clear_existing=False):
    """Sync a single module from Zoho to Airtable (entry point that uses recursive sync)"""
    synced_modules = set()
    return sync_module_recursive(zoho_client, airtable_client, module_name, clear_existing, synced_modules, depth=0)


def main():
    """Main execution function"""
    print(f"""
{'='*60}
Zoho CRM to Airtable Sync
{'='*60}
Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)
    
    # Validate environment variables
    if not all([ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, AIRTABLE_API_KEY]):
        print("Error: Missing required environment variables!")
        print("Required variables:")
        print("  - CRM_CLIENTID")
        print("  - CRM_CLIENTSECRET")
        print("  - CRM_REFRESH_TOKEN (you need to add this)")
        print("  - AIRTABLE_PERSONALKEY")
        print("  - AIRTABLE_BASE_ID (you need to add this)")
        sys.exit(1)
    
    try:
        # Initialize clients
        zoho_client = ZohoCRMClient()
        airtable_client = AirtableClient()
        
        # Check Airtable tables
        print("\nChecking Airtable base...")
        airtable_tables = airtable_client.get_base_schema()
        if airtable_tables:
            print(f"Found {len(airtable_tables)} existing tables in Airtable:")
            for table in airtable_tables:
                print(f"  - {table['name']}")
        else:
            print("⚠️  Could not retrieve Airtable tables. Make sure:")
            print("  1. Your AIRTABLE_BASE_ID is correct")
            print("  2. Your token has 'schema.bases:read' permission")
            print("  3. You have access to the base")
        
        # Get all modules
        print("\nFetching available modules from Zoho CRM...")
        modules = zoho_client.get_modules()
        
        if not modules:
            print("No modules found in Zoho CRM")
            sys.exit(1)
        
        print(f"\nFound {len(modules)} modules:")
        for i, module in enumerate(modules, 1):
            print(f"  {i}. {module['api_name']} ({module['plural_label']})")
        
        # Ask user which modules to sync
        print("\nOptions:")
        print("  1. Sync all modules")
        print("  2. Select specific modules")
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        modules_to_sync = []
        if choice == '1':
            modules_to_sync = [m['api_name'] for m in modules]
        elif choice == '2':
            print("\nEnter module numbers to sync (comma-separated, e.g., 1,3,5):")
            indices = input().strip().split(',')
            for idx in indices:
                try:
                    i = int(idx.strip()) - 1
                    if 0 <= i < len(modules):
                        modules_to_sync.append(modules[i]['api_name'])
                except ValueError:
                    pass
        
        if not modules_to_sync:
            print("No modules selected. Exiting.")
            sys.exit(0)
        
        # Ask about clearing existing data
        clear = input("\nClear existing Airtable data before sync? (y/n): ").strip().lower() == 'y'
        
        # Sync each module
        total_synced = 0
        for module_name in modules_to_sync:
            synced = sync_module(zoho_client, airtable_client, module_name, clear_existing=clear)
            total_synced += synced
        
        # Summary
        print(f"""
{'='*60}
Sync Complete!
{'='*60}
Total records synced: {total_synced}
Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
        
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
