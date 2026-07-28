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
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
THREATS_PATH = os.path.join(DATA_DIR, "processed_threat_networks.parquet")
TXNS_PATH = os.path.join(DATA_DIR, "raw_transactions", "**", "*.parquet")

@app.get("/api/investigate/{device_id}", response_model=NetworkResponse)
async def investigate_network(device_id: str):
    try:
        # Fetch the threat record
        threats_query = f"SELECT * FROM '{THREATS_PATH}' WHERE device_id = '{device_id}'"
        device_record = duckdb.query(threats_query).df()
        
        if device_record.empty:
            raise HTTPException(status_code=404, detail="Device ID not flagged in the threat network.")
            
        record = device_record.iloc[0]
        
        # Fetch up to 15 transactions
        txns_query = f"SELECT * FROM '{TXNS_PATH}' WHERE device_id = '{device_id}' LIMIT 15"
        device_txns = duckdb.query(txns_query).df()
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, 
            detail=f"Error reading dataset via DuckDB: {str(e)}"
        )
    
    # Parse connected_ips since parquet arrays become pandas arrays/lists
    try:
        connected_ips = list(record['connected_ips'])
    except:
        connected_ips = []

    # Format the data to match what the React frontend expects
    data = {
        "risk_score": int(record['risk_score']),
        "total_accounts": int(record['unique_users_count']),
        "total_value_at_risk": float(record['total_value_at_risk']),
        "connected_ips": connected_ips,
        "transactions": [
            {
                "txn_id": row['transaction_id'], 
                "user_id": row['user_id'], 
                "amount": float(row['cart_value']), 
                "status": "flagged" if row['is_fraud_flag'] == 1 else "cleared"
            }
            for _, row in device_txns.iterrows()
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
