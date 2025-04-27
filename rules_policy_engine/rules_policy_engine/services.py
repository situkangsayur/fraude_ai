from typing import Any
from .models import StandardRule, VelocityRule, Policy, RuleType
from datetime import datetime, timedelta
from pymongo import MongoClient
from common.config import MONGODB_URI, MONGODB_DB_NAME

RISK_FRAUD_THRESHOLD = 100
RISK_SUSPECT_THRESHOLD = 70

def evaluate_standard_rule(transaction: dict, rule_data: dict) -> bool:
    """Evaluates a standard rule dictionary against a transaction dictionary."""
    field = rule_data.get("field")
    operator = rule_data.get("operator")
    value = rule_data.get("value")

    if field is None or operator is None or value is None:
         print(f"Warning: Incomplete standard rule data: {rule_data}")
         return False # Incomplete rule data

    field_value = transaction.get(field)
    if field_value is None:
        # Optionally print a warning if the field is expected but missing
        # print(f"Warning: Field '{field}' not found in transaction: {transaction}")
        return False  # Field not found in transaction

    # Ensure type consistency for comparisons if necessary, especially for numeric types
    # Example: Convert value from rule if field_value is numeric
    # try:
    #     if isinstance(field_value, (int, float)):
    #         value = type(field_value)(value)
    # except (ValueError, TypeError):
    #      print(f"Warning: Type mismatch or conversion error for rule {rule_data} and transaction field {field_value}")
    #      return False

    if operator == "equal":
        return field_value == value
    elif operator == "greater_than":
        # Add explicit type checks/conversions if necessary before comparison
        try:
            # Ensure comparison is valid (e.g., comparing numbers)
            return field_value > value
        except TypeError:
             print(f"Warning: Type mismatch for '>' comparison. Rule: {rule_data}, Tx Value: {field_value}")
             return False
    elif operator == "greater_than_equal":
        try:
            return field_value >= value
        except TypeError:
             print(f"Warning: Type mismatch for '>=' comparison. Rule: {rule_data}, Tx Value: {field_value}")
             return False
    elif operator == "lower_than":
        try:
            return field_value < value
        except TypeError:
             print(f"Warning: Type mismatch for '<' comparison. Rule: {rule_data}, Tx Value: {field_value}")
             return False
    elif operator == "lower_than_equal":
        try:
            return field_value <= value
        except TypeError:
             print(f"Warning: Type mismatch for '<=' comparison. Rule: {rule_data}, Tx Value: {field_value}")
             return False
    elif operator == "not_equal":
        return field_value != value
    elif operator == "in":
        # Ensure value is iterable (list, tuple, set, string) for 'in'/'not in' operators
        if not isinstance(value, (list, tuple, set, str)):
             print(f"Warning: 'in' operator requires an iterable value in rule: {rule_data}")
             return False
        return field_value in value
    elif operator == "not_in":
        if not isinstance(value, (list, tuple, set, str)):
             print(f"Warning: 'not in' operator requires an iterable value in rule: {rule_data}")
             return False
        return field_value not in value
    else:
        print(f"Unknown operator: {operator}")
        return False

def parse_time_range(time_range: str) -> timedelta:
    """Parses a time range string (e.g., "1 month", "1 week") into a timedelta."""
    parts = time_range.split()
    if len(parts) != 2:
        raise ValueError("Invalid time range format")

    value = int(parts[0])
    unit = parts[1].lower()

    if unit == "month" or unit == "months":
        return timedelta(days=value * 30)  # Approximate
    elif unit == "week" or unit == "weeks":
        return timedelta(days=value * 7)
    elif unit == "day" or unit == "days":
        return timedelta(days=value)
    elif unit == "hour" or unit == "hours":
        return timedelta(hours=value)
    else:
        raise ValueError("Invalid time unit")

