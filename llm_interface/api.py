from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from llm_interface.llm_core import load_llm, analyze_transaction_data

app = FastAPI()

class AnalysisRequest(BaseModel):
    transaction_data: Dict[str, Any]

@app.post("/analyze")
async def analyze_transaction(request: AnalysisRequest) -> Dict[str, Any]:
    """
    Analyzes the transaction data using an LLM.
    """
    try:
        llm = load_llm()
        llm_response = analyze_transaction_data(request.transaction_data, llm)

        # Extract the fraud score and justification from the LLM response
        fraud_score = 0.5  # Replace with actual fraud score extraction logic
        justification = llm_response  # Replace with actual justification extraction logic

        return {
            "fraud_score": fraud_score,
            "justification": justification,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))