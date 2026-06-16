import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from supabase import create_client, Client

# --- Config ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # use a service_role key aqui (backend), nunca a anon key

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Defina SUPABASE_URL e SUPABASE_KEY nas variáveis de ambiente.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE = "email_clicks"

app = FastAPI(title="Click Tracker API")


# --- 1. Endpoint que registra o clique ---
@app.post("/api/track-click")
async def track_click(origem: str = "desconhecido"):
    """
    Chamado pela página /redirecionando via navigator.sendBeacon().
    Recebe ?origem=carrinho na própria query string.
    """
    try:
        supabase.table(TABLE).insert({
            "origem": origem,
            "clicked_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 2. Endpoint que resgata os dados agregados ---
@app.get("/api/clicks")
async def get_clicks(origem: Optional[str] = None):
    """
    Sem parâmetro: retorna contagem total e por origem.
    Com ?origem=carrinho: retorna só a contagem daquela origem.
    """
    try:
        query = supabase.table(TABLE).select("origem")
        if origem:
            query = query.eq("origem", origem)
        result = query.execute()
        rows = result.data or []

        counts: dict[str, int] = {}
        for row in rows:
            o = row["origem"]
            counts[o] = counts.get(o, 0) + 1

        return {
            "total": len(rows),
            "by_origem": counts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def health():
    return {"status": "ok"}