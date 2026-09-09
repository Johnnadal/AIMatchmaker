# init_db.py
import os
import clickhouse_connect

def init_schema():
    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
        secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true"
    )

    with open("schema.sql", "r") as f:
        schema_sql = f.read()

    # Exécution des requêtes SQL du schéma
    for statement in schema_sql.split(";"):
        if statement.strip():
            client.command(statement)
            
    print("✅ Table 'default.creators' initialisée dans ClickHouse.")

if __name__ == "__main__":
    init_schema()