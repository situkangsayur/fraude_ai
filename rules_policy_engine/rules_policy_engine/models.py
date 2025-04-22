from pydantic import BaseModel
from typing import List, Union, Any
from enum import Enum

class RuleType(str, Enum):
    STANDARD = "standard"
    VELOCITY = "velocity"

class BaseRule(BaseModel):
    rule_type: RuleType
    description: str
    points: int

class StandardRule(BaseRule):
    rule_type: RuleType = RuleType.STANDARD
    field: str
    operator: str
    value: Any

class VelocityRule(BaseRule):
    rule_type: RuleType = RuleType.VELOCITY
    field: str
    time_range: str  # e.g., "1 month", "1 week"
    aggregation_function: str  # e.g., "sum", "count", "average"
    threshold: float

class Policy(BaseModel):
    name: str
    description: str
    rules: List[Union[StandardRule, VelocityRule]]

class Transaction(BaseModel):
    user_id: str
    transaction_id: str
    amount: float
    timestamp: str
    # Add other transaction fields as needed