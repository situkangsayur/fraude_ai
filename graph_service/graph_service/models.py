from pydantic import BaseModel
from typing import Optional, List

class UserNode(BaseModel):
    id_user: str
    nama_lengkap: str
    email: str
    domain_email: str
    address: str
    address_zip: str
    address_city: str
    address_province: str
    address_kecamatan: str
    phone_number: str
    is_fraud: bool = False

class GraphRule(BaseModel):
    name: str
    description: str
    field1: str
    operator: str  # e.g., "equal", "greater_than", "contains"
    field2: Optional[str] = None  # Optional, for comparing two fields
    value: Optional[str] = None  # Optional, for comparing with a fixed value

class Link(BaseModel):
    source: str
    target: str
    type: str
    weight: float = 1.0
    reasons: List[str] = []
    rule_ids: List[str] = []