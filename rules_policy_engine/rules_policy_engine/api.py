from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from common.config import MONGODB_URI, MONGODB_DB_NAME
from common.mongodb_utils import get_mongodb_client, get_mongodb_database
from .models import Policy, StandardRule, VelocityRule, Transaction
from .services import evaluate_policy, determine_risk_level

policy_router = APIRouter()
rule_router = APIRouter()

@policy_router.post("/policies/", response_model=Dict[str, Any])
async def create_policy(policy: Policy):
    """Creates a new fraud detection policy."""
    try:
        client = get_mongodb_client(MONGODB_URI)
        if not client:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if not db:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        policy_data = policy.dict()
        # Insert the policy itself
        result = await db.policies.insert_one(policy_data)
        policy_id = result.inserted_id

        # Insert the rules into their respective collections
        for rule in policy.rules:
            rule_data = rule.dict()
            if rule.rule_type == "standard":
                await db.standard_rule.insert_one(rule_data)
            elif rule.rule_type == "velocity":
                await db.velocity_rule.insert_one(rule_data)

        new_policy = await db.policies.find_one({"_id": policy_id})
        return new_policy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@policy_router.get("/policies/{policy_id}", response_model=Dict[str, Any])
async def read_policy(policy_id: str):
    """Reads a fraud detection policy by ID."""
    try:
        client = get_mongodb_client(MONGODB_URI)
        if not client:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if not db:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        policy = await db.policies.find_one({"_id": policy_id})
        if policy is None:
            raise HTTPException(status_code=404, detail="Policy not found")
        return policy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@policy_router.put("/policies/{policy_id}", response_model=Dict[str, Any])
async def update_policy(policy_id: str, policy: Policy):
    """Updates a fraud detection policy by ID."""
    try:
        client = get_mongodb_client(MONGODB_URI)
        if not client:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if not db:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        policy_data = policy.dict()
        result = await db.policies.update_one({"_id": policy_id}, {"$set": policy_data})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Policy not found")
        updated_policy = await db.policies.find_one({"_id": policy_id})
        return updated_policy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@policy_router.delete("/policies/{policy_id}", response_model=Dict[str, Any])
