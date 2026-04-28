from dataplex_connector import DataplexConnector
connector = DataplexConnector(
    project_id="insight-pilot-trios"
)

entities = connector.fetch_all_entities()
schema = connector.fetch_schema(
    "//bigquery.googleapis.com/projects/insight-pilot-trios/datasets/modamart_core/tables/dim_promotion",
    "eu"
)
print(schema)