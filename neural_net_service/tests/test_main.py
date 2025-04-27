import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import torch
import mongomock
from datetime import datetime
import os # Import os for file path checks

# Import the FastAPI app and models from the main service file
from neural_net_service.main import app, SimpleNN, FraudScoreResponse, FraudConfirmation, TrainingParams, MODEL_PATH, train_model # Import TrainingParams and MODEL_PATH, train_model
from common.models import Transaction, FraudData

# Create a TestClient for the FastAPI app within a fixture
@pytest.fixture(scope="function")
def client(mock_db_session):
    # Patch the functions that get the MongoDB client and database
    # to use the mocked database instance from the session fixture
    yield TestClient(app)

# Mock MongoDB client and database for testing (This fixture is no longer needed in test_main.py
# as the mocking is handled in conftest.py at the module level)
# @pytest.fixture(scope="function")
# def mock_db():
#     # Use mongomock for a in-memory MongoDB instance
#     mock_client = mongomock.MongoClient()
#     mock_db = mock_client.get_database("test_db")

#     # Patch the functions that get the MongoDB client and database
#     with patch('neural_net_service.main.get_mongodb_client', return_value=mock_client), \
#          patch('neural_net_service.main.get_mongodb_database', return_value=mock_db):
#         yield mock_db

# Fixture to seed the database with sample data
# This fixture now depends on the session-scoped mock_db_session from conftest.py
@pytest.fixture(scope="function")
def seeded_db(mock_db_session):
    transactions_collection = mock_db_session.transactions
    fraud_data_collection = mock_db_session.fraud_data

    # Sample Transaction Data (30 transactions)
    sample_transactions = []
    for i in range(1, 31):
        transaction_data = {
            "id_transaction": f"transaction_{i}",
            "id_user": f"user_{(i % 10) + 1}", # Assign to 10 users
            "shipzip": f"zip_{i:05d}",
            "shipping_address": f"{i} Test St",
            "shipping_city": "Testville",
            "shipping_province": "TV",
            "shipping_kecamatan": "Test District",
            "payment_type": "credit_card" if i % 2 == 0 else "debit_card",
            "number": f"1111-2222-3333-{i:04d}",
            "bank_name": f"Bank_{i % 5 + 1}",
            "amount": 10.0 * i,
            "status": "completed",
            "billing_address": f"{i} Test St",
            "billing_city": "Testville",
            "billing_province": "TV",
            "billing_kecamatan": "Test District",
            "list_of_items": [{"item_id": f"item_{j}", "price": 5.0} for j in range(i % 3 + 1)] # 1 to 3 items
        }
        sample_transactions.append(transaction_data)

    transactions_collection.insert_many(sample_transactions)

    # Sample Fraud Data (10 fraud, 20 normal)
    sample_fraud_data = []
    for i in range(1, 31):
        fraud_status = "fraud" if i <= 10 else "normal"
        fraud_data = {
            "fraud_id": f"fraud_data_{i}",
            "id_user": f"user_{(i % 10) + 1}",
            "id_transactions": [f"transaction_{i}"],
            "status": "processed",
            "probability_ml": 0.9 if i <= 10 else 0.1,
            "policy_list": [f"policy_{i % 3 + 1}"],
            "jarak_fraud": 5 if i <= 10 else None,
            "probability_contact_with_fraud": 0.8 if i <= 10 else None,
            "confirmed_fraud": fraud_status,
            "confirmed_date": datetime.now().isoformat() if i <= 10 else None,
            "confirmed_institution": f"Institution_{i % 2 + 1}" if i <= 10 else None
        }
        sample_fraud_data.append(fraud_data)

    fraud_data_collection.insert_many(sample_fraud_data)

    yield mock_db_session

# Test the /predict endpoint
@pytest.mark.asyncio
async def test_predict_fraud(client, seeded_db): # Add seeded_db fixture dependency
    # Mock the model prediction
    with patch('neural_net_service.main.model') as mock_model:
        mock_model.eval.return_value = None # Mock eval call
        mock_model.return_value = torch.tensor([0.8]) # Mock prediction result

        # Create a dummy transaction
        transaction_data = {
            "id_transaction": "test_transaction_123",
            "id_user": "test_user_456",
            "shipzip": "12345",
            "shipping_address": "123 Test St",
            "shipping_city": "Testville",
            "shipping_province": "TV",
            "shipping_kecamatan": "Test District",
            "payment_type": "credit_card",
            "number": "1234-5678-9012-3456",
            "bank_name": "Test Bank",
            "amount": 100.50,
            "status": "completed",
            "billing_address": "123 Test St",
            "billing_city": "Testville",
            "billing_province": "TV",
            "billing_kecamatan": "Test District",
            "list_of_items": [{"item_id": "item1", "price": 50.25}, {"item_id": "item2", "price": 50.25}]
        }
        transaction = Transaction(**transaction_data)

        response = client.post("/predict", json=transaction.model_dump())

        assert response.status_code == 200
        response_data = response.json()
        assert "fraud_score" in response_data
        assert "fraud_tag" in response_data
        assert response_data["fraud_score"] == pytest.approx(0.8)
        assert response_data["fraud_tag"] == "fraud"