async def delete_policy(policy_id: str):
    """Deletes a fraud detection policy by ID."""
    try:
        client = get_mongodb_client(MONGODB_URI)
        if not client:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if not db:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        result = await db.policies.delete_one({"_id": policy_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Policy not found")
        return {"message": "Policy deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@policy_router.post("/transactions")
async def process_transaction(transaction: Transaction) -> Dict[str, Any]:
    """
    Processes a transaction, evaluates it against the defined policies,
    and updates the user's average risk score.
    """
    try:
        client = get_mongodb_client(MONGODB_URI)
        if not client:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if not db:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        # Convert transaction to a dict for evaluation
        transaction_data = transaction.dict()

        policies = await db.policies.find().to_list(length=None)
        total_risk_points = 0
        for policy in policies:
            total_risk_points += evaluate_policy(transaction_data, policy)

        # Determine risk level
        risk_level = determine_risk_level(total_risk_points)

        # Update user's average score (placeholder)
        # In a real implementation, you would retrieve the user's existing
        # average score, update it with the new transaction's score, and
        # save it back to the database.
        print(f"Transaction {transaction.transaction_id} for user {transaction.user_id} has risk level: {risk_level} (points: {total_risk_points})")

        return {
            "transaction_id": transaction.transaction_id,
            "user_id": transaction.user_id,
            "risk_points": total_risk_points,
            "risk_level": risk_level
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@rule_router.get("/rule_statistics/", response_model=Dict[str, Any])
async def get_rule_statistics():
    """
    Retrieves statistics about how the rules affect transactions.
    """
    try:
        client = get_mongodb_client(MONGODB_URI)
        if not client:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if not db:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        # This is a placeholder; the actual implementation would involve
        # querying the database to count how many transactions each rule
        # has affected.
        print("Rule statistics API not implemented yet.")
        return {"message": "Rule statistics API not implemented yet."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@rule_router.get("/users/{user_id}/risk_info", response_model=Dict[str, Any])
async def get_user_risk_info(user_id: str):
    """
    Retrieves risk information for a specific user account.
    """
    try:
        client = get_mongodb_client(MONGODB_URI)
        if not client:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if not db:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        # This is a placeholder; the actual implementation would involve
        # querying the database to retrieve the user's risk points,
        # top affecting rules, and latest transactions.
        print(f"User risk info API not implemented yet for user: {user_id}")
        return {"message": f"User risk info API not implemented yet for user: {user_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Standard Rule CRUD operations
@rule_router.post("/standard_rules/", response_model=Dict[str, Any])
async def create_standard_rule(rule: StandardRule):
    """Creates a new standard rule."""
    try:
        client = get_mongodb_client(MONGODB_URI)
        if not client:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if not db:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        rule_data = rule.dict()
        result = await db.standard_rule.insert_one(rule_data)
        new_rule = await db.standard_rule.find_one({"_id": result.inserted_id})
        return new_rule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@rule_router.get("/standard_rules/{rule_id}", response_model=Dict[str, Any])
async def read_standard_rule(rule_id: str):
    """Reads a standard rule by ID."""
    try:
        client = get_mongodb_client(MONGODB_URI)
        if not client:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if not db:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        rule = await db.standard_rule.find_one({"_id": rule_id})
        if rule is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        return rule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@rule_router.put("/standard_rules/{rule_id}", response_model=Dict[str, Any])
async def update_standard_rule(rule_id: str, rule: StandardRule):
    """Updates a standard rule by ID."""
    try:
        client = get_mongodb_client(MONGODB_URI)
        if not client:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if not db:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        rule_data = rule.dict()
        result = await db.standard_rule.update_one({"_id": rule_id}, {"$set": rule_data})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Rule not found")
        updated_rule = await db.standard_rule.find_one({"_id": rule_id})
        return updated_rule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@rule_router.delete("/standard_rules/{rule_id}", response_model=Dict[str, Any])
async def delete_standard_rule(rule_id: str):
    """Deletes a standard rule by ID."""
    try:
        client = get_mongodb_client(MONGODB_URI)
        if not client:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if not db:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        result = await db.standard_rule.delete_one({"_id": rule_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Rule not found")
        return {"message": "Rule deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Velocity Rule CRUD operations
@rule_router.post("/velocity_rules/", response_model=Dict[str, Any])
async def create_velocity_rule(rule: VelocityRule):
    """Creates a new velocity rule."""
    try:
        client = get_mongodb_client(MONGODB_URI)
        if not client:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if not db:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        rule_data = rule.dict()
        result = await db.velocity_rule.insert_one(rule_data)
        new_rule = await db.velocity_rule.find_one({"_id": result.inserted_id})
        return new_rule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@rule_router.get("/velocity_rules/{rule_id}", response_model=Dict[str, Any])
async def read_velocity_rule(rule_id: str):
    """Reads a velocity rule by ID."""
    try:
        client = get_mongodb_client(MONGODB_URI)
        if not client:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if not db:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        rule = await db.velocity_rule.find_one({"_id": rule_id})
        if rule is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        return rule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@rule_router.put("/velocity_rules/{rule_id}", response_model=Dict[str, Any])
async def update_velocity_rule(rule_id: str, rule: VelocityRule):
    """Updates a velocity rule by ID."""
    try:
        client = get_mongodb_client(MONGODB_URI)
        if not client:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if not db:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        rule_data = rule.dict()
        result = await db.velocity_rule.update_one({"_id": rule_id}, {"$set": rule_data})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Rule not found")
        updated_rule = await db.velocity_rule.find_one({"_id": rule_id})
        return updated_rule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@rule_router.delete("/velocity_rules/{rule_id}", response_model=Dict[str, Any])
async def delete_velocity_rule(rule_id: str):
    """Deletes a velocity rule by ID."""
    try:
        client = get_mongodb_client(MONGODB_URI)
        if not client:
            raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
        db = get_mongodb_database(client, MONGODB_DB_NAME)
        if not db:
            raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        result = await db.velocity_rule.delete_one({"_id": rule_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Rule not found")
        return {"message": "Rule deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))