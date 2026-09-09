@app.post("/api/v1/match")
async def process_brief(payload: MatchRequest):
    system_instruction = """
    Tu es l'Agent Matchmaker de Vid30. Analyse le brief client, évalue la répartition des compétences nécessaires 
    (Runway Gen-3, Midjourney, Luma, Flux) de 0.0 à 1.0, identifie le budget max, et déclenche l'outil 'query_clickhouse_matchmaker'.
    """

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=payload.brief_text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[clickhouse_tool],
                temperature=0.1
            )
        )

        if response.function_calls:
            args = response.function_calls[0].args
        else:
            # Fallback par défaut si pas de function call
            args = {"w_runway": 0.8, "w_midjourney": 0.6, "w_luma": 0.2, "w_flux": 0.2, "max_budget": 120.0}

    except Exception as e:
        # Fallback de secours si quota API dépassé (429)
        print(f"[WARNING] Erreur Gemini ({e}), utilisation des paramètres de secours.")
        args = {"w_runway": 0.8, "w_midjourney": 0.6, "w_luma": 0.2, "w_flux": 0.2, "max_budget": 120.0}

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