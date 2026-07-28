from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
import pandas as pd
import os
import json
from dotenv import load_dotenv

load_dotenv()

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
    elif os.environ.get("K_SERVICE"): 
        # Only use Vertex AI fallback if we are on Google Cloud Run
        gemini_client = genai.Client(vertexai=True, project="data-intelligence-tool", location="us-central1")
    else:
        gemini_client = None
except Exception as e:
    gemini_client = None
    print(f"Warning: Gemini Client could not be initialized: {e}")

import pyarrow.dataset as ds

# --- REMOVED GLOBAL CACHING TO PREVENT OOM ---

class NetworkResponse(BaseModel):
    device_id: str
    network_data: dict
    ai_summary: str

@app.get("/")
async def root():
    return {"status": "Sentinel API is running!", "docs": "Visit /docs for the API documentation."}

@app.get("/api/investigate/{device_id}", response_model=NetworkResponse)
async def investigate_network(device_id: str):
    # --- MEMORY-EFFICIENT DATA LOADING WITH PYARROW ---
    try:
        # Query the parquet files directly without loading them entirely into memory
        dataset_threats = ds.dataset("../data/processed_threat_networks.parquet", format="parquet")
        table_threats = dataset_threats.to_table(filter=ds.field("device_id") == device_id)
        device_record = table_threats.to_pandas()
        
        dataset_raw = ds.dataset("../data/raw_transactions", format="parquet")
        table_raw = dataset_raw.to_table(filter=ds.field("device_id") == device_id)
        device_txns = table_raw.to_pandas().head(15)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error reading dataset: {str(e)}"
        )

    if device_record.empty:
        raise HTTPException(status_code=404, detail="Device ID not flagged in the threat network.")
        
    record = device_record.iloc[0]

    # Format the data to match what the React frontend expects
    data = {
        "risk_score": int(record['risk_score']),
        "total_accounts": int(record['unique_users_count']),
        "total_value_at_risk": float(record['total_value_at_risk']),
        "connected_ips": list(record['connected_ips']),
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