async def evaluate_velocity_rule(transaction: dict, rule_data: dict, db: Any = None) -> bool:
    """Evaluates a velocity rule dictionary against a transaction dictionary."""
    # Extract necessary fields from rule_data
    time_range_str = rule_data.get("time_range")
    aggregation_function = rule_data.get("aggregation_function", "").lower()
    field_to_aggregate = rule_data.get("field") # Field like 'amount' or '*' for count
    threshold = rule_data.get("threshold")

    # Validate required rule fields
    if not all([time_range_str, aggregation_function, field_to_aggregate, threshold is not None]):
        print(f"Warning: Incomplete velocity rule data: {rule_data}")
        return False

    # Validate aggregation function
    valid_aggregations = ["sum", "count", "average"] # 'count' might need special handling
    if aggregation_function not in valid_aggregations:
        print(f"Unsupported aggregation function: {aggregation_function}")
        return False

    # Get DB connection (Consider dependency injection or a shared client)
    # Using a new client per call is inefficient
    if db is None:
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_DB_NAME]
    else:
        client = None # No need to close client if it was passed in

    collection = db.transactions # Assuming transactions are stored here

    try:
        time_delta = parse_time_range(time_range_str)
        cutoff_time = datetime.utcnow() - time_delta # Consider timezone awareness

        # --- Build Aggregation Pipeline ---
        match_stage = {
            "user_id": transaction.get("user_id"), # Use .get() for safety
            # Assuming transaction timestamp field is named 'timestamp' and is a datetime object or ISO string
            "timestamp": {"$gte": cutoff_time} # Use datetime object directly if possible
        }

        group_stage = {"_id": None} # Group all matched documents for the user

        # Determine the aggregation operation
        if aggregation_function == "count":
            # For count, we sum 1 for each document
            group_stage["aggregated_value"] = {"$sum": 1}
        elif field_to_aggregate == "*": # Handle count case if field is '*'
             group_stage["aggregated_value"] = {"$sum": 1}
        else:
            # For sum/average, specify the field from the transaction document
            group_stage["aggregated_value"] = {f"${aggregation_function}": f"${field_to_aggregate}"}


        pipeline = [
            {"$match": match_stage},
            {"$group": group_stage}
        ]
        # print(f"Velocity rule pipeline: {pipeline}") # Debugging

        # Execute aggregation (ensure collection.aggregate is awaited if using async driver like motor)
        # Note: MongoClient from pymongo is synchronous. If async is needed, use Motor.
        # For now, assuming pymongo and synchronous execution within the async function.
        # If Motor is used elsewhere, this needs adjustment.
        result_cursor = collection.aggregate(pipeline)
        result = list(result_cursor) # Evaluate the cursor

        # print(f"Velocity rule result: {result}") # Debugging

        if not result:
            aggregated_value = 0  # No matching transactions found
        else:
            # Handle potential None if the field didn't exist in any doc for sum/avg
            aggregated_value = result[0].get("aggregated_value", 0) or 0


        # print(f"Aggregated value: {aggregated_value}, Threshold: {threshold}") # Debugging

        # Compare with threshold (ensure types are compatible)
        try:
            if aggregated_value > threshold:
                return True
        except TypeError:
            print(f"Warning: Type mismatch comparing aggregated value and threshold. Agg: {aggregated_value}, Thr: {threshold}")
            return False
        else:
            return False

    except Exception as e:
        print(f"Error evaluating velocity rule: {e}")
        return False
    finally:
        if client: # Only close client if it was created in this function
            client.close()

async def evaluate_policy(transaction, policy: Policy, db: Any = None) -> int:
    """Evaluates a transaction against a policy and returns the total risk points."""
    total_points = 0
    # Iterate through the rules list directly from the Policy object
    for rule in policy.rules:
        # Check the type of the rule object
        if isinstance(rule, StandardRule):
            # Pass the rule object and transaction dictionary
            if evaluate_standard_rule(transaction, rule.model_dump()):
                total_points += rule.risk_point
        elif isinstance(rule, VelocityRule):
            # Pass the rule object, transaction dictionary, and db connection
            if await evaluate_velocity_rule(transaction, rule.model_dump(), db=db):
                total_points += rule.risk_point
    return total_points

def determine_risk_level(total_risk_points: int) -> str:
    """Determines the risk level based on the total risk points."""
    if total_risk_points >= RISK_FRAUD_THRESHOLD:
        return "fraud_confirm"
    elif total_risk_points >= RISK_SUSPECT_THRESHOLD:
        return "suspect"
    else:
        return "normal"