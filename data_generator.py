import random
import datetime
from faker import Faker

fake = Faker('id_ID')  # Use Indonesian locale for realistic data

def generate_sample_data(num_records=500, fraud_percentage=0.3):
    """Generates sample transaction data with a mix of normal and fraudulent transactions."""

    num_fraudulent = int(num_records * fraud_percentage)
    num_normal = num_records - num_fraudulent

    data = []

    # Generate normal transactions
    for _ in range(num_normal):
        user_data = generate_user_data()
        transaction_data = generate_transaction_data(user_data['id_user'], is_fraud=False)
        data.append({**user_data, **transaction_data})

    # Generate fraudulent transactions
    for _ in range(num_fraudulent):
        user_data = generate_user_data()
        transaction_data = generate_transaction_data(user_data['id_user'], is_fraud=True)
        data.append({**user_data, **transaction_data})

    return data

def generate_user_data():
    """Generates sample user data."""
    id_user = fake.uuid4()
    nama_lengkap = fake.name()
    email = fake.email()
    domain_email = email.split('@')[1]
    address = fake.address()
    address_zip = fake.postcode()
    address_city = fake.city()
    address_province = fake.state()
    address_kecamatan = fake.state()  # Kecamatan is similar to state in Faker

    phone_number = fake.phone_number()

    return {
        'id_user': id_user,
        'nama_lengkap': nama_lengkap,
        'email': email,
        'domain_email': domain_email,
        'address': address,
        'address_zip': address_zip,
        'address_city': address_city,
        'address_province': address_province,
        'address_kecamatan': address_kecamatan,
        'phone_number': phone_number
    }

def generate_transaction_data(id_user, is_fraud=False):
    """Generates sample transaction data."""
    id_transaction = fake.uuid4()
    shipzip = fake.postcode()
    shipping_address = fake.address()
    shipping_city = fake.city()
    shipping_province = fake.state()
    shipping_kecamatan = fake.state()

    payment_type = random.choice(['virtual account', 'credit card', 'cash on delivery', 'debit card', 'wallet gopay'])
    number = fake.credit_card_number() if payment_type == 'credit card' else fake.random_number(digits=10)
    bank_name = fake.company() if payment_type in ['virtual account', 'debit card'] else None
    amount = round(random.uniform(10000, 10000000), 2)  # Amount in IDR
    status = random.choice(['success', 'failed', 'on process'])
    billing_address = fake.address()
    billing_city = fake.city()
    billing_province = fake.state()
    billing_kecamatan = fake.state()

    list_of_items = []
    num_items = random.randint(1, 5)
    for _ in range(num_items):
        item_name = fake.word()
        price = round(random.uniform(10000, 5000000), 2)
        quantity = random.randint(1, 3)
        list_of_items.append({'item_name': item_name, 'price': price, 'quantity': quantity})

    fraud_id = fake.uuid4() if is_fraud else None
    id_transactions = [id_transaction] if is_fraud else []
    fraud_status = random.choice(['fraud', 'normal', 'suspect']) if is_fraud else 'normal'
    probability_ml = round(random.uniform(0.7, 0.99), 2) if is_fraud else None
    policy_list = ['policy1', 'policy2'] if is_fraud else []
    jarak_fraud = random.randint(1, 5) if is_fraud else None
    probability_contact_with_fraud = round(random.uniform(0.5, 0.8), 2) if is_fraud else None
    confirmed_fraud = fake.date_between(start_date='-6m', end_date='today') if is_fraud and random.random() < 0.3 else None # 30% chance of being confirmed
    confirmed_fraud = confirmed_fraud.isoformat() if confirmed_fraud else None
    confirmed_date = fake.date_between(start_date='-6m', end_date='today') if confirmed_fraud else None
    confirmed_date = confirmed_date.isoformat() if confirmed_fraud else None
    confirmed_institution = fake.company() if confirmed_fraud else None

    return {
        'id_transaction': id_transaction,
        'id_user': id_user,
        'shipzip': shipzip,
        'shipping_address': shipping_address,
        'shipping_city': shipping_city,
        'shipping_province': shipping_province,
        'shipping_kecamatan': shipping_kecamatan,
        'payment': {
            'payment_type': payment_type,
            'number': number,
            'bank_name': bank_name,
            'amount': amount,
            'status': status,
            'billing_address': billing_address,
            'billing_city': billing_city,
            'billing_province': billing_province,
            'billing_kecamatan': billing_kecamatan
        },
        'amount': amount,
        'list_of_items': list_of_items,
        'fraud_field': {
            'fraud_id': fraud_id,
            'id_transactions': id_transactions,
            'status': fraud_status,
            'probability_ml': probability_ml,
            'policy_list': policy_list,
            'graph_info': {
                'jarak_fraud': jarak_fraud,
                'probability_contact_with_fraud': probability_contact_with_fraud
            },
            'confirmed_fraud': confirmed_fraud,
            'confirmed_date': confirmed_date,
            'confirmed_institution': confirmed_institution
        }
    }

if __name__ == '__main__':
    sample_data = generate_sample_data()
    import json
    with open('sample_data.json', 'w') as f:
        json.dump(sample_data, f, indent=4, ensure_ascii=False)
    print("Sample data generated and saved to sample_data.json")