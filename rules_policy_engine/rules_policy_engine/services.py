from typing import Any
from .models import StandardRule, VelocityRule, Policy, RuleType
from datetime import datetime, timedelta
from pymongo import MongoClient
from common.config import MONGODB_URI, MONGODB_DB_NAME

RISK_FRAUD_THRESHOLD = 100
RISK_SUSPECT_THRESHOLD = 70

def evaluate_standard_rule(transaction, rule: StandardRule) -> bool:
    """Evaluates a standard rule against a transaction."""
    field_value = transaction.get(rule.field)
    if field_value is None:
        return False  # Field not found in transaction

    operator = rule.operator
    value = rule.value

    if operator == "equal":
        return field_value == value
    elif operator == "greater_than":
        return field_value > value
    elif operator == "greater_than_equal":
        return field_value >= value
    elif operator == "lower_than":
        return field_value < value
    elif operator == "lower_than_equal":
        return field_value <= value
    elif operator == "not_equal":
        return field_value != value
    elif operator == "in":
        return field_value in value
    elif operator == "not_in":
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

async def evaluate_velocity_rule(transaction, rule: VelocityRule) -> bool:
    """Evaluates a velocity rule against a transaction."""
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    collection = db.transactions  # Assuming transactions are stored in a 'transactions' collection

    try:
        time_delta = parse_time_range(rule.time_range)
        cutoff_time = datetime.utcnow() - time_delta

        aggregation_function = rule.aggregation_function.lower()

        if aggregation_function not in ["sum", "count", "average"]:
            print(f"Unsupported aggregation function: {aggregation_function}")
            return False

        pipeline = [
            {"$match": {
                "user_id": transaction["user_id"],
                "timestamp": {"$gte": cutoff_time.isoformat()},
            }},
            {"$group": {
                "_id": None,
                "total": {f"${aggregation_function}": f"${rule.field}"}
            }}
        ]

        result = list(await collection.aggregate(pipeline).to_list(length=1))
        if not result:
            aggregated_value = 0  # No transactions found in the time range
        else:
            aggregated_value = result[0]["total"]

        if aggregated_value is None:
            return False

        threshold = rule.threshold

        if aggregated_value > threshold:
            return True
        else:
            return False

    except Exception as e:
        print(f"Error evaluating velocity rule: {e}")
        return False
    finally:
        client.close()

def evaluate_policy(transaction, policy: Policy) -> int:
    """Evaluates a transaction against a policy and returns the total risk points."""
    total_points = 0
    for rule in policy.rules:
        if rule.rule_type == RuleType.STANDARD:
            if evaluate_standard_rule(transaction, rule):
                total_points += rule.points
        elif rule.rule_type == RuleType.VELOCITY:
            if evaluate_velocity_rule(transaction, rule):
                total_points += rule.points
    return total_points

def determine_risk_level(total_risk_points: int) -> str:
    """Determines the risk level based on the total risk points."""
    if total_risk_points >= RISK_FRAUD_THRESHOLD:
        return "fraud_confirm"
    elif total_risk_points >= RISK_SUSPECT_THRESHOLD:
        return "suspect"
    else:
        return "normal"