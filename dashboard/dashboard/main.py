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
    policies = get_policies()
    st.write(policies)
    # Add UI elements for CRUD policy
    st.write("Functionality to Create, Read, Update, and Delete fraud detection policies will be implemented here.")

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