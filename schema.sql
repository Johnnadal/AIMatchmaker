-- schema.sql
CREATE TABLE IF NOT EXISTS default.creators
(
    creator_id UUID,
    name String,
    email String,
    available UInt8 DEFAULT 1,
    score_runway_gen3 Float32 DEFAULT 0.0,
    score_midjourney Float32 DEFAULT 0.0,
    score_luma Float32 DEFAULT 0.0,
    score_flux Float32 DEFAULT 0.0,
    completed_jobs UInt32 DEFAULT 0,
    avg_rating Float32 DEFAULT 0.0,
    on_time_delivery_rate Float32 DEFAULT 1.0,
    hourly_rate_usd Float32 DEFAULT 50.0,
    updated_at DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (available, hourly_rate_usd, creator_id);