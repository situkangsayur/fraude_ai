import json
import random
import uuid
import requests

def generate_transaction_data(num_transactions):
    transaction_data = []
    fraud_count = int(0.3 * num_transactions)
    suspect_count = int(0.3 * num_transactions)
    normal_count = num_transactions - fraud_count - suspect_count

    for i in range(num_transactions):
        transaction_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        amount = round(random.uniform(10, 1000), 2)
        transaction_type = random.choice(["deposit", "withdrawal", "transfer"])

        if i < fraud_count:
            risk_level = "fraud"
        elif i < fraud_count + suspect_count:
            risk_level = "suspect"
        else:
            risk_level = "normal"

        transaction = {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "amount": amount,
            "transaction_type": transaction_type,
            "risk_level": risk_level
        }
        transaction_data.append(transaction)

    return transaction_data

def post_transaction_data(transaction_data, endpoint_url):
    headers = {'Content-type': 'application/json'}
    for transaction in transaction_data:
        try:
            response = requests.post(endpoint_url, data=json.dumps(transaction), headers=headers)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            print(f"Transaction {transaction['transaction_id']} posted successfully. Response: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"Error posting transaction {transaction['transaction_id']}: {e}")

if __name__ == "__main__":
    num_transactions = 20
    endpoint_url = "http://localhost:8000/transactions"  # Assuming the API is running locally on port 8000
    transaction_data = generate_transaction_data(num_transactions)

    print("Generated Transaction Data:")
    print(json.dumps(transaction_data, indent=4))

    post_transaction_data(transaction_data, endpoint_url)