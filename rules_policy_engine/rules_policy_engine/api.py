from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from common.config import MONGODB_URI, MONGODB_DB_NAME
from common.mongodb_utils import get_mongodb_client, get_mongodb_database
# Import RuleType
from .models import Policy, StandardRule, VelocityRule, Transaction, RuleType
from .services import evaluate_policy, determine_risk_level
from bson.errors import InvalidId

policy_router = APIRouter()
rule_router = APIRouter()


@policy_router.post("/policies/", response_model=Dict[str, Any])
# Use Depends for database injection
async def create_policy(policy: Policy, db: Any = Depends(get_mongodb_database)):
    """Creates a new fraud detection policy."""
    try:
        print("Creating policy...")
        if db is None:
             print("Failed to get MongoDB database via Depends")
             raise HTTPException(status_code=500, detail="Internal server error: Database connection failed")

        # Check if the policy has any rules
        if not policy.rules:
            raise HTTPException(status_code=422, detail="Policy must have at least one rule")

        # Extract rules before inserting the policy
        rules_data = [rule.model_dump() for rule in policy.rules]
        policy_data_without_rules = policy.model_dump(exclude={"rules"})

        # Insert the policy without nested rules
        result = db.policies.insert_one(policy_data_without_rules)
        policy_id = result.inserted_id
        print(f"Policy inserted with id: {policy_id}")

        inserted_rule_ids = []
        # Insert the rules into their respective collections and link them to the policy
        for rule_data in rules_data:
            rule_data["policy_id"] = policy_id # Link rule to policy
            print(f"Inserting rule data: {rule_data}")
            if rule_data["rule_type"] == RuleType.STANDARD.value:
                rule_insert_result = db.standard_rule.insert_one(rule_data)
                inserted_rule_ids.append({"type": RuleType.STANDARD.value, "id": rule_insert_result.inserted_id})
                print(f"Standard rule inserted with id: {rule_insert_result.inserted_id}")
            elif rule_data["rule_type"] == RuleType.VELOCITY.value:
                rule_insert_result = db.velocity_rule.insert_one(rule_data)
                inserted_rule_ids.append({"type": RuleType.VELOCITY.value, "id": rule_insert_result.inserted_id})
                print(f"Velocity rule inserted with id: {rule_insert_result.inserted_id}")

        # Update the policy document to include the ObjectIds of the inserted rules
        db.policies.update_one(
            {"_id": policy_id},
            {"$set": {"rules": inserted_rule_ids}}
        )
        print(f"Policy {policy_id} updated with rule ids: {inserted_rule_ids}")

        # Retrieve the updated policy document
        updated_policy = db.policies.find_one({"_id": policy_id})
        print(f"Retrieved updated policy: {updated_policy}")
        updated_policy["_id"] = str(updated_policy["_id"])

        # Convert rule ObjectIds to strings in the returned policy
        if "rules" in updated_policy:
            for rule_entry in updated_policy["rules"]:
                if "id" in rule_entry:
                    rule_entry["id"] = str(rule_entry["id"])

        return updated_policy

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Unexpected Exception in create_policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@policy_router.get("/policies/{policy_id}", response_model=Dict[str, Any])
async def read_policy(policy_id: str, db: Any = Depends(get_mongodb_database)):
    """Reads a fraud detection policy by ID."""
    try:
        from bson import ObjectId
        policy = db.policies.find_one({"_id": ObjectId(policy_id)})
        if policy is None:
            raise HTTPException(status_code=404, detail="Policy not found")
        # Convert ObjectId to string for response
        policy["_id"] = str(policy["_id"])
        return policy
    except Exception as e:
        # Catching potential BSON invalid ID error
        if isinstance(e, InvalidId) or "invalid id" in str(e).lower():
             raise HTTPException(status_code=404, detail="Policy not found")
        raise HTTPException(status_code=500, detail=str(e))


