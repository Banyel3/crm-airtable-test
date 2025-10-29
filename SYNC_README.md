# Zoho CRM to Airtable Sync Script

This script fetches all data from your Zoho CRM and imports it into Airtable.

## Prerequisites

1. **Zoho CRM API Access**

   - Client ID and Client Secret (already in your .env)
   - Refresh Token (needs to be generated)

2. **Airtable API Access**
   - Personal Access Token (already in your .env)
   - Base ID (needs to be added)

## Setup Instructions

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Get Zoho CRM Refresh Token

You need to generate a refresh token for Zoho CRM:

1. Go to: https://api-console.zoho.com/
2. Click on "Self Client" or "Server-based Applications"
3. Use your Client ID and Client Secret
4. Set the scope to: `ZohoCRM.modules.ALL,ZohoCRM.settings.ALL`
5. Generate the code and exchange it for a refresh token

**Quick method using their API:**

```bash
# Step 1: Get the authorization code
# Visit this URL in your browser (replace YOUR_CLIENT_ID):
https://accounts.zoho.com/oauth/v2/auth?scope=ZohoCRM.modules.ALL,ZohoCRM.settings.ALL&client_id=YOUR_CLIENT_ID&response_type=code&access_type=offline&redirect_uri=http://localhost

# Step 2: After authorization, you'll be redirected to a URL with a code parameter
# Copy that code and use it in the next command

# Step 3: Exchange the code for a refresh token (run in PowerShell):
curl -X POST "https://accounts.zoho.com/oauth/v2/token?code=YOUR_CODE&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET&grant_type=authorization_code&redirect_uri=http://localhost"
```

Replace:

- `YOUR_CLIENT_ID` with your actual Client ID
- `YOUR_CLIENT_SECRET` with your actual Client Secret
- `YOUR_CODE` with the code you received

The response will include a `refresh_token`. Add this to your `.env` file.

### Step 3: Get Airtable Base ID

1. Go to https://airtable.com/
2. Open the base you want to use
3. The URL will look like: `https://airtable.com/appXXXXXXXXXXXXXX/...`
4. Copy the `appXXXXXXXXXXXXXX` part - that's your Base ID

### Step 4: Update .env File

Add these variables to your `.env` file:

```
CRM_REFRESH_TOKEN=your_refresh_token_here
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
ZOHO_REGION=com
```

**Note on ZOHO_REGION:**

- `com` - US (default)
- `eu` - Europe
- `com.au` - Australia
- `in` - India
- `com.cn` - China

### Step 5: Prepare Airtable Base

Before running the script, create tables in your Airtable base with names matching your Zoho CRM modules. Common modules include:

- Leads
- Contacts
- Accounts
- Deals
- Tasks
- Calls
- etc.

**Note:** The script will automatically create records, but tables must exist first. Alternatively, you can let the script fail on non-existent tables and create them as needed.

## Running the Script

```bash
python sync_zoho_to_airtable.py
```

The script will:

1. Connect to Zoho CRM and fetch all available modules
2. Ask you which modules to sync (all or specific ones)
3. Ask if you want to clear existing Airtable data
4. Fetch all records from selected modules
5. Convert and import them into Airtable

## Features

- ✓ Automatic pagination for large datasets
- ✓ Batch processing for Airtable imports
- ✓ Rate limiting to respect API limits
- ✓ Error handling and progress reporting
- ✓ Automatic token refresh for Zoho
- ✓ Data type conversion (handles nested objects, arrays, etc.)
- ✓ Optional clearing of existing data

## Troubleshooting

### "Missing required environment variables"

Make sure all variables in `.env` are set correctly.

### "Invalid refresh token"

Generate a new refresh token following Step 2 above.

### "Table not found in Airtable"

Create the table in your Airtable base before running the script.

### Rate Limit Errors

The script includes delays, but if you hit limits, you can increase the `time.sleep()` values in the code.

## Notes

- The script converts nested Zoho objects to strings for Airtable compatibility
- Array fields are converted to comma-separated values
- Field names are cleaned to remove special characters
- Each module is synced to a separate Airtable table with the same name

## Customization

You can modify the `convert_zoho_to_airtable()` function to customize how data is transformed between Zoho and Airtable.

## Safety

- Always test with a test Airtable base first
- The script asks for confirmation before clearing data
- Consider backing up your Airtable data before running

## Support

For issues related to:

- Zoho CRM API: https://www.zoho.com/crm/developer/docs/api/v3/
- Airtable API: https://airtable.com/developers/web/api/introduction
