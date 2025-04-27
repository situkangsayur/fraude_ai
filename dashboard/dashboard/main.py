import streamlit as st
import pandas as pd
import httpx
import asyncio
import threading
from typing import Dict, Any

st.title("Fraud Detection Dashboard")

# --- API Endpoints ---
API_BASE_URL = "http://orchestrator:8000"  # Assuming orchestrator service is named 'orchestrator'

# --- Functions to fetch data from APIs ---
async def get_fraud_check(transaction_id: str) -> Dict[str, Any]:
    try:
        async def fetch_data():
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/fraud_check/{transaction_id}")
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()

        return await fetch_data()  # Run the async function synchronously
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error fetching fraud check for transaction {transaction_id}: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"Request error fetching fraud check for transaction {transaction_id}: {e}")
        return None

# --- Sidebar for navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Choose a page", ["Transaction Review", "Policy Management", "Graph Management", "LLM Prompt Management", "Training Data Management"])

# --- Main content area ---
if page == "Transaction Review":
    st.header("Transaction Review")
    transaction_id = st.text_input("Enter Transaction ID:")
    if st.button("Check Fraud"):
        if transaction_id:
            fraud_data = get_fraud_check(transaction_id)
            if fraud_data:
                st.subheader(f"Fraud Check Results for Transaction {transaction_id}")
                st.json(fraud_data)
        else:
            st.warning("Please enter a Transaction ID.")