# Test the /transactions/{transaction_id} endpoint - found case
@pytest.mark.asyncio
async def test_get_transaction_found(client, seeded_db):
    transaction_id = "transaction_1" # Use an ID from the seeded data
    response = client.get(f"/transactions/{transaction_id}")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id_transaction"] == transaction_id
    assert response_data["amount"] == 10.0 # Amount for transaction_1

# Test the /transactions/{transaction_id} endpoint - not found case
@pytest.mark.asyncio
async def test_get_transaction_not_found(client, seeded_db):
    transaction_id = "non_existent_transaction"
    response = client.get(f"/transactions/{transaction_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Transaction not found"}

# Test the /transactions/{transaction_id}/confirm_fraud endpoint - success case
@pytest.mark.asyncio
async def test_confirm_fraud_status_success(client, seeded_db):
    transaction_id = "transaction_1" # Use an ID from the seeded data
    confirmation_data = {"confirmed_fraud": "fraud", "confirmed_institution": "Test Institution Update"}
    confirmation = FraudConfirmation(**confirmation_data)

    response = client.post(f"/transactions/{transaction_id}/confirm_fraud", json=confirmation.model_dump())

    assert response.status_code == 200
    assert response.json() == {"message": "Fraud confirmation updated successfully"}

    # Verify the update in the mock database
    updated_transaction = seeded_db.transactions.find_one({"id_transaction": transaction_id})
    assert updated_transaction is not None
    assert updated_transaction["confirmed_fraud"] == "fraud"
    assert updated_transaction["confirmed_institution"] == "Test Institution Update"
    assert "confirmed_date" in updated_transaction # Check if confirmed_date was added

# Test the /transactions/{transaction_id}/confirm_fraud endpoint - transaction not found case
@pytest.mark.asyncio
async def test_confirm_fraud_status_transaction_not_found(client, seeded_db):
    transaction_id = "non_existent_transaction"
    confirmation_data = {"confirmed_fraud": "fraud", "confirmed_institution": "Test Institution"}
    confirmation = FraudConfirmation(**confirmation_data)

    response = client.post(f"/transactions/{transaction_id}/confirm_fraud", json=confirmation.model_dump())

    assert response.status_code == 404
    assert response.json() == {"detail": "Transaction not found"}

# Test the /transactions/{transaction_id}/confirm_fraud endpoint - no changes made case
@pytest.mark.asyncio
async def test_confirm_fraud_status_no_changes(client, seeded_db):
    transaction_id = "transaction_1" # Use an ID from the seeded data
    # Use the same confirmation data that's already in the seeded data (assuming transaction_1 is fraud)
    confirmation_data = {"confirmed_fraud": "fraud", "confirmed_institution": "Institution_1"} # Assuming transaction_1 is linked to Institution_1 in seeding
    confirmation = FraudConfirmation(**confirmation_data)

    response = client.post(f"/transactions/{transaction_id}/confirm_fraud", json=confirmation.model_dump())

    assert response.status_code == 200
    assert response.json() == {"message": "Transaction found, but no changes were made"}


# Test the SimpleNN model
def test_simple_nn_forward():
    input_size = 2 # Use input size 2 as defined in main.py
    model = SimpleNN(input_size)
    # Create a dummy input tensor
    input_tensor = torch.randn(1, input_size) # Batch size of 1

    output = model(input_tensor)

    # Check the output shape and range
    assert output.shape == torch.Size([1, 1])
    assert 0 <= output.item() <= 1 # Sigmoid output should be between 0 and 1

# --- Neural Network Tests ---

# Fixture to create and clean up a dummy model file
@pytest.fixture(scope="function")
def dummy_model_file():
    # Ensure no model file exists before the test
    if os.path.exists(MODEL_PATH):
        os.remove(MODEL_PATH)
    yield
    # Clean up the dummy model file after the test
    if os.path.exists(MODEL_PATH):
        os.remove(MODEL_PATH)

def test_model_loads_if_exists(dummy_model_file, mocker):
    # Create a dummy model file
    dummy_model = MagicMock(spec=nn.Module)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(dummy_model, f)

    # Mock pickle.load to track if it's called
    mocker.patch('neural_net_service.neural_net_service.main.pickle.load', return_value=dummy_model)
    mocker.patch('neural_net_service.neural_net_service.main.SimpleNN', return_value=MagicMock(spec=nn.Module)) # Mock SimpleNN to avoid actual instantiation

    # Reload the main module to trigger model loading logic
    with patch.dict('sys.modules', {'neural_net_service.neural_net_service.main': None}):
        from neural_net_service.neural_net_service import main as reloaded_main
        assert reloaded_main.pickle.load.called # Check if pickle.load was called