@policy_router.put("/policies/{policy_id}", response_model=Dict[str, Any])
async def update_policy(policy_id: str, policy: Policy, db: Any = Depends(get_mongodb_database)):
    """Updates a fraud detection policy by ID."""
    try:
        from bson import ObjectId
        # Use model_dump() instead of dict()
        policy_data = policy.model_dump(exclude_unset=True) # Use exclude_unset to only update provided fields
        result = db.policies.update_one({"_id": ObjectId(policy_id)}, {"$set": policy_data})
        if result.modified_count == 0:
            # Check if the policy exists but no changes were made
            existing_policy = db.policies.find_one({"_id": ObjectId(policy_id)})
            if existing_policy:
                 # If exists but no changes, return the existing policy
                 existing_policy["_id"] = str(existing_policy["_id"])
                 return existing_policy
            else:
                 raise HTTPException(status_code=404, detail="Policy not found")

        updated_policy = db.policies.find_one({"_id": ObjectId(policy_id)})
        updated_policy["_id"] = str(updated_policy["_id"])
        return updated_policy
    except Exception as e:
        if isinstance(e, InvalidId) or "invalid id" in str(e).lower():
             raise HTTPException(status_code=404, detail="Policy not found")
        raise HTTPException(status_code=500, detail=str(e))


