from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
import duckdb
import os
import json

app = FastAPI(title="Sentinel Ad-Hoc API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    if os.environ.get("GEMINI_API_KEY"):
        gemini_client = genai.Client()
    elif os.environ.get("K_SERVICE") or os.environ.get("VERCEL"): 
        # Fallback to Vertex AI if running on Cloud Run or Vercel (if properly configured)
        gemini_client = genai.Client(vertexai=True, project="data-intelligence-tool", location="us-central1")
    else:
        gemini_client = None
except Exception as e:
    gemini_client = None
    print(f"Warning: Gemini Client could not be initialized: {e}")

class NetworkResponse(BaseModel):
    device_id: str
    network_data: dict
    ai_summary: str

# Resolve paths correctly for Vercel
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
THREATS_PATH = os.path.join(DATA_DIR, "processed_threat_networks.parquet")
TXNS_PATH = os.path.join(DATA_DIR, "raw_transactions", "**", "*.parquet")

@app.get("/api/investigate/{device_id}", response_model=NetworkResponse)
async def investigate_network(device_id: str):
    try:
        # Fetch the threat record
        threats_query = f"SELECT * FROM '{THREATS_PATH}' WHERE device_id = '{device_id}'"
        res = duckdb.query(threats_query)
        cols = [x[0] for x in res.description]
        rows = res.fetchall()
        
        if not rows:
            raise HTTPException(status_code=404, detail="Device ID not flagged in the threat network.")
            
        record = dict(zip(cols, rows[0]))
        
        # Fetch up to 15 transactions
        txns_query = f"SELECT * FROM '{TXNS_PATH}' WHERE device_id = '{device_id}' LIMIT 15"
        res2 = duckdb.query(txns_query)
        cols2 = [x[0] for x in res2.description]
        device_txns = [dict(zip(cols2, row)) for row in res2.fetchall()]
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, 
            detail=f"Error reading dataset via DuckDB: {str(e)}"
        )
    
    # Format the data to match what the React frontend expects
    data = {
        "risk_score": int(record['risk_score']),
        "total_accounts": int(record['unique_users_count']),
        "total_value_at_risk": float(record['total_value_at_risk']),
        "connected_ips": record.get('connected_ips', []),
        "transactions": [
            {
                "txn_id": row['transaction_id'], 
                "user_id": row['user_id'], 
                "amount": float(row['cart_value']), 
                "status": "flagged" if row['is_fraud_flag'] == 1 else "cleared"
            }
            for row in device_txns
        ]
    }

    # --- GEMINI AI SUMMARIZATION ---
    ai_summary = "AI summarization unavailable. Please set GEMINI_API_KEY."
    
    if gemini_client:
        prompt = f"""
        You are an expert fraud analyst. Review the following JSON data representing a detected e-commerce fraud ring.
        Write a concise, high-urgency 3-sentence summary of the threat level, the number of connected accounts, 
        and the total financial exposure. Tell the analyst whether they should block this network immediately.
        
        Data: {json.dumps(data)}
        """
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            ai_summary = response.text
        except Exception as e:
            ai_summary = f"Error generating summary: {str(e)}"

    return {
        "device_id": device_id,
        "network_data": data,
        "ai_summary": ai_summary
    }

@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "DuckDB Vercel Backend Running"}
