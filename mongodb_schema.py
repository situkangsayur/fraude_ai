"""
MongoDB Schema Definitions for Fraud Detection System
"""

user_schema = {
    "id_user": "uuid",
    "nama_lengkap": "string",
    "email": "string",
    "domain_email": "string",
    "address": "string",
    "address_zip": "string",
    "address_city": "string",
    "address_province": "string",
    "address_kecamatan": "string",
    "phone_number": "string"
}

transaction_schema = {
    "id_transaction": "uuid",
    "id_user": "uuid",
    "shipzip": "string",
    "shipping_address": "string",
    "shipping_city": "string",
    "shipping_province": "string",
    "shipping_kecamatan": "string",
    "payment": {
        "payment_type": "string (enum)",
        "number": "string",
        "bank_name": "string",
        "amount": "number",
        "status": "string (enum)",
        "billing_address": "string",
        "billing_city": "string",
        "billing_province": "string",
        "billing_kecamatan": "string"
    },
    "amount": "number",
    "list_of_items": [
        {
            "item_name": "string",
            "price": "number",
            "quantity": "number"
        }
    ]
}

fraud_data_schema = {
    "fraud_id": "uuid",
    "id_user": "uuid",
    "id_transactions": ["uuid"],
    "status": "string (enum)",
    "probability_ml": "number",
    "policy_list": ["string"],
    "graph_info": {
        "jarak_fraud": "number",
        "probability_contact_with_fraud": "number"
    },
    "confirmed_fraud": "string (date)",
    "confirmed_date": "string (date)",
    "confirmed_institution": "string"
}

policy_schema = {
    "policy_id": "uuid",
    "name": "string",
    "description": "string",
    "rules": "string (e.g., JSON or a rule engine format)",
    "created_at": "string (date)",
    "updated_at": "string (date)"
}

link_schema = {
    "source": "uuid (id_user)",
    "target": "uuid (id_user)",
    "type": "string (e.g., address_similarity, phone_similarity)",
    "weight": "number",
    "reason": "string"
}

print("MongoDB Schema Definitions for Fraud Detection System")
print("Please use these schemas as a template for creating collections in MongoDB.")