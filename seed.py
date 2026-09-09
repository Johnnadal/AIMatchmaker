# seed.py
import os
import random
import uuid
import time
from datetime import datetime
import clickhouse_connect

client = clickhouse_connect.get_client(
    host=os.getenv("CLICKHOUSE_HOST"),
    port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
    username=os.getenv("CLICKHOUSE_USER", "default"),
    password=os.getenv("CLICKHOUSE_PASSWORD", ""),
    secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true"
)

PRENOMS = ["Alex", "Sora", "Elena", "Marcus", "Yuki", "Chloe", "David", "Aisha", "Liam", "Zoe", "Hugo", "Maya"]
NOMS = ["VFX", "Prompt", "Cinema", "Art", "Motion", "AI", "Visuals", "Studio", "Labs", "Tech", "Render", "Frame"]
SPECIALITES = ["runway", "midjourney", "luma", "flux", "balanced"]

def seed_database(total_records=100000, batch_size=20000):
    column_names = [
        "creator_id", "name", "email", "available", 
        "score_runway_gen3", "score_midjourney", "score_luma", "score_flux",
        "completed_jobs", "avg_rating", "on_time_delivery_rate", 
        "hourly_rate_usd", "updated_at"
    ]

    print(f"🚀 Début de l'injection de {total_records} créateurs...")
    start_total = time.time()

    inserted = 0
    while inserted < total_records:
        data = []
        current_batch = min(batch_size, total_records - inserted)
        
        for _ in range(current_batch):
            spec = random.choice(SPECIALITES)
            
            s_runway = round(random.uniform(7.5, 10.0) if spec == "runway" else random.uniform(1.0, 7.0), 1)
            s_midjourney = round(random.uniform(7.5, 10.0) if spec == "midjourney" else random.uniform(1.0, 7.0), 1)
            s_luma = round(random.uniform(7.5, 10.0) if spec == "luma" else random.uniform(1.0, 7.0), 1)
            s_flux = round(random.uniform(7.5, 10.0) if spec == "flux" else random.uniform(1.0, 7.0), 1)

            creator = [
                uuid.uuid4(),
                f"{random.choice(PRENOMS)} {random.choice(NOMS)}",
                f"creator_{inserted + len(data)}@vid30.tv",
                1 if random.random() > 0.10 else 0,  # 90% disponibles
                s_runway,
                s_midjourney,
                s_luma,
                s_flux,
                random.randint(1, 200),
                round(random.uniform(4.0, 5.0), 2),
                round(random.uniform(0.90, 1.0), 2),
                float(random.choice([40, 55, 70, 85, 100, 120, 150])),
                datetime.now()
            ]
            data.append(creator)
        
        client.insert("default.creators", data, column_names=column_names)
        inserted += len(data)
        print(f"  -> {inserted} / {total_records} créateurs insérés...")

    print(f"✅ Injection terminée en {time.time() - start_total:.2f} secondes.")

if __name__ == "__main__":
    seed_database(100000)


# 3. Script d'injection massif seed.py (100 000 créateurs)
# Pour injecter 100 000 profils en moins de 10 secondes, le script envoie les données par lots de 20 000 lignes.