def test_model_creates_new_if_not_exists(dummy_model_file, mocker):
    # Ensure no model file exists
    assert not os.path.exists(MODEL_PATH)

    # Mock SimpleNN to track if it's called
    mocker.patch('neural_net_service.neural_net_service.main.SimpleNN', return_value=MagicMock(spec=nn.Module))
    mocker.patch('neural_net_service.neural_net_service.main.pickle.load', side_effect=FileNotFoundError) # Ensure load fails

    # Reload the main module to trigger model loading logic
    with patch.dict('sys.modules', {'neural_net_service.neural_net_service.main': None}):
        from neural_net_service.neural_net_service import main as reloaded_main
        assert reloaded_main.SimpleNN.called # Check if SimpleNN was called

def test_train_model_saves_model(dummy_model_file):
    model = SimpleNN(input_size=2)
    # Dummy data: ([features], label)
    dummy_data = [([100.0, 2], 1.0), ([50.0, 1], 0.0)]

    # Ensure model file does not exist before training
    assert not os.path.exists(MODEL_PATH)

    train_model(model, dummy_data, epochs=1)

    # Check if model file was created
    assert os.path.exists(MODEL_PATH)

    # Optional: Load the model back to ensure it's a valid pickle file
    with open(MODEL_PATH, 'rb') as f:
        loaded_model = pickle.load(f)
    assert isinstance(loaded_model, SimpleNN)

@patch('neural_net_service.neural_net_service.main.train_model')
def test_train_endpoint(mock_train_model, mock_db_session):
    client = TestClient(app)
    training_params = {"epochs": 5, "learning_rate": 0.01}

    # Add some dummy data to the mocked database
    mock_db_session.transactions.insert_many([
        {"id_transaction": "trans1", "amount": 100.0, "list_of_items": ["item1"], "confirmed_fraud": "fraud"},
        {"id_transaction": "trans2", "amount": 50.0, "list_of_items": ["item2", "item3"], "confirmed_fraud": "normal"},
    ])

    response = client.post("/train", json=training_params)

    assert response.status_code == 200
    assert response.json() == {"message": "Model training initiated. Check logs for progress."}
    mock_train_model.assert_called_once()
    # You could add more assertions here to check the arguments passed to train_model

@patch('neural_net_service.neural_net_service.main.model') # Mock the global model instance
def test_predict_endpoint(mock_model, mock_db_session):
    client = TestClient(app)
    transaction_data = {
        "id": "trans_predict_1",
        "id_transaction": "trans_predict_1",
        "id_account": "acc_predict_1",
        "id_subscription": "sub_predict_1",
        "id_policy": "pol_predict_1",
        "id_block": "block_predict_1",
        "id_merchant": "mer_predict_1",
        "id_terminal": "ter_predict_1",
        "id_customer": "cus_predict_1",
        "id_payment_method": "pay_predict_1",
        "id_channel": "cha_predict_1",
        "id_location": "loc_predict_1",
        "id_device": "dev_predict_1",
        "id_product": "pro_predict_1",
        "amount": 150.0,
        "currency": "USD",
        "timestamp": datetime.now().isoformat(),
        "type": "purchase",
        "status": "completed",
        "list_of_items": [{"item_id": "item_p1", "price": 150.0, "quantity": 1}],
        "payment_method_details": {"card_type": "credit"},
        "customer_details": {"age": 30},
        "device_details": {"os": "android"},
        "location_details": {"country": "USA"},
        "transaction_history": [],
        "ip_address": "192.168.1.1",
        "user_agent": "test-agent",
        "additional_info": {},
        "fraud_score": None,
        "fraud_tag": None,
        "confirmed_fraud": None,
        "confirmed_date": None,
        "confirmed_institution": None
    }

    # Configure the mock model's forward method to return a specific score
    mock_model.return_value = torch.tensor([[0.8]]) # Simulate a high fraud score

    response = client.post("/predict", json=transaction_data)

    assert response.status_code == 200
    # Check the response against the expected fraud score and tag based on the mock model output
    expected_fraud_score = 0.8
    expected_fraud_tag = "fraud" if expected_fraud_score >= 0.5 else "normal"
    assert response.json() == {"fraud_score": expected_fraud_score, "fraud_tag": expected_fraud_tag}

    # Test with a low fraud score
    mock_model.return_value = torch.tensor([[0.3]]) # Simulate a low fraud score
    response = client.post("/predict", json=transaction_data)
    assert response.status_code == 200
    expected_fraud_score = 0.3
    expected_fraud_tag = "fraud" if expected_fraud_score >= 0.5 else "normal"
    assert response.json() == {"fraud_score": expected_fraud_score, "fraud_tag": expected_fraud_tag}