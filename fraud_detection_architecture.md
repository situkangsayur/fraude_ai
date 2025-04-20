# Fraud Detection System Architecture

## Overview

This document outlines the architecture for a fraud detection system designed for an e-commerce platform. The system aims to detect fraudulent transactions and mark fraudulent accounts. It leverages LLMs, statistical/probabilistic inference, and graph theory to identify various fraud patterns.

## Components

*   **E-commerce Platform:** The existing e-commerce platform where transactions occur.
*   **Data Ingestion:** A component to extract transaction and user data from the e-commerce platform.
*   **MongoDB:** A database to store transaction data, user data, fraud data, and graph data.
*   **Data Preprocessing:** A component to clean and transform the data for feature engineering.
*   **Feature Engineering:** A component to create features for fraud detection models.
*   **LLM Fraud Detection:** A component that uses an LLM to detect fraud based on transaction descriptions, user behavior, etc. It uses RAG to incorporate existing fraud rules, UU PDP, and ISO standards.
*   **Statistical/Probabilistic Inference:** A component that uses statistical and probabilistic methods to detect fraud based on transaction patterns, user demographics, etc.
*   **Graph-Based Fraud Detection:** A component that uses graph theory to detect fraud based on connections between users and transactions.
*   **Policy Engine:** This component will evaluate transactions against a set of predefined rules.
*   **Fraud Aggregation & Scoring:** A component that combines the results from the different fraud detection methods to generate a final fraud score.
*   **Fraud Review Dashboard (Streamlit):** A dashboard for fraud analysts to review flagged transactions and accounts.
*   **FastAPI:** A backend API to serve data to the Streamlit dashboard.
*   **Account Marking:** A component to mark accounts as fraudulent in the e-commerce platform.
*   **Policy Management (CRUD):** A component in the Fraud Review Dashboard to create, read, update, and delete fraud detection policies.
*   **LLM Policy Suggestion:** A component that uses an LLM to analyze transaction data and suggest new fraud detection policies.
*   **RAG (UU PDP, ISO Standards, Fraud Rules):** A component that integrates with the LLM Fraud Detection component to retrieve relevant information from a knowledge base of policies (e.g., UU PDP, ISO standards, existing fraud rules) and augment the LLM's input with the retrieved information.

## Technology Stack

*   **Python:** The primary programming language.
*   **LLM (GPT):** For natural language processing-based fraud detection.
*   **FastAPI:** For building the backend API.
*   **Streamlit:** For creating the fraud review dashboard.
*   **MongoDB:** For storing data.
*   **NetworkX:** For graph analysis.

## Data Flow

1.  Transaction and user data are ingested into MongoDB.
2.  The data is preprocessed and features are engineered.
3.  The Policy Engine evaluates transactions against predefined rules.
4.  The LLM Fraud Detection component uses RAG to analyze transaction data in the context of UU PDP, ISO standards, and existing fraud rules.
5.  The statistical/probabilistic inference and graph-based fraud detection components analyze the data.
6.  The results are combined to generate a final fraud score.
7.  Flagged transactions are sent to the fraud review dashboard.
8.  Fraud analysts review the transactions and mark accounts as fraudulent.
9.  The account marking component updates the e-commerce platform.
10. Fraud analysts can manage fraud detection policies using the Policy Management (CRUD) component.
11. The LLM Policy Suggestion component suggests new fraud detection policies based on transaction data analysis.

## Graph Database Design

*   **Nodes:** Users (id\_user, other user fields)
*   **Edges:** Connections between users based on shared attributes (e.g., same address, phone number, email domain). The edges will have weights based on the similarity of the attributes.

### Graph Storage in MongoDB

*   **Collection: `nodes`**

    ```json
    {
        "id_user": "user123",
        "nama_lengkap": "John Doe",
        "email": "john.doe@example.com",
        "address": "123 Main St",
        ...other user fields
    }
    ```

*   **Collection: `links`**

    ```json
    {
        "source": "user123", // id_user of the source node
        "target": "user456", // id_user of the target node
        "type": "address_similarity", // Type of connection (e.g., address, phone number)
        "weight": 0.85, // Similarity score
        "reason": "Shared address and similar name" // Explanation for the link
    }
    ```

## Fraud Detection Process

1.  **LLM-based analysis:** Analyze transaction descriptions and user behavior using the LLM to identify suspicious patterns.
2.  **Statistical/probabilistic inference:** Use statistical models to identify unusual transaction patterns based on amount, frequency, location, etc.
3.  **Graph-based analysis:**
    *   Detect accounts that are within a short distance (e.g., 3 nodes) of known fraudulent accounts.
    *   Calculate a "probability of contact with fraud" based on the strength and number of connections to fraudulent accounts.

## Confirmed Fraud Updates

*   A process will be implemented to receive confirmed fraud labels from the bank every 3 months.
*   This data will be used to update the `confirmed_fraud` field in the `fraud_field` collection.
*   The confirmed fraud data will also be used to retrain the fraud detection models.

## Sample Data

The system will use sample data (70% normal, 30% fraud) for a total of 500 transactions.

## Policies

The system will use a policy engine to evaluate transactions against predefined rules. For example:

```
IF (item_name == "handphone" AND price > 5000000 AND quantity >= 3 AND time_window == "1 hour") OR (item_name == "handphone" OR item_type == "electronics gadget" AND quantity >= 5 AND time_window == "1 day") THEN flag_as_suspect
```

\`\`\`mermaid
graph LR
    A[User] --> B(E-commerce Platform);
    B --> C{Transaction Data};
    C --> D[Data Ingestion];
    D --> E(MongoDB);
    E --> F[Data Preprocessing];
    F --> G{Feature Engineering};
    G --> H[LLM Fraud Detection];
    G --> I[Statistical/Probabilistic Inference];
    G --> J[Graph-Based Fraud Detection];
    H --> K{Fraud Scores};
    I --> K;
    J --> K;
    K --> L[Fraud Aggregation & Scoring];
    L --> M{Fraudulent Transaction};
    L --> N[Fraud Review Dashboard (Streamlit)];
    M --> O[Account Marking];
    O --> B;
    N --> P(FastAPI);
    P --> E;
    G --> Q{Policy Engine};
    Q --> K;
    N --> R[Policy Management (CRUD)];
    R --> E;
    S[LLM Policy Suggestion] --> R;
    S --> E;
    H --> T[RAG (UU PDP, ISO Standards, Fraud Rules)];
    T --> H;
\`\`\`