elif page == "Policy Management":
    st.header("Policy Management")
    # Fetch and display policies from the orchestrator
    st.subheader("Policies")

    # Display existing policies
    policies = get_policies()
    if policies:
        st.write("Existing Policies:")
        st.json(policies)
    else:
        st.write("No policies found.")

    st.subheader("Manage Policies")

    policy_operation = st.selectbox("Choose Policy Operation", ["Create", "Read", "Update", "Delete"])

    if policy_operation == "Create":
        st.write("Create New Policy")
        policy_name = st.text_input("Policy Name:")
        policy_description = st.text_area("Policy Description:")
        # Simplified rule input - in a real app, this would be more complex
        st.write("Add Rules (JSON format):")
        rules_input = st.text_area("Rules List:")

        if st.button("Create Policy"):
            if policy_name and rules_input:
                try:
                    rules_data = eval(rules_input) # Using eval for simplicity, use json.loads in production
                    policy_data = {"name": policy_name, "description": policy_description, "rules": rules_data}
                    # Run the async function using asyncio.run or similar in a real app context
                    # For Streamlit, we can use a simple thread or a library like streamlit-asyncio
                    import threading
                    import asyncio

                    def run_async_in_thread(coro):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        return loop.run_until_complete(coro)

                    result = run_async_in_thread(create_policy(policy_data))
                    if result:
                        st.success("Policy created successfully!")
                        st.json(result)
                    else:
                        st.error("Failed to create policy.")
                except Exception as e:
                    st.error(f"Error parsing rules JSON or creating policy: {e}")
            else:
                st.warning("Please provide policy name and rules.")

    elif policy_operation == "Read":
        st.write("Read Policy by ID")
        policy_id_input = st.text_input("Policy ID to Read:")
        if st.button("Read Policy"):
            if policy_id_input:
                import threading
                import asyncio

                def run_async_in_thread(coro):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    return loop.run_until_complete(coro)

                policy = run_async_in_thread(read_policy(policy_id_input))
                if policy:
                    st.subheader("Policy Details:")
                    st.json(policy)
                else:
                    st.warning("Policy not found.")
            else:
                st.warning("Please enter a Policy ID.")

    elif policy_operation == "Update":
        st.write("Update Policy by ID")
        policy_id_input = st.text_input("Policy ID to Update:")
        st.write("Enter updated policy data (JSON format):")
        updated_policy_data_input = st.text_area("Updated Policy Data:")
        if st.button("Update Policy"):
            if policy_id_input and updated_policy_data_input:
                try:
                    updated_policy_data = eval(updated_policy_data_input) # Use json.loads in production
                    import threading
                    import asyncio

                    def run_async_in_thread(coro):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        return loop.run_until_complete(coro)

                    result = run_async_in_thread(update_policy(policy_id_input, updated_policy_data))
                    if result:
                        st.success("Policy updated successfully!")
                        st.json(result)
                    else:
                        st.error("Failed to update policy.")
                except Exception as e:
                    st.error(f"Error parsing updated policy data JSON or updating policy: {e}")
            else:
                st.warning("Please provide Policy ID and updated policy data.")

    elif policy_operation == "Delete":
        st.write("Delete Policy by ID")
        policy_id_input = st.text_input("Policy ID to Delete:")
        if st.button("Delete Policy"):
            if policy_id_input:
                import threading
                import asyncio

                def run_async_in_thread(coro):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    return loop.run_until_complete(coro)

                result = run_async_in_thread(delete_policy(policy_id_input))
                if result:
                    st.success("Policy deleted successfully!")
                    st.json(result)
                else:
                    st.error("Failed to delete policy.")
            else:
                st.warning("Please enter a Policy ID.")

    st.subheader("Manage Rules")
    rule_type = st.selectbox("Choose Rule Type", ["Standard Rule", "Velocity Rule"])
    rule_operation = st.selectbox("Choose Rule Operation", ["Create", "Read", "Update", "Delete"], key=f"{rule_type}_operation")

    if rule_type == "Standard Rule":
        if rule_operation == "Create":
            st.write("Create New Standard Rule")
            # Add input fields for Standard Rule data
            rule_data_input = st.text_area("Standard Rule Data (JSON format):", key="create_standard_rule_data")
            if st.button("Create Standard Rule"):
                if rule_data_input:
                    try:
                        rule_data = eval(rule_data_input) # Use json.loads in production
                        import threading
                        import asyncio

                        def run_async_in_thread(coro):
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            return loop.run_until_complete(coro)

                        result = run_async_in_thread(create_standard_rule(rule_data))
                        if result:
                            st.success("Standard Rule created successfully!")
                            st.json(result)
                        else:
                            st.error("Failed to create standard rule.")
                    except Exception as e:
                        st.error(f"Error parsing standard rule data JSON or creating rule: {e}")
                else:
                    st.warning("Please provide standard rule data.")

        elif rule_operation == "Read":
            st.write("Read Standard Rule by ID")
            rule_id_input = st.text_input("Standard Rule ID to Read:", key="read_standard_rule_id")
            if st.button("Read Standard Rule"):
                if rule_id_input:
                    import threading
                    import asyncio

                    def run_async_in_thread(coro):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        return loop.run_until_complete(coro)

                    rule = run_async_in_thread(read_standard_rule(rule_id_input))
                    if rule:
                        st.subheader("Standard Rule Details:")
                        st.json(rule)
                    else:
                        st.warning("Standard Rule not found.")
                else:
                    st.warning("Please enter a Standard Rule ID.")

        elif rule_operation == "Update":
            st.write("Update Standard Rule by ID")
            rule_id_input = st.text_input("Standard Rule ID to Update:", key="update_standard_rule_id")
            st.write("Enter updated standard rule data (JSON format):")
            updated_rule_data_input = st.text_area("Updated Standard Rule Data:", key="update_standard_rule_data")
            if st.button("Update Standard Rule"):
                if rule_id_input and updated_rule_data_input:
                    try:
                        updated_rule_data = eval(updated_rule_data_input) # Use json.loads in production
                        import threading
                        import asyncio

                        def run_async_in_thread(coro):
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            return loop.run_until_complete(coro)

                        result = run_async_in_thread(update_standard_rule(rule_id_input, updated_rule_data))
                        if result:
                            st.success("Standard Rule updated successfully!")
                            st.json(result)
                        else:
                            st.error("Failed to update standard rule.")
                    except Exception as e:
                        st.error(f"Error parsing updated standard rule data JSON or updating rule: {e}")
                else:
                    st.warning("Please provide Standard Rule ID and updated rule data.")

        elif rule_operation == "Delete":
            st.write("Delete Standard Rule by ID")
            rule_id_input = st.text_input("Standard Rule ID to Delete:", key="delete_standard_rule_id")
            if st.button("Delete Standard Rule"):
                if rule_id_input:
                    import threading
                    import asyncio

                    def run_async_in_thread(coro):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        return loop.run_until_complete(coro)

                    result = run_async_in_thread(delete_standard_rule(rule_id_input))
                    if result:
                        st.success("Standard Rule deleted successfully!")
                        st.json(result)
                    else:
                        st.error("Failed to delete standard rule.")
                else:
                    st.warning("Please enter a Standard Rule ID.")

    elif rule_type == "Velocity Rule":
        if rule_operation == "Create":
            st.write("Create New Velocity Rule")
            # Add input fields for Velocity Rule data
            rule_data_input = st.text_area("Velocity Rule Data (JSON format):", key="create_velocity_rule_data")
            if st.button("Create Velocity Rule"):
                if rule_data_input:
                    try:
                        rule_data = eval(rule_data_input) # Use json.loads in production
                        import threading
                        import asyncio

                        def run_async_in_thread(coro):
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            return loop.run_until_complete(coro)

                        result = run_async_in_thread(create_velocity_rule(rule_data))
                        if result:
                            st.success("Velocity Rule created successfully!")
                            st.json(result)
                        else:
                            st.error("Failed to create velocity rule.")
                    except Exception as e:
                        st.error(f"Error parsing velocity rule data JSON or creating rule: {e}")
                else:
                    st.warning("Please provide velocity rule data.")

        elif rule_operation == "Read":
            st.write("Read Velocity Rule by ID")
            rule_id_input = st.text_input("Velocity Rule ID to Read:", key="read_velocity_rule_id")
            if st.button("Read Velocity Rule"):
                if rule_id_input:
                    import threading
                    import asyncio

                    def run_async_in_thread(coro):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        return loop.run_until_complete(coro)

                    rule = run_async_in_thread(read_velocity_rule(rule_id_input))
                    if rule:
                        st.subheader("Velocity Rule Details:")
                        st.json(rule)
                    else:
                        st.warning("Velocity Rule not found.")
                else:
                    st.warning("Please enter a Velocity Rule ID.")

        elif rule_operation == "Update":
            st.write("Update Velocity Rule by ID")
            rule_id_input = st.text_input("Velocity Rule ID to Update:", key="update_velocity_rule_id")
            st.write("Enter updated velocity rule data (JSON format):")
            updated_rule_data_input = st.text_area("Updated Velocity Rule Data:", key="update_velocity_rule_data")
            if st.button("Update Velocity Rule"):
                if rule_id_input and updated_rule_data_input:
                    try:
                        updated_rule_data = eval(updated_rule_data_input) # Use json.loads in production
                        import threading
                        import asyncio

                        def run_async_in_thread(coro):
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            return loop.run_until_complete(coro)

                        result = run_async_in_thread(update_velocity_rule(rule_id_input, updated_rule_data))
                        if result:
                            st.success("Velocity Rule updated successfully!")
                            st.json(result)
                        else:
                            st.error("Failed to update velocity rule.")
                    except Exception as e:
                        st.error(f"Error parsing updated velocity rule data JSON or updating rule: {e}")
                else:
                    st.warning("Please provide Velocity Rule ID and updated rule data.")

        elif rule_operation == "Delete":
            st.write("Delete Velocity Rule by ID")
            rule_id_input = st.text_input("Velocity Rule ID to Delete:", key="delete_velocity_rule_id")
            if st.button("Delete Velocity Rule"):
                if rule_id_input:
                    import threading
                    import asyncio

                    def run_async_in_thread(coro):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        return loop.run_until_complete(coro)

                    result = run_async_in_thread(delete_velocity_rule(rule_id_input))
                    if result:
                        st.success("Velocity Rule deleted successfully!")
                        st.json(result)
                    else:
                        st.error("Failed to delete velocity rule.")
                else:
                    st.warning("Please enter a Velocity Rule ID.")

