# agent.py
import os
from dotenv import load_dotenv

load_dotenv()  # Charge automatiquement le fichier .env

import json
import clickhouse_connect
from google import genai
from google.genai import types


# 1. Connexion ClickHouse
ch_client = clickhouse_connect.get_client(
    host=os.getenv("CLICKHOUSE_HOST"),
    port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
    username=os.getenv("CLICKHOUSE_USER", "default"),
    password=os.getenv("CLICKHOUSE_PASSWORD"),
    secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true"
)

# 2. Fonction d'exécution de la requête analytique
def query_clickhouse_matchmaker(w_runway: float, w_midjourney: float, w_luma: float, w_flux: float, max_budget: float):
    """
    Exécute la requête SQL analytique sur ClickHouse pour extraire les 3 meilleurs profils.
    """
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
            "rating": row[3],
            "hourly_rate": f"${row[4]}/h",
            "match_score": round(row[5], 2)
        })
    return creators

# 3. Déclaration du Tool pour Gemini
clickhouse_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="query_clickhouse_matchmaker",
            description="Interroge ClickHouse pour trouver les 3 meilleurs créateurs vidéo IA selon la pondération des outils et le budget.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "w_runway": types.Schema(type=types.Type.NUMBER, description="Importance de Runway Gen-3 (0.0 à 1.0)"),
                    "w_midjourney": types.Schema(type=types.Type.NUMBER, description="Importance de Midjourney (0.0 à 1.0)"),
                    "w_luma": types.Schema(type=types.Type.NUMBER, description="Importance de Luma Dream Machine (0.0 à 1.0)"),
                    "w_flux": types.Schema(type=types.Type.NUMBER, description="Importance de Flux1 (0.0 à 1.0)"),
                    "max_budget": types.Schema(type=types.Type.NUMBER, description="Budget horaire maximal accepté en USD"),
                },
                required=["w_runway", "w_midjourney", "w_luma", "w_flux", "max_budget"]
            )
        )
    ]
)

# 4. Agent Execution Loop
def run_agent_matchmaking(brief_text: str):
    gemini_client = genai.Client()
    
    system_instruction = """
    Tu es l'Agent Matchmaker de Vid30. Ton rôle est d'analyser les briefs clients pour des projets vidéo IA,
    d'évaluer l'importance relative de chaque outil IA (Runway Gen-3, Midjourney, Luma, Flux) de 0.0 à 1.0,
    et d'appeler l'outil 'query_clickhouse_matchmaker' pour obtenir les 3 meilleurs candidats.
    """

    print(f"🤖 [AGENT] Analyse du brief client : '{brief_text}'\n")

    # Étape A : Génération initiale & Déclenchement du Function Calling
    response = gemini_client.models.generate_content(
        model="gemini-3.6-flash",
        contents=brief_text,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[clickhouse_tool],
            temperature=0.1
        )
    )

    # Étape B : Interception de l'appel de fonction
    if response.function_calls:
        call = response.function_calls[0]
        args = call.args
        print(f"🎯 [TOOL CALL] Gemini a calculé les paramètres ClickHouse suivants :")
        print(f"   -> Runway Weight: {args.get('w_runway')}")
        print(f"   -> Midjourney Weight: {args.get('w_midjourney')}")
        print(f"   -> Luma Weight: {args.get('w_luma')}")
        print(f"   -> Flux Weight: {args.get('w_flux')}")
        print(f"   -> Max Budget: ${args.get('max_budget')}/h\n")

        # Étape C : Exécution SQL
        results = query_clickhouse_matchmaker(
            w_runway=float(args.get("w_runway", 0)),
            w_midjourney=float(args.get("w_midjourney", 0)),
            w_luma=float(args.get("w_luma", 0)),
            w_flux=float(args.get("w_flux", 0)),
            max_budget=float(args.get("max_budget", 150))
        )

        print("⚡ [CLICKHOUSE] Résultats retournés :")
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return results
    else:
        print("❌ L'agent n'a pas appelé l'outil ClickHouse.")
        return None

if __name__ == "__main__":
    # Test d'un brief réaliste
    test_brief = """
    Nous cherchons une équipe pour réaliser une publicité de 30 secondes pour une marque automobile.
    Besoin critique d'un réalisme photoréaliste pour les véhicules (très fort besoin Flux/Midjourney) 
    et de mouvements de caméra fluides et hyper-dynamiques pour les séquences de conduite (besoin majeur Runway Gen-3).
    Budget max : 110$ / heure.
    """
    run_agent_matchmaking(test_brief)