@policy_router.delete("/policies/{policy_id}", response_model=Dict[str, Any])
async def delete_policy(policy_id: str, db: Any = Depends(get_mongodb_database)):
    """Deletes a fraud detection policy by ID."""
    try:
        from bson import ObjectId
        result = db.policies.delete_one({"_id": ObjectId(policy_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Policy not found")
        return {"message": "Policy deleted successfully"}
    except Exception as e:
        if isinstance(e, InvalidId) or "invalid id" in str(e).lower():
             raise HTTPException(status_code=404, detail="Policy not found")
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
        for policy_data in cursor:
            # Convert rule dictionaries back to Pydantic models
            policy_data["rules"] = [
                StandardRule(**rule) if rule.get("rule_type") == "standard" else VelocityRule(**rule)
                for rule in policy_data.get("rules", [])
            ]
            policy = Policy(**policy_data)
            total_risk_points += await evaluate_policy(transaction_data, policy, db=db)
    
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
async def create_standard_rule(rule: StandardRule, db: Any = Depends(get_mongodb_database)):
    """Creates a new standard rule."""
    try:
        # Use model_dump()
        rule_data = rule.model_dump()
        result = db["standard_rule"].insert_one(rule_data)
        rule_data["_id"] = str(result.inserted_id)
        return rule_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@rule_router.get("/standard_rules/{rule_id}", response_model=Dict[str, Any])
async def read_standard_rule(rule_id: str, db: Any = Depends(get_mongodb_database)):
    """Reads a standard rule by ID."""
    try:
        from bson import ObjectId
        rule = db["standard_rule"].find_one({"_id": ObjectId(rule_id)})
        if rule is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        rule["_id"] = str(rule["_id"])
        return rule
    except Exception as e:
        if isinstance(e, InvalidId) or "invalid id" in str(e).lower():
             raise HTTPException(status_code=404, detail="Rule not found")
        raise HTTPException(status_code=500, detail=str(e))


@rule_router.put("/standard_rules/{rule_id}", response_model=Dict[str, Any])
async def update_standard_rule(rule_id: str, rule: StandardRule, db: Any = Depends(get_mongodb_database)):
    """Updates a standard rule by ID."""
    try:
        from bson import ObjectId
        # Use model_dump()
        rule_data = rule.model_dump(exclude_unset=True)
        result = db["standard_rule"].update_one({"_id": ObjectId(rule_id)}, {"$set": rule_data})
        if result.modified_count == 0:
            existing_rule = db["standard_rule"].find_one({"_id": ObjectId(rule_id)})
            if existing_rule:
                 existing_rule["_id"] = str(existing_rule["_id"])
                 return existing_rule
            else:
                 raise HTTPException(status_code=404, detail="Rule not found")

        updated_rule_doc = db["standard_rule"].find_one({"_id": ObjectId(rule_id)})
        if updated_rule_doc:
            updated_rule_doc["_id"] = str(updated_rule_doc["_id"])
            # Return the fetched dictionary directly
            return updated_rule_doc
        else:
            # This case should ideally not be reached if modified_count > 0, but as a safeguard
            raise HTTPException(status_code=404, detail="Rule not found after update")
    except Exception as e:
        if isinstance(e, InvalidId) or "invalid id" in str(e).lower():
             raise HTTPException(status_code=404, detail="Rule not found")
        raise HTTPException(status_code=500, detail=str(e))


@rule_router.delete("/standard_rules/{rule_id}", response_model=Dict[str, Any])
async def delete_standard_rule(rule_id: str, db: Any = Depends(get_mongodb_database)):
    """Deletes a standard rule by ID."""
    try:
        from bson import ObjectId
        result = db["standard_rule"].delete_one({"_id": ObjectId(rule_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Rule not found")
        return {"message": "Rule deleted successfully"}
    except InvalidId:
         raise HTTPException(status_code=404, detail="Rule not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Velocity Rule CRUD operations
@rule_router.post("/velocity_rules/", response_model=Dict[str, Any])
async def create_velocity_rule(rule: VelocityRule, db: Any = Depends(get_mongodb_database)):
    """Creates a new velocity rule."""
    try:
        # Use model_dump()
        rule_data = rule.model_dump()
        result = db["velocity_rule"].insert_one(rule_data)
        rule_data["_id"] = str(result.inserted_id)
        return rule_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@rule_router.get("/velocity_rules/{rule_id}", response_model=Dict[str, Any])
async def read_velocity_rule(rule_id: str, db: Any = Depends(get_mongodb_database)):
    """Reads a velocity rule by ID."""
    try:
        from bson import ObjectId
        rule = db["velocity_rule"].find_one({"_id": ObjectId(rule_id)})
        if rule is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        rule["_id"] = str(rule["_id"])
        return rule
    except Exception as e:
        if isinstance(e, InvalidId) or "invalid id" in str(e).lower():
             raise HTTPException(status_code=404, detail="Rule not found")
        raise HTTPException(status_code=500, detail=str(e))


@rule_router.put("/velocity_rules/{rule_id}", response_model=Dict[str, Any])
async def update_velocity_rule(rule_id: str, rule: VelocityRule, db: Any = Depends(get_mongodb_database)):
    """Updates a velocity rule by ID."""
    try:
        from bson import ObjectId
        # Use model_dump()
        rule_data = rule.model_dump(exclude_unset=True)
        result = db["velocity_rule"].update_one({"_id": ObjectId(rule_id)}, {"$set": rule_data})
        if result.modified_count == 0:
            existing_rule = db["velocity_rule"].find_one({"_id": ObjectId(rule_id)})
            if existing_rule:
                 existing_rule["_id"] = str(existing_rule["_id"])
                 return existing_rule
            else:
                 raise HTTPException(status_code=404, detail="Rule not found")

        updated_rule_doc = db["velocity_rule"].find_one({"_id": ObjectId(rule_id)})
        if updated_rule_doc:
            updated_rule_doc["_id"] = str(updated_rule_doc["_id"])
            # Return the fetched dictionary directly
            return updated_rule_doc
        else:
            # This case should ideally not be reached if modified_count > 0, but as a safeguard
            raise HTTPException(status_code=404, detail="Rule not found after update")
    except Exception as e:
        if isinstance(e, InvalidId) or "invalid id" in str(e).lower():
             raise HTTPException(status_code=404, detail="Rule not found")
        raise HTTPException(status_code=500, detail=str(e))


@rule_router.delete("/velocity_rules/{rule_id}", response_model=Dict[str, Any])
async def delete_velocity_rule(rule_id: str, db: Any = Depends(get_mongodb_database)):
    """Deletes a velocity rule by ID."""
    try:
        from bson import ObjectId
        result = db["velocity_rule"].delete_one({"_id": ObjectId(rule_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Rule not found")
        return {"message": "Rule deleted successfully"}
    except InvalidId:
         raise HTTPException(status_code=404, detail="Rule not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))