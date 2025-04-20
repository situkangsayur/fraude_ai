import json

class PolicyEngine:
    def __init__(self, policies):
        self.policies = policies

    def evaluate_transaction(self, transaction):
        """
        Evaluates a transaction against the defined policies.
        Returns a list of policy IDs that the transaction violates.
        """
        violated_policies = []
        for policy in self.policies:
            if self.evaluate_policy(transaction, policy):
                violated_policies.append(policy['policy_id'])
        return violated_policies

    def evaluate_policy(self, transaction, policy):
        """
        Evaluates a transaction against a single policy.
        Returns True if the transaction violates the policy, False otherwise.
        """
        try:
            # Evaluate the policy rules using a simple eval() function
            # **WARNING:** Using eval() can be dangerous if the policy rules are not carefully controlled.
            # In a production environment, consider using a safer rule engine or a more restricted evaluation method.
            return eval(policy['rules'], {'transaction': transaction})
        except Exception as e:
            print(f"Error evaluating policy {policy['policy_id']}: {e}")
            return False

# Sample Usage:
if __name__ == '__main__':
    # Sample Policies (loaded from a database or configuration file)
    sample_policies = [
        {
            'policy_id': 'policy1',
            'name': 'High value handphone purchase',
            'description': 'Flags transactions with multiple high-value handphone purchases within a short time',
            'rules': """transaction['list_of_items'][0]['item_name'] == 'handphone' and transaction['list_of_items'][0]['price'] > 5000000 and len(transaction['list_of_items']) >= 3"""
        },
        {
            'policy_id': 'policy2',
            'name': 'Multiple electronics gadget purchase',
            'description': 'Flags transactions with multiple electronics gadget purchases in a day',
            'rules': """len([item for item in transaction['list_of_items'] if item['item_name'] in ['handphone', 'electronics gadget']]) >= 5"""
        }
    ]

    # Sample Transaction Data
    sample_transaction = {
        'id_transaction': 'txn123',
        'id_user': 'user456',
        'list_of_items': [
            {'item_name': 'handphone', 'price': 6000000, 'quantity': 1},
            {'item_name': 'handphone', 'price': 5500000, 'quantity': 1},
            {'item_name': 'handphone', 'price': 5200000, 'quantity': 1},
            {'item_name': 'charger', 'price': 200000, 'quantity': 1}
        ]
    }

    # Initialize Policy Engine
    policy_engine = PolicyEngine(sample_policies)

    # Evaluate Transaction
    violated_policies = policy_engine.evaluate_transaction(sample_transaction)

    # Print Results
    if violated_policies:
        print(f"Transaction {sample_transaction['id_transaction']} violates policies: {violated_policies}")
    else:
        print(f"Transaction {sample_transaction['id_transaction']} does not violate any policies.")