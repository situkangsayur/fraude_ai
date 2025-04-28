from fastapi import FastAPI, Depends
from typing import Dict, Any
import httpx
from common.config import MONGODB_URI, MONGODB_DB_NAME
from common.mongodb_utils import get_mongodb_client, get_mongodb_database

app = FastAPI()

async def get_transaction_data(transaction_id: str) -> Dict[str, Any]:
    """
    Retrieves transaction data from a data source (e.g., a database or API).
    This is a placeholder function and should be replaced with actual data retrieval logic.
    """
    # Replace with your actual data retrieval logic
    transaction_data = {
        "id_transaction": transaction_id,
        "id_user": "user123",
        "amount": 100.00,
        "list_of_items": [{"item_name": "Laptop", "price": 900.00, "quantity": 1}]
    }
    return transaction_data

async def call_llm_interface(transaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls the LLM interface to analyze the transaction data.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post("http://llm_interface:8001/analyze", json=transaction_data)
        return response.json()

async def call_graph_service(transaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls the Graph Service to analyze the transaction data.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post("http://graph_service:8002/analyze", json=transaction_data)
        return response.json()

async def call_rules_policy_engine(transaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls the Rules Policy Engine to evaluate the transaction data.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post("http://rules_policy_engine:8003/evaluate", json=transaction_data)
        return response.json()

async def call_neural_net_service(transaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls the Neural Net Service to score the transaction data.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post("http://neural_net_service:8004/score", json=transaction_data)
        return response.json()

@app.get("/fraud_check/{transaction_id}")
async def fraud_check(transaction_id: str):
    """
    Main endpoint to trigger the fraud detection pipeline.
    """
    transaction_data = await get_transaction_data(transaction_id)

    llm_results = await call_llm_interface(transaction_data)
    graph_results = await call_graph_service(transaction_data)
    rules_results = await call_rules_policy_engine(transaction_data)
    neural_net_results = await call_neural_net_service(transaction_data)

    # Aggregate and score the results from all the microservices
    fraud_score = (
        llm_results.get("fraud_score", 0) +
        graph_results.get("proximity_score", 0) +
        rules_results.get("risk_points", 0) +
        neural_net_results.get("fraud_score", 0)
    )

    return {
        "transaction_id": transaction_id,
        "fraud_score": fraud_score,
        "llm_results": llm_results,
        "graph_results": graph_results,
        "rules_results": rules_results,
        "neural_net_results": neural_net_results,
    }

@app.get("/health")
async def health_check():
   return {"status": "ok"}
# --- API Endpoints for Policy Management ---
@app.get("/policies/")
async def list_policies():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://rules_policy_engine:8003/policies/")
        return response.json()

@app.get("/policies/{policy_id}")
async def read_policy(policy_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://rules_policy_engine:8003/policies/{policy_id}")
        return response.json()

# Add more endpoints for creating, updating, and deleting policies
@app.post("/policies/")
async def create_policy(policy_data: Dict[str, Any]):
    async with httpx.AsyncClient() as client:
        response = await client.post("http://rules_policy_engine:8003/policies/", json=policy_data)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()

@app.put("/policies/{policy_id}")
async def update_policy(policy_id: str, policy_data: Dict[str, Any]):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"http://rules_policy_engine:8003/policies/{policy_id}", json=policy_data)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()

@app.delete("/policies/{policy_id}")
async def delete_policy(policy_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"http://rules_policy_engine:8003/policies/{policy_id}")
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()

@app.post("/transactions")
async def process_transaction(transaction_data: Dict[str, Any]):
    async with httpx.AsyncClient() as client:
        response = await client.post("http://rules_policy_engine:8003/transactions", json=transaction_data)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()

# --- API Endpoints for Rule Management ---
@app.post("/standard_rules/")
async def create_standard_rule(rule_data: Dict[str, Any]):
    async with httpx.AsyncClient() as client:
        response = await client.post("http://rules_policy_engine:8003/standard_rules/", json=rule_data)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()

@app.get("/standard_rules/{rule_id}")
async def read_standard_rule(rule_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://rules_policy_engine:8003/standard_rules/{rule_id}")
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()

@app.put("/standard_rules/{rule_id}")
async def update_standard_rule(rule_id: str, rule_data: Dict[str, Any]):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"http://rules_policy_engine:8003/standard_rules/{rule_id}", json=rule_data)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()

@app.delete("/standard_rules/{rule_id}")
async def delete_standard_rule(rule_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"http://rules_policy_engine:8003/standard_rules/{rule_id}")
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()

@app.post("/velocity_rules/")
async def create_velocity_rule(rule_data: Dict[str, Any]):
    async with httpx.AsyncClient() as client:
        response = await client.post("http://rules_policy_engine:8003/velocity_rules/", json=rule_data)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()

@app.get("/velocity_rules/{rule_id}")
async def read_velocity_rule(rule_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://rules_policy_engine:8003/velocity_rules/{rule_id}")
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()

@app.put("/velocity_rules/{rule_id}")
async def update_velocity_rule(rule_id: str, rule_data: Dict[str, Any]):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"http://rules_policy_engine:8003/velocity_rules/{rule_id}", json=rule_data)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()

@app.delete("/velocity_rules/{rule_id}")
async def delete_velocity_rule(rule_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"http://rules_policy_engine:8003/velocity_rules/{rule_id}")
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()


# --- API Endpoints for Graph Management ---
@app.get("/graph_rules/")
async def list_graph_rules():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://graph_service:8002/graph_rules/")
        return response.json()

@app.get("/nodes/")
async def list_nodes():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://graph_service:8002/nodes/")
        return response.json()

# Add more endpoints for creating, updating, and deleting graph rules and nodes