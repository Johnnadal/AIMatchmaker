# main.py
import os
from dotenv import load_dotenv

load_dotenv()  # Charge automatiquement le fichier .env

import json
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import clickhouse_connect
from google import genai
from google.genai import types


gemini_client = genai.Client(api_key=os.getenv("TA_CLE_API_GEMINI"))

app = FastAPI(
    title="Vid30 AI Matchmaker API",
    description="API autonome d'attribution de projets vidéo IA basée sur ClickHouse & Gemini Enterprise",
    version="1.0.0"
)

# Configuration CORS pour le frontend Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Client ClickHouse
ch_client = clickhouse_connect.get_client(
    host=os.getenv("CLICKHOUSE_HOST"),
    port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
    username=os.getenv("CLICKHOUSE_USER", "default"),
    password=os.getenv("CLICKHOUSE_PASSWORD"),
    secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true"
)

# Client Gemini
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class MatchRequest(BaseModel):
    project_id: str = Field(..., example="proj_99812")
    brief_text: str = Field(..., example="Besoin d'un teaser vidéo photoréaliste de 15s avec voiture de luxe.")

clickhouse_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="query_clickhouse_matchmaker",
            description="Interroge ClickHouse pour extraire les 3 meilleurs candidats.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "w_runway": types.Schema(type=types.Type.NUMBER, description="Poids Runway Gen-3 (0.0 à 1.0)"),
                    "w_midjourney": types.Schema(type=types.Type.NUMBER, description="Poids Midjourney (0.0 à 1.0)"),
                    "w_luma": types.Schema(type=types.Type.NUMBER, description="Poids Luma (0.0 à 1.0)"),
                    "w_flux": types.Schema(type=types.Type.NUMBER, description="Poids Flux (0.0 à 1.0)"),
                    "max_budget": types.Schema(type=types.Type.NUMBER, description="Budget max par heure"),
                },
                required=["w_runway", "w_midjourney", "w_luma", "w_flux", "max_budget"]
            )
        )
    ]
)

def query_clickhouse(w_runway: float, w_midjourney: float, w_luma: float, w_flux: float, max_budget: float):
    query = """
    SELECT 
        creator_id, name, email, avg_rating, hourly_rate_usd,
        (
            ({w_runway:Float32} * score_runway_gen3) +
            ({w_midjourney:Float32} * score_midjourney) +
            ({w_luma:Float32} * score_luma) +
            ({w_flux:Float32} * score_flux)
        ) * avg_rating * on_time_delivery_rate AS match_score
    FROM default.creators
    WHERE available = 1 AND hourly_rate_usd <= {max_budget:Float32}
    ORDER BY match_score DESC
    LIMIT 3;
    """
    params = {
        "w_runway": w_runway,
        "w_midjourney": w_midjourney,
        "w_luma": w_luma,
        "w_flux": w_flux,
        "max_budget": max_budget
    }
    res = ch_client.query(query, parameters=params)
    
    creators = []
    for row in res.result_rows:
        creators.append({
            "creator_id": str(row[0]),
            "name": row[1],
            "email": row[2],
            "rating": float(row[3]),
            "hourly_rate_usd": float(row[4]),
            "match_score": round(float(row[5]), 2)
        })
    return creators

@app.get("/healthz")
def health_check():
    return {"status": "ok", "service": "vid30-matchmaker"}

@app.post("/api/v1/match")
async def process_brief(payload: MatchRequest):
    system_instruction = """
    Tu es l'Agent Matchmaker de Vid30. Analyse le brief client, évalue la répartition des compétences nécessaires 
    (Runway Gen-3, Midjourney, Luma, Flux) de 0.0 à 1.0, identifie le budget max, et déclenche l'outil 'query_clickhouse_matchmaker'.
    """

    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            # gemini-3.6-flash",
            contents=payload.brief_text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[clickhouse_tool],
                temperature=0.1
            )
        )
        


        if not response.function_calls:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail="L'agent n'a pas pu déterminer les paramètres de matching à partir du brief."
            )

        args = response.function_calls[0].args
        creators = query_clickhouse(
            w_runway=float(args.get("w_runway", 0)),
            w_midjourney=float(args.get("w_midjourney", 0)),
            w_luma=float(args.get("w_luma", 0)),
            w_flux=float(args.get("w_flux", 0)),
            max_budget=float(args.get("max_budget", 150))
        )

        return {
            "status": "assigned",
            "project_id": payload.project_id,
            "agent_parameters": args,
            "assigned_creators": creators
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        