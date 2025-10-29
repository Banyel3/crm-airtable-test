"""Test Airtable connection and permissions"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv('AIRTABLE_PERSONALKEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')

print(f"Testing Airtable connection...")
print(f"Base ID: {AIRTABLE_BASE_ID}")
print(f"Token: {AIRTABLE_API_KEY[:20]}...")

# Test 1: Get base schema
print("\n" + "="*60)
print("Test 1: Fetching base schema")
print("="*60)
url = f'https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables'
headers = {'Authorization': f'Bearer {AIRTABLE_API_KEY}'}
response = requests.get(url, headers=headers)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    data = response.json()
    tables = data.get('tables', [])
    print(f"\n✓ Success! Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table['name']} (ID: {table['id']})")
else:
    print(f"\n✗ Error: {response.status_code}")
    
# Test 2: List all accessible bases
print("\n" + "="*60)
print("Test 2: Listing all accessible bases")
print("="*60)
url = 'https://api.airtable.com/v0/meta/bases'
response = requests.get(url, headers=headers)

print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    bases = data.get('bases', [])
    print(f"\n✓ Found {len(bases)} accessible bases:")
    for base in bases:
        print(f"  - {base['name']} (ID: {base['id']})")
        if base['id'] == AIRTABLE_BASE_ID:
            print(f"    ✓ This is your configured base!")
else:
    print(f"Response: {response.text}")
