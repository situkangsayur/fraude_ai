from fastapi import HTTPException
from typing import Dict, Any
from bson.objectid import ObjectId

from ..models import GraphRule
from ..services import db

def apply_graph_rule(user1, user2, rule):
    """
    Applies a graph rule to two users and returns True if the rule is satisfied, False otherwise.
    """
    field1_value = user1.get(rule['field1'])
    field2_value = user2.get(rule['field2']) if rule.get('field2') else rule.get('value')

    if field1_value is None or field2_value is None:
        return False

    operator = rule['operator']

    if operator == "equal":
        return str(field1_value) == str(field2_value) # Compare as strings for flexibility
    elif operator == "greater_than":
        try:
            return float(field1_value) > float(field2_value)
        except (ValueError, TypeError):
            return False # Cannot compare non-numeric values
    elif operator == "lower_than":
        try:
            return float(field1_value) < float(field2_value)
        except (ValueError, TypeError):
            return False # Cannot compare non-numeric values
    elif operator == "contains":
        return str(field2_value) in str(field1_value) # Check if value is a substring of field1

    return False

def apply_graph_rule_single(data, rule):
    """
    Applies a graph rule to a single data object (user or transaction) and returns True if the rule is satisfied.
    """
    field1_value = data.get(rule['field1'])
    value_to_compare = rule.get('value')

    if field1_value is None or value_to_compare is None:
        return False

    operator = rule['operator']

    if operator == "equal":
        return str(field1_value) == str(value_to_compare)
    elif operator == "greater_than":
        try:
            return float(field1_value) > float(value_to_compare)
        except (ValueError, TypeError):
            return False
    elif operator == "lower_than":
        try:
            return float(field1_value) < float(value_to_compare)
        except (ValueError, TypeError):
            return False
    elif operator == "contains":
        return str(value_to_compare) in str(field1_value)

    return False

async def create_graph_rule_service(rule: GraphRule, db) -> Dict[str, Any]:
    """
    Creates a new graph rule in MongoDB.
    """
    rule_data = rule.model_dump(by_alias=True) # Use by_alias=True
    result = db.graph_rules.insert_one(rule_data)
    new_rule = db.graph_rules.find_one({"_id": result.inserted_id})
    # Convert ObjectId to string for response and rename _id to id
    if new_rule and '_id' in new_rule:
        new_rule['id'] = str(new_rule.pop('_id'))
    return new_rule

async def read_graph_rule_service(rule_id: str, db) -> Dict[str, Any]:
    """
    Reads a graph rule by ID from MongoDB.
    """
    # Check if rule_id is a valid ObjectId format first
    if not ObjectId.is_valid(rule_id):
        raise HTTPException(status_code=400, detail="Invalid rule ID format")

    rule_object_id = ObjectId(rule_id)
    rule = db.graph_rules.find_one({"_id": rule_object_id})
    if rule is None:
        raise HTTPException(status_code=404, detail="Graph rule not found")
    # Convert ObjectId to string for response and rename _id to id
    if rule and '_id' in rule:
        rule['id'] = str(rule.pop('_id'))
    return rule


async def update_graph_rule_service(rule_id: str, rule: GraphRule) -> Dict[str, Any]:
    """
    Updates a graph rule by ID in MongoDB.
    """
    # Check if rule_id is a valid ObjectId format first
    if not ObjectId.is_valid(rule_id):
        raise HTTPException(status_code=400, detail="Invalid rule ID format")

    rule_object_id = ObjectId(rule_id)
    rule_data = rule.model_dump(by_alias=True, exclude_unset=True) # Use by_alias=True and exclude_unset=True
    rule_data.pop("id", None) # Remove id from rule_data to prevent updating _id
    result = db.graph_rules.update_one({"_id": rule_object_id}, {"$set": rule_data})
    if result.modified_count == 0:
        # Check if the rule exists with the given ID but no changes were made
        rule_exists = db.graph_rules.find_one({"_id": rule_object_id})
        if rule_exists is None:
            raise HTTPException(status_code=404, detail="Graph rule not found")
        # If rule exists but no changes, return the existing rule
        updated_rule = db.graph_rules.find_one({"_id": rule_object_id})
    else:
        updated_rule = db.graph_rules.find_one({"_id": rule_object_id}) # Fetch the updated document

    # Convert ObjectId to string for response and rename _id to id
    if updated_rule and '_id' in updated_rule:
        updated_rule['id'] = str(updated_rule.pop('_id'))
    return updated_rule

async def delete_graph_rule_service(rule_id: str) -> Dict[str, Any]:
    """
    Deletes a graph rule by ID from MongoDB.
    """
    # Check if rule_id is a valid ObjectId format first
    if not ObjectId.is_valid(rule_id):
        raise HTTPException(status_code=400, detail="Invalid rule ID format")

    rule_object_id = ObjectId(rule_id)
    result = db.graph_rules.delete_one({"_id": rule_object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Graph rule not found")
    # Also remove any links created by this rule
    db.links.delete_many({"rule_ids": rule_id}) # Assuming rule_ids is a list
    # Need to rebuild the graph or remove edges from the graph based on the deleted rule
    # For simplicity, we'll just return success here. Rebuilding the graph on rule deletion might be complex.
    return {"message": "Graph rule deleted successfully"}