elif page == "Graph Management":
    st.header("Graph Management")
    # Fetch and display graph rules and nodes from the orchestrator
    graph_rules = get_graph_rules()
    nodes = get_nodes()
    st.write("Graph Rules:", graph_rules)
    st.write("Nodes:", nodes)
    # Add UI elements for CRUD graph rules and nodes
    st.write("Functionality to Create, Read, Update, and Delete graph rules and nodes will be implemented here.")

elif page == "LLM Prompt Management":
    st.header("LLM Prompt Management")
    # Add UI elements to update the LLM prompt and view prompt history
    st.write("Functionality to update the LLM prompt and view prompt history will be implemented here.")

elif page == "Training Data Management":
    st.header("Training Data Management")
    # Add UI elements for re-running training and getting evaluation metrics
    st.write("Functionality to re-run training and get evaluation metrics will be implemented here.")

@st.cache_data
def get_policies():
    try:
        response = httpx.get(f"{API_BASE_URL}/policies/")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error fetching policies: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"Request error fetching policies: {e}")
        return None

@st.cache_data
def get_graph_rules():
    try:
        response = httpx.get(f"{API_BASE_URL}/graph_rules/")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error fetching graph rules: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"HTTP error fetching graph rules: {e}")
        return None

@st.cache_data
def get_nodes():
    try:
        response = httpx.get(f"{API_BASE_URL}/nodes/")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error fetching nodes: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"Request error fetching nodes: {e}")
        return None
