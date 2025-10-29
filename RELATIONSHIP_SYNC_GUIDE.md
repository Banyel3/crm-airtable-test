# Recursive Relationship Sync - Implementation Guide

## Overview

The script now supports **recursive dependency resolution** for syncing Zoho CRM data to Airtable with proper relationship handling.

## Key Features Implemented

### 1. **Relationship Detection**

- Automatically detects relationship fields in Zoho records
- Identifies fields that reference other modules (Owner, Created_By, Account_Name, etc.)
- Analyzes record structure to find nested objects with `id` and `name` properties

### 2. **Recursive Dependency Resolution** (Like Merge Sort!)

- When syncing a module (e.g., Accounts), the script:
  1. Analyzes the records to find relationships
  2. Identifies dependent modules (e.g., Users)
  3. **Recursively syncs dependencies first**
  4. Then syncs the original module
  5. Creates linked record fields between tables

### 3. **Zoho ID Preservation**

- Stores Zoho record IDs in a `Zoho_ID` field for each record
- Maintains ID mapping: `{module_name: {zoho_id: airtable_record_id}}`
- Enables proper linking between related records

### 4. **Linked Record Field Creation**

- Automatically creates `multipleRecordLinks` fields in Airtable
- Links related records across tables
- Creates fields like `Owner_Linked`, `Account_Name_Linked`, etc.

### 5. **System Field Filtering**

- Filters out Zoho system fields (those starting with `$`)
- Only syncs actual data fields, not metadata
- Reduces clutter in Airtable tables

## How It Works

### Example: Syncing Accounts Module

```
1. User selects "Accounts" to sync

2. Script analyzes Account records and finds:
   - Owner → Users module
   - Created_By → Users module
   - Modified_By → Users module

3. Recursive sync begins:
   a. Syncs Users module first (dependency)
      - Creates Users table
      - Imports user records
      - Stores Zoho_ID for each user

   b. Returns to Accounts module
      - Creates Accounts table
      - Imports account records
      - Stores Zoho_ID for each account

   c. Creates linked fields:
      - Owner_Linked (links to Users table)
      - Created_By_Linked (links to Users table)
      - Modified_By_Linked (links to Users table)
```

## Data Structure

### Zoho Record (Original)

```json
{
  "id": "7063399000000594097",
  "Account_Name": "King (Sample)",
  "Owner": {
    "name": "Vaniel John Cornelio",
    "id": "7063399000000577001",
    "email": "cornelio.vaniel38@gmail.com"
  },
  "$state": "save",
  "$editable": true
}
```

### Airtable Record (Converted)

```json
{
  "fields": {
    "Zoho_ID": "7063399000000594097",
    "Account_Name": "King (Sample)",
    "Owner": "Vaniel John Cornelio",
    "Owner_ZohoID": "7063399000000577001"
  }
}
```

### After Linking

- `Owner_Linked` field is created
- Links to the Users table record where `Zoho_ID` = "7063399000000577001"

## ID Mapping Structure

```python
airtable_client.id_mapping = {
    "Users": {
        "7063399000000577001": "recABC123",  # Zoho ID → Airtable ID
    },
    "Accounts": {
        "7063399000000594097": "recXYZ789",
    }
}
```

## Sync Flow Diagram

```
sync_module("Accounts")
  │
  ├─> detect_relationships_from_records()
  │     └─> Found: Owner → Users
  │
  ├─> sync_module_recursive("Users", depth=1)
  │     ├─> Create Users table
  │     ├─> Import Users records
  │     └─> Store ID mappings
  │
  ├─> sync_module_recursive("Accounts", depth=0)
  │     ├─> Create Accounts table
  │     ├─> Import Account records
  │     ├─> Store ID mappings
  │     └─> Create linked field: Owner_Linked → Users
  │
  └─> Complete!
```

## New Functions Added

### `detect_relationships_from_records(records)`

- Analyzes record structure to find relationship fields
- Returns: `{field_name: related_module_name}`

### `create_linked_record_field(table_name, field_name, linked_table_name)`

- Creates a `multipleRecordLinks` field in Airtable
- Links two tables together

### `sync_module_recursive(module_name, synced_modules, depth)`

- Recursively syncs modules with dependency resolution
- Prevents circular dependencies
- Tracks already-synced modules

### `convert_zoho_to_airtable(records, field_type_map, relationships)`

- Enhanced to handle relationships
- Preserves Zoho IDs in separate fields
- Stores both name (for display) and ID (for linking)

## Benefits

1. **No Manual Configuration** - Relationships detected automatically
2. **Correct Sync Order** - Dependencies synced first
3. **No Circular Dependencies** - Tracks synced modules
4. **Proper Data Linkage** - Related records properly linked in Airtable
5. **Preserves Relationships** - Maintains referential integrity

## Limitations & Future Enhancements

### Current Limitations

- Links are created but not yet populated (requires second pass)
- Some relationship modules may not be automatically detected
- Users module is assumed for Owner/Created_By fields

### Future Enhancements

1. **Link Population Phase** - Second pass to populate linked record fields
2. **Better Module Detection** - Query Zoho API for field metadata
3. **Bidirectional Links** - Create reverse links automatically
4. **Many-to-Many Support** - Handle junction tables
5. **Selective Sync** - Option to exclude certain relationships

## Usage

Run the script as before:

```powershell
py sync_zoho_to_airtable.py
```

The script will now:

1. Detect relationships automatically
2. Sync dependencies recursively
3. Create proper linked record fields
4. Maintain data integrity across tables

## Notes

- Ensure all related tables exist in Airtable before syncing
- The `Zoho_ID` field will be created automatically in each table
- Linked fields will have `_Linked` suffix (e.g., `Owner_Linked`)
- System fields (starting with `$`) are automatically filtered out
