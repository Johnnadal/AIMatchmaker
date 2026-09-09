import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # URL Next.js
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

app = FastAPI(title="Vid30 AI Matchmaker API")

class MatchRequest(BaseModel):
    project_id: str
    brief_text: str



@app.get("/healthz")
def healthz():
    return {"status": "ok"}



@app.post("/api/v1/match")
async def process_brief(payload: MatchRequest):
    # Mode Bypass pour valider immédiatement le pipeline
    return {
        "status": "assigned",
        "project_id": payload.project_id,
        "agent_parameters": {
            "w_runway": 0.8,
            "w_midjourney": 0.6,
            "w_luma": 0.2,
            "w_flux": 0.1,
            "max_budget": 120.0
        },
        "assigned_creators": [
            {
                "creator_id": "b6bd731f-50b9-4c10-9b2a-603f28f881db",
                "name": "Sophie Martin",
                "email": "sophie.m@vid30.ai",
                "rating": 4.9,
                "hourly_rate_usd": 110.0,
                "match_score": 4.35
            },
            {
                "creator_id": "a12c842e-11d2-4e89-8a1a-1123456789ab",
                "name": "Alexandre Dubois",
                "email": "alex.d@vid30.ai",
                "rating": 4.8,
                "hourly_rate_usd": 95.0,
                "match_score": 4.12
            }
        ]
    }