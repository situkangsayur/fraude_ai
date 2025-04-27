from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from common.config import MONGODB_URI, MONGODB_DB_NAME
from common.mongodb_utils import get_mongodb_client, get_mongodb_database
# Import RuleType
from .models import Policy, StandardRule, VelocityRule, Transaction, RuleType
from .services import evaluate_policy, determine_risk_level

policy_router = APIRouter()
rule_router = APIRouter()


@policy_router.post("/policies/", response_model=Dict[str, Any])
# Use Depends for database injection
async def create_policy(policy: Policy, db: Any = Depends(get_mongodb_database)):
    """Creates a new fraud detection policy."""
    try:
        print("Creating policy...")
        # db is now injected via Depends

        # Basic check if db injection worked (optional, Depends should handle errors)
        if db is None:
             print("Failed to get MongoDB database via Depends")
             raise HTTPException(status_code=500, detail="Internal server error: Database connection failed")

        policy_data = policy.model_dump()
        print(f"Policy data: {policy_data}")
        # Insert the policy itself
        result = db.policies.insert_one(policy_data)
        policy_id = result.inserted_id

        # Check if the policy has any rules
        if not policy.rules:
            raise HTTPException(status_code=422, detail="Policy must have at least one rule")

        # Insert the rules into their respective collections
        for rule in policy.rules:
            rule_data = rule.model_dump()
            print(f"Rule data: {rule_data}")
            # Compare with Enum member
            if rule.rule_type == RuleType.STANDARD:
                # Ensure collection name matches if needed, e.g., db[RuleType.STANDARD.value + "_rule"]
                db.standard_rule.insert_one(rule_data)
            # Compare with Enum member
            elif rule.rule_type == RuleType.VELOCITY:
                db.velocity_rule.insert_one(rule_data)

        new_policy = db.policies.find_one({"_id": policy_id})
        print(f"New policy: {new_policy}")
        new_policy["_id"] = str(new_policy["_id"])
        return new_policy
    except HTTPException as http_exc:
        # Re-raise HTTPException to preserve the original status code and detail
        raise http_exc
    except Exception as e:
        # Catch other unexpected errors
        print(f"Unexpected Exception in create_policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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

        # Use model_dump() instead of dict()
        policy_data = policy.model_dump()
        # Consider excluding unset fields if needed: policy.model_dump(exclude_unset=True)
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
async def process_transaction(transaction: Transaction, mock_db=None) -> Dict[str, Any]:
    """
    Processes a transaction, evaluates it against the defined policies,
    and updates the user's average risk score.
    """
    try:
        if mock_db:
            client = mock_db.client
            db = mock_db
        else:
            client = get_mongodb_client(MONGODB_URI, mock_db)
            if not client:
                raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")
            db = get_mongodb_database(client, MONGODB_DB_NAME)
            if db is None:
                raise HTTPException(status_code=500, detail="Failed to get MongoDB database")

        # Convert transaction to a dict for evaluation
        # Use model_dump() instead of dict()
        transaction_data = transaction.model_dump()

        policies = []
        total_risk_points = 0
        cursor = db.policies.find()
        for policy in cursor:
            total_risk_points += await evaluate_policy(transaction_data, policy)
    
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

        # Use model_dump()
        rule_data = rule.model_dump()
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

        # Use model_dump()
        rule_data = rule.model_dump()
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

        # Use model_dump()
        rule_data = rule.model_dump()
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

        # Use model_dump()
        rule_data = rule.model_dump()
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