# --- Functions to interact with Rules Policy Engine via Orchestrator ---

async def create_policy(policy_data: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_BASE_URL}/policies/", json=policy_data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error creating policy: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"Request error creating policy: {e}")
async def read_policy(policy_id: str) -> Dict[str, Any] | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/policies/{policy_id}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error reading policy {policy_id}: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"Request error reading policy {policy_id}: {e}")
        return None

async def update_policy(policy_id: str, policy_data: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{API_BASE_URL}/policies/{policy_id}", json=policy_data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error updating policy {policy_id}: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"Request error updating policy {policy_id}: {e}")
        return None

async def delete_policy(policy_id: str) -> Dict[str, Any] | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{API_BASE_URL}/policies/{policy_id}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error deleting policy {policy_id}: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"Request error deleting policy {policy_id}: {e}")
        return None

async def create_standard_rule(rule_data: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_BASE_URL}/standard_rules/", json=rule_data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error creating standard rule: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"Request error creating standard rule: {e}")
        return None

async def read_standard_rule(rule_id: str) -> Dict[str, Any] | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/standard_rules/{rule_id}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error reading standard rule {rule_id}: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"Request error reading standard rule {rule_id}: {e}")
        return None

async def update_standard_rule(rule_id: str, rule_data: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{API_BASE_URL}/standard_rules/{rule_id}", json=rule_data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error updating standard rule {rule_id}: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"Request error updating standard rule {rule_id}: {e}")
        return None

async def delete_standard_rule(rule_id: str) -> Dict[str, Any] | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{API_BASE_URL}/standard_rules/{rule_id}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error deleting standard rule {rule_id}: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"Request error deleting standard rule {rule_id}: {e}")
        return None

async def create_velocity_rule(rule_data: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_BASE_URL}/velocity_rules/", json=rule_data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error creating velocity rule: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"Request error creating velocity rule: {e}")
        return None

async def read_velocity_rule(rule_id: str) -> Dict[str, Any] | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/velocity_rules/{rule_id}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error reading velocity rule {rule_id}: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"Request error reading velocity rule {rule_id}: {e}")
        return None

async def update_velocity_rule(rule_id: str, rule_data: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{API_BASE_URL}/velocity_rules/{rule_id}", json=rule_data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error updating velocity rule {rule_id}: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"Request error updating velocity rule {rule_id}: {e}")
        return None

async def delete_velocity_rule(rule_id: str) -> Dict[str, Any] | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{API_BASE_URL}/velocity_rules/{rule_id}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error deleting velocity rule {rule_id}: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"Request error deleting velocity rule {rule_id}: {e}")
        return None

async def process_transaction_api(transaction_data: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_BASE_URL}/transactions", json=transaction_data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error processing transaction: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"Request error processing transaction: {e}")
        return None
        return None