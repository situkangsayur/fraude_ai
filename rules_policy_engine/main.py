from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from common.config import MONGODB_URI, MONGODB_DB_NAME
from common.mongodb_utils import get_mongodb_client, get_mongodb_database

app = FastAPI()

class Policy(BaseModel):
    name: str
    description: str
    rules: str

@app.post("/policies/", response_model=Dict[str, Any])
async def create_policy(policy: Policy):
    """
    Creates a new fraud detection policy.
    """
    try:
        client = get_mongodb_client(MONGODB_URI)
        if client is None:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if db is None:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        policy_data = policy.dict()
        result = await db.policies.insert_one(policy_data)
        new_policy = await db.policies.find_one({"_id": result.inserted_id})
        return new_policy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/policies/{policy_id}", response_model=Dict[str, Any])
async def read_policy(policy_id: str):
    """
    Reads a fraud detection policy by ID.
    """
    try:
        client = get_mongodb_client(MONGODB_URI)
        if client is None:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if db is None:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        policy = await db.policies.find_one({"policy_id": policy_id})
        if policy is None:
            raise HTTPException(status_code=404, detail="Policy not found")
        return policy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/policies/{policy_id}", response_model=Dict[str, Any])
async def update_policy(policy_id: str, policy: Policy):
    """
    Updates a fraud detection policy by ID.
    """
    try:
        client = get_mongodb_client(MONGODB_URI)
        if client is None:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if db is None:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        policy_data = policy.dict()
        result = await db.policies.update_one({"policy_id": policy_id}, {"$set": policy_data})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Policy not found")
        updated_policy = await db.policies.find_one({"policy_id": policy_id})
        return updated_policy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/policies/{policy_id}", response_model=Dict[str, Any])
async def delete_policy(policy_id: str):
    """
    Deletes a fraud detection policy by ID.
    """
    try:
        client = get_mongodb_client(MONGODB_URI)
        if client is None:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if db is None:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        result = await db.policies.delete_one({"policy_id": policy_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Policy not found")
        return {"message": "Policy deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate")
async def evaluate_transaction(transaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates a transaction against the defined policies.
    Returns a list of policy IDs that the transaction violates.
    """
    try:
        client = get_mongodb_client(MONGODB_URI)
        if client is None:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if db is None:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        policies = await db.policies.find().to_list(length=None)
        violated_policies = []
        for policy in policies:
            if evaluate_policy(transaction_data, policy):
                violated_policies.append(policy['policy_id'])
        return {"policy_violations": violated_policies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def evaluate_policy(transaction, policy):
    """
    Evaluates a transaction against a single policy.
    Returns True if the transaction violates the policy, False otherwise.
    """
    try:
        # Evaluate the policy rules using a simple eval() function
        # **WARNING:** Using eval() can be dangerous if the policy rules are not carefully controlled.
        # In a production environment, consider using a safer rule engine or a more restricted evaluation method.
        return eval(policy['rules'], {'transaction': transaction})
    except Exception as e:
        print(f"Error evaluating policy {policy['policy_id']}: {e}")
        return False