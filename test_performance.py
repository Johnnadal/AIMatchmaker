import os
import time
import clickhouse_connect

client = clickhouse_connect.get_client(
    host=os.getenv("CLICKHOUSE_HOST", "localhost"),
    port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
    username=os.getenv("CLICKHOUSE_USER", "default"),
    password=os.getenv("CLICKHOUSE_PASSWORD", ""),
    secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true"
)

query = """
SELECT 
    name, 
    hourly_rate_usd,
    ((0.8 * score_runway_gen3) + (0.2 * score_midjourney)) * avg_rating AS match_score
FROM default.creators
WHERE available = 1 AND hourly_rate_usd <= 100
ORDER BY match_score DESC
LIMIT 3;
"""

start_time = time.perf_counter()
result = client.query(query)
end_time = time.perf_counter()

print("--- RÉSULTATS DE MATCHING EXPRESS ---")
for row in result.result_rows:
    print(f"Nom: {row[0]} | Taux: ${row[1]}/h | Match Score: {round(row[2], 2)}")

print(f"\n⚡ Temps de réponse ClickHouse : {(end_time - start_time) * 1000:.2f} ms")