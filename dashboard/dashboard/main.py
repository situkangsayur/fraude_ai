import streamlit as st
import pandas as pd
import httpx
import asyncio
import threading
from typing import Dict, Any
from common.config import RULES_POLICY_ENGINE_URL

st.title("Fraud Detection Dashboard")

# --- API Endpoints ---
API_BASE_URL = "http://orchestrator:8000"  # Assuming orchestrator service is named 'orchestrator'

# --- Functions to fetch data from APIs ---
async def get_fraud_check(transaction_id: str) -> Dict[str, Any]:
    try:
        async def fetch_data():
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{RULES_POLICY_ENGINE_URL}/fraud_check/{transaction_id}")
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                return response.json()

        return await fetch_data()  # Run the async function synchronously
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error fetching fraud check for transaction {transaction_id}: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"HTTP error fetching fraud check for transaction {transaction_id}: {e}")
        return None

async def get_transactions() -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RULES_POLICY_ENGINE_URL}/transactions/")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error fetching transactions: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"HTTP error fetching transactions: {e}")
        return None

async def get_users() -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RULES_POLICY_ENGINE_URL}/users/")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error fetching users: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"HTTP error fetching users: {e}")
        return None

# --- Sidebar for navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Choose a page", ["Transaction Review", "Policy Management", "Graph Management", "LLM Prompt Management", "Training Data Management", "User Management", "Add Transaction", "Transaction List", "User List", "LLM Report", "LLM Rule Recommendation"])

# --- Main content area ---
if page == "Transaction Review":
    st.header("Transaction Review")
    transaction_id = st.text_input("Enter Transaction ID:")
    if st.button("Check Fraud"):
        if transaction_id:
            async def check_fraud():
                fraud_data = await get_fraud_check(transaction_id)
                if fraud_data:
                    st.subheader(f"Fraud Check Results for Transaction {transaction_id}")
                    st.json(fraud_data)
            asyncio.run(check_fraud())
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
                    rules_data = eval(rules_input) # Use json.loads in production
                    policy_data = {"name": policy_name, "description": policy_description, "rules": rules_data}
                    # Run the async function using asyncio.run or similar in a real app context
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

    elif page == "User Management":
        st.header("User Management")
        # Fetch and display users from the rules_policy_engine
        async def display_users():
            users = await get_users()
            if users:
                st.write("Users:")
                st.json(users)
            else:
                st.write("No users found.")
        asyncio.run(display_users())
elif page == "LLM Rule Recommendation":
        st.header("LLM Rule Recommendation")

        async def get_llm_recommendations():
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://llm_interface:8000/recommendations")  # Assuming llm_interface is named 'llm_interface'
                    response.raise_for_status()
                    recommendations = response.json()
                    return recommendations
            except httpx.HTTPStatusError as e:
                st.error(f"HTTP error: {e}")
                return None
            except httpx.RequestError as e:
                st.error(f"Request error: {e}")
                return None

        recommendations = asyncio.run(get_llm_recommendations())

        if recommendations:
            st.subheader("Rules Policy Engine Recommendations:")
            rules_engine_recommendations = recommendations.get("rules_policy_engine")
            if rules_engine_recommendations:
                st.json(rules_engine_recommendations)
                if st.button("Add to Rules Policy Engine"):
                    async def add_rules_engine_rule(rule_data: Dict[str, Any]):
                        try:
                            async with httpx.AsyncClient() as client:
                                if rule_data.get("rule_type") == "standard":
                                    response = await client.post(f"{RULES_POLICY_ENGINE_URL}/standard_rules/", json=rule_data)
                                elif rule_data.get("rule_type") == "velocity":
                                    response = await client.post(f"{RULES_POLICY_ENGINE_URL}/velocity_rules/", json=rule_data)
                                else:
                                    st.error("Unknown rule type.")
                                    return

                                response.raise_for_status()
                                result = response.json()
                                st.success("Rule added to Rules Policy Engine successfully!")
                                st.json(result)
                        except httpx.HTTPStatusError as e:
                            st.error(f"HTTP error: {e}")
                        except httpx.RequestError as e:
                            st.error(f"Request error: {e}")
                        except Exception as e:
                            st.error(f"An unexpected error occurred: {e}")

                    asyncio.run(add_rules_engine_rule(rules_engine_recommendations))
            else:
                st.write("No recommendations found for Rules Policy Engine.")

            st.subheader("Graph Service Recommendations:")
            graph_service_recommendations = recommendations.get("graph_service")
            if graph_service_recommendations:
                st.json(graph_service_recommendations)
                if st.button("Add to Graph Service"):
                    async def add_graph_service_rule(rule_data: Dict[str, Any]):
                        try:
                            async with httpx.AsyncClient() as client:
                                response = await client.post("http://graph_service:8000/graph_rules/", json=rule_data)
                                response.raise_for_status()
                                result = response.json()
                                st.success("Rule added to Graph Service successfully!")
                                st.json(result)
                        except httpx.HTTPStatusError as e:
                            st.error(f"HTTP error: {e}")
                        except httpx.RequestError as e:
                            st.error(f"Request error: {e}")
                        except Exception as e:
                            st.error(f"An unexpected error occurred: {e}")

                    asyncio.run(add_graph_service_rule(graph_service_recommendations))
            else:
                st.write("No recommendations found for Graph Service.")
elif page == "LLM Report":
        st.header("LLM Report")

        async def get_llm_report():
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://llm_interface:8000/report")  # Assuming llm_interface is named 'llm_interface'
                    response.raise_for_status()
                    report = response.json()
                    return report
            except httpx.HTTPStatusError as e:
                st.error(f"HTTP error: {e}")
                return None
            except httpx.RequestError as e:
                st.error(f"Request error: {e}")
                return None

        report = asyncio.run(get_llm_report())

        if report:
            st.subheader("Fraud Information:")
            st.write(f"True Positives: {report.get('true_positives')}")
            st.write(f"False Positives: {report.get('false_positives')}")
            st.write(f"True Negatives: {report.get('true_negatives')}")
            st.write(f"False Negatives: {report.get('false_negatives')}")
            st.write(f"Transaction Number: {report.get('transaction_number')}")

            st.subheader("Fraud Cluster (Graph Service):")
            st.json(report.get("fraud_cluster"))
        else:
            st.error("Failed to retrieve LLM report.")
elif page == "User List":
        st.header("User List")

        async def get_all_users():
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{RULES_POLICY_ENGINE_URL}/users")
                    response.raise_for_status()
                    users = response.json()
                    return users
            except httpx.HTTPStatusError as e:
                st.error(f"HTTP error: {e}")
                return None
            except httpx.RequestError as e:
                st.error(f"Request error: {e}")
                return None

        users = asyncio.run(get_all_users())

        if users:
            for user in users:
                user_id = user.get("user_id")
                if user_id:
                    st.markdown(f"<a href='/?page=User%20Profile&user_id={user_id}'>{user_id}</a>", unsafe_allow_html=True)
                else:
                    st.write(f"User: {user}")
        else:
            st.warning("No users found.")
elif page == "Transaction List":
        st.header("Transaction List")
        
        async def get_all_transactions():
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{RULES_POLICY_ENGINE_URL}/transactions")
                    response.raise_for_status()
                    transactions = response.json()
                    return transactions
            except httpx.HTTPStatusError as e:
                st.error(f"HTTP error: {e}")
                return None
            except httpx.RequestError as e:
                st.error(f"Request error: {e}")
                return None

        transactions = asyncio.run(get_all_transactions())

        if transactions:
            df = pd.DataFrame(transactions)
            st.dataframe(df)
        else:
            st.warning("No transactions found.")
elif page == "Add Transaction":
        st.header("Add Transaction")
        transaction_id = st.text_input("Transaction ID:")
        user_id = st.text_input("User ID:")
        amount = st.number_input("Amount:")
        description = st.text_area("Description:")

        if st.button("Submit Transaction"):
            if transaction_id and user_id and amount:
                # Send transaction data to rules_policy_engine and graph_service
                transaction_data = {
                    "transaction_id": transaction_id,
                    "user_id": user_id,
                    "amount": amount,
                    "description": description,
                }
                
                async def send_transaction():
                    try:
                        async with httpx.AsyncClient() as client:
                            rules_response = await client.post(f"{RULES_POLICY_ENGINE_URL}/transactions", json=transaction_data)
                            rules_response.raise_for_status()
                            rules_result = rules_response.json()

                            graph_response = await client.post("http://graph_service:8000/analyze", json=transaction_data)  # Assuming graph_service is named 'graph_service'
                            graph_response.raise_for_status()
                            graph_result = graph_response.json()

                            return rules_result, graph_result
                    except httpx.HTTPStatusError as e:
                        st.error(f"HTTP error: {e}")
                        return None, None
                    except httpx.RequestError as e:
                        st.error(f"HTTP error: {e}")
                        return None, None

                rules_result, graph_result = asyncio.run(send_transaction())

                if rules_result and graph_result:
                    st.subheader("Rules Policy Engine Result:")
                    st.json(rules_result)
                    st.subheader("Graph Service Result:")
                    st.json(graph_result)
                else:
                    st.error("Failed to send transaction data to services.")
            else:
                st.warning("Please fill in all required fields.")
elif page == "User Profile":
        st.header("User Profile")
        user_id = st.query_params.get("user_id")

        if user_id:
            async def get_user_profile(user_id: str):
                try:
                    async with httpx.AsyncClient() as client:
                        rules_response = await client.get(f"{RULES_POLICY_ENGINE_URL}/users/{user_id}/risk_info")
                        rules_response.raise_for_status()
                        rules_result = rules_response.json()

                        # Assuming graph_service also has user profile endpoint
                        graph_response = await client.get(f"http://graph_service:8000/users/{user_id}")
                        graph_response.raise_for_status()
                        graph_result = graph_response.json()

                        return rules_result, graph_result
                except httpx.HTTPStatusError as e:
                    st.error(f"HTTP error: {e}")
                    return None, None
                except httpx.RequestError as e:
                    st.error(f"HTTP error: {e}")
                    return None, None

            rules_result, graph_result = asyncio.run(get_user_profile(user_id))

            if rules_result and graph_result:
                st.subheader(f"User ID: {user_id}")
                st.subheader("Risk Information (Rules Policy Engine):")
                st.json(rules_result)
                st.subheader("Graph Service Information:")
                st.json(graph_result)

                # Placeholder for bank confirmation data
                st.subheader("Bank Confirmation:")
                st.write("No bank confirmation data available.")
            else:
                st.error("Failed to retrieve user profile data.")
        else:
            st.warning("No user ID specified.")

@st.cache_data
def get_policies():
    try:
        response = httpx.get(f"{RULES_POLICY_ENGINE_URL}/policies/")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error fetching policies: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"HTTP error fetching policies: {e}")
        return None

@st.cache_data
def get_graph_rules():
    try:
        response = httpx.get(f"{RULES_POLICY_ENGINE_URL}/graph_rules/")
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
        response = httpx.get(f"{RULES_POLICY_ENGINE_URL}/nodes/")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error fetching nodes: {e}")
        return None
    except httpx.RequestError as e:
        st.error(f"HTTP error fetching nodes: {e}")
        return None