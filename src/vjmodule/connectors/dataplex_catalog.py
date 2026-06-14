import json
import os
from google.cloud import datacatalog_v1
from config import Config, MetadataConfig

def load_local_dataplex_metadata() -> str:
  """Loads the batched Dataplex metadata from the local data folder."""
  file_path = "data/dataplex_metadata.json"
  if not os.path.exists(file_path):
    return None
  
  with open(file_path, 'r') as f:
    try:
      metadata = json.load(f)
    except json.JSONDecodeError:
      return None
  return json.dumps(metadata)

def fetch_table_schema_from_dataplex(dataset_id: str, table_id: str) -> dict:
  """
  Utility function to pull live schemas from Dataplex/Data Catalog.
  You can use this in a separate script to build your dataplex_metadata.json file.
  """
  client = datacatalog_v1.DataCatalogClient()
  
  # The GCP resource name format for a BigQuery table
  resource_name = f"//bigquery.googleapis.com/projects/{Config.GCP_PROJECT_ID}/datasets/{dataset_id}/tables/{table_id}"
  
  try:
    request = datacatalog_v1.LookupEntryRequest(linked_resource=resource_name)
    entry = client.lookup_entry(request=request)
    
    schema_info = [
      {
        "column_name": column.column,
        "data_type": column.type_,
        "description": column.description
      }
      for column in entry.schema.columns
    ]
    return {"table": table_id, "schema": schema_info}
  except Exception as e:
    print(f"Error fetching {table_id}: {e}")
    return {}

def save_metadata_to_local_file(metadata: list):
  """Saves the extracted metadata to a local JSON file."""
  file_path = "data/dataplex_metadata.json"
  os.makedirs(os.path.dirname(file_path), exist_ok=True)
  with open(file_path, 'w') as f:
    json.dump(metadata, f, indent=2)
  print(f"Metadata saved to {file_path}")

def extract_and_save_dataplex_metadata(datasets_tables: dict = MetadataConfig.datasets_tables):
  """Extracts metadata for specified datasets and tables, then saves to local file."""
  all_metadata = []
  for dataset, tables in datasets_tables.items():
    for table in tables:
      metadata = fetch_table_schema_from_dataplex(dataset, table)
      dataset_name = {"dataset": dataset}
      if metadata:
        metadata.update(dataset_name)
        all_metadata.append(metadata)
  save_metadata_to_local_file(all_metadata)