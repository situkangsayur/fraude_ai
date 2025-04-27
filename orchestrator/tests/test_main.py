import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from orchestrator.orchestrator.main import app

client = TestClient(app)

@pytest.fixture
def mock_services():
    """Fixture to mock external service calls."""
    with patch("orchestrator.orchestrator.main.call_llm_interface", new_callable=AsyncMock) as mock_llm, \
         patch("orchestrator.orchestrator.main.call_graph_service", new_callable=AsyncMock) as mock_graph, \
         patch("orchestrator.orchestrator.main.call_rules_policy_engine", new_callable=AsyncMock) as mock_rules, \
         patch("orchestrator.orchestrator.main.call_neural_net_service", new_callable=AsyncMock) as mock_neural_net, \
         patch("orchestrator.orchestrator.main.get_transaction_data", new_callable=AsyncMock) as mock_get_transaction:
        yield {
            "llm": mock_llm,
            "graph": mock_graph,
            "rules": mock_rules,
            "neural_net": mock_neural_net,
            "get_transaction": mock_get_transaction,
        }

def test_fraud_check_endpoint(mock_services):
    """Test the /fraud_check/{transaction_id} endpoint."""
    transaction_id = "test_transaction_123"
    mock_transaction_data = {
        "id_transaction": transaction_id,
        "id_user": "user123",
        "amount": 100.00,
        "list_of_items": []
    }

    # Configure mock service responses
    mock_services["get_transaction"].return_value = mock_transaction_data
    mock_services["llm"].return_value = {"fraud_score": 10}
    mock_services["graph"].return_value = {"proximity_score": 5}
    mock_services["rules"].return_value = {"risk_points": 20, "risk_level": "suspect"} # Use risk_points
    mock_services["neural_net"].return_value = {"fraud_score": 15}

    response = client.get(f"/fraud_check/{transaction_id}")

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["transaction_id"] == transaction_id
    # Check if the total fraud score is calculated correctly using risk_points
    assert response_data["fraud_score"] == 10 + 5 + 20 + 15
    assert response_data["llm_results"] == {"fraud_score": 10}
    assert response_data["graph_results"] == {"proximity_score": 5}
    assert response_data["rules_results"] == {"risk_points": 20, "risk_level": "suspect"}
    assert response_data["neural_net_results"] == {"fraud_score": 15}

    # Verify that the mocked services were called with the correct data
    mock_services["get_transaction"].assert_called_once_with(transaction_id)
    mock_services["llm"].assert_called_once_with(mock_transaction_data)
    mock_services["graph"].assert_called_once_with(mock_transaction_data)
    mock_services["rules"].assert_called_once_with(mock_transaction_data)
    mock_services["neural_net"].assert_called_once_with(mock_transaction_data)

# Add more test cases as needed, e.g., for different transaction data,
# error handling from services, etc.