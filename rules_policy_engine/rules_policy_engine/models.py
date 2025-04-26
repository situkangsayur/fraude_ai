from pydantic import BaseModel, validator
from typing import List, Union, Any
from enum import Enum

class RuleType(str, Enum):
    STANDARD = "standard"
    VELOCITY = "velocity"

class BaseRule(BaseModel):
    rule_type: RuleType
    description: str
    risk_point: int

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
    transaction_type: str

    @validator("amount")
    def amount_must_be_positive(cls, amount):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        return amount

    @validator("transaction_type")
    def transaction_type_must_be_valid(cls, transaction_type):
        allowed_transaction_types = ["deposit", "withdrawal", "transfer"]
        if transaction_type not in allowed_transaction_types:
            raise ValueError(f"Transaction type must be one of {allowed_transaction_types}")
        return transaction_type
    # Add other transaction fields as needed