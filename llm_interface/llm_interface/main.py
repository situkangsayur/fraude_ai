from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from common.config import MONGODB_URI, MONGODB_DB_NAME, LLM_MODEL_NAME
from common.mongodb_utils import get_mongodb_client, get_mongodb_database
from langchain.llms import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

app = FastAPI()

class AnalysisRequest(BaseModel):
    transaction_data: Dict[str, Any]

@app.post("/analyze")
async def analyze_transaction(request: AnalysisRequest) -> Dict[str, Any]:
    """
    Analyzes the transaction data using an LLM and RAG.
    """
    try:
        # Load the LLM model
        model_name = LLM_MODEL_NAME
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)

        pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
        llm = HuggingFacePipeline(pipeline=pipe)

        # Prepare the prompt for the LLM
        prompt = f"Analyze the following transaction data for fraud:\n{request.transaction_data}\n\nConsider UU PDP, ISO standards, and existing fraud rules. Provide a fraud score and a justification."

        # Run the LLM and get the response
        llm_response = llm(prompt)

        # Extract the fraud score and justification from the LLM response
        fraud_score = 0.5  # Replace with actual fraud score extraction logic
        justification = llm_response  # Replace with actual justification extraction logic

        return {
            "fraud_score": fraud_score,
            "justification": justification,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}