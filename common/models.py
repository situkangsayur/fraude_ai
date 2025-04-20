from pydantic import BaseModel
from typing import List, Optional

class User(BaseModel):
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

class Transaction(BaseModel):
    id_transaction: str
    id_user: str
    shipzip: str
    shipping_address: str
    shipping_city: str
    shipping_province: str
    shipping_kecamatan: str
    payment_type: str
    number: str
    bank_name: Optional[str]
    amount: float
    status: str
    billing_address: str
    billing_city: str
    billing_province: str
    billing_kecamatan: str
    list_of_items: List[dict]

class FraudData(BaseModel):
    fraud_id: str
    id_user: str
    id_transactions: List[str]
    status: str
    probability_ml: float
    policy_list: List[str]
    jarak_fraud: Optional[int]
    probability_contact_with_fraud: Optional[float]
    confirmed_fraud: Optional[str]
    confirmed_date: Optional[str]
    confirmed_institution: Optional[str]

class Policy(BaseModel):
    policy_id: str
    name: str
    description: str
    rules: str
    created_at: str
    updated_at: str

class Link(BaseModel):
    source: str
    target: str
    type: str
    weight: float
    reason: str