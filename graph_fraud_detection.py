import networkx as nx
import json
from pymongo import MongoClient

class GraphFraudDetector:
    def __init__(self, mongo_uri, db_name, node_collection, link_collection):
        try:
            self.client = MongoClient(mongo_uri)
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            self.client = None
            self.db = None
            self.node_collection = None
            self.link_collection = None
            return

        self.db = self.client[db_name]
        self.node_collection = self.db[node_collection]
        self.link_collection = self.db[link_collection]
        self.graph = None

    def load_graph(self):
        """Loads the graph from MongoDB."""
        self.graph = nx.Graph()

        # Add nodes
        print("Loading nodes from MongoDB...")
        for node_data in self.node_collection.find():
            node_id = node_data['id_user']
            self.graph.add_node(node_id, **node_data)
            print(f"Added node: {node_id}")

        # Add edges
        print("Loading links from MongoDB...")
        for link_data in self.link_collection.find():
            source = link_data['source']
            target = link_data['target']
            weight = link_data['weight']
            self.graph.add_edge(source, target, weight=weight, type=link_data['type'], reason=link_data['reason'])

        print("Nodes in the graph:", self.graph.nodes())

    def get_neighbors(self, user_id, distance=3):
        """
        Finds all neighbors within a specified distance from a given user.
        Returns a set of user IDs.
        """
        if self.graph is None:
            self.load_graph()

        neighbors = set()
        for node in nx.descendants_at_distance(self.graph, user_id, distance):
            neighbors.add(node)
        return neighbors

    def calculate_proximity_score(self, user_id, fraud_user_ids):
         """
         Calculates a proximity score based on the distance to known fraudulent users.
         A higher score indicates a higher risk of fraud.
         """
         if self.graph is None:
             self.load_graph()

         total_proximity = 0
         for fraud_user in fraud_user_ids:
             try:
                 path_length = nx.shortest_path_length(self.graph, source=user_id, target=fraud_user)
                 proximity = 1.0 / path_length  # Closer is higher proximity
                 total_proximity += proximity
             except nx.NetworkXNoPath:
                 # No path to fraudulent user
                 pass

         return total_proximity

    def is_close_to_fraud(self, user_id, fraud_user_ids, distance=3):
        """
        Checks if a user is within a specified distance of any known fraudulent users.
        Returns True if the user is close to fraud, False otherwise.
        """
        if self.graph is None:
            self.load_graph()

        neighbors = self.get_neighbors(user_id, distance)
        return any(fraud_user in neighbors for fraud_user in fraud_user_ids)

# Sample Usage (replace with your MongoDB credentials and data)
if __name__ == '__main__':
    # MongoDB Connection Details
    mongo_uri = "mongodb://root:@localhost:27017/?authSource=admin"  # Replace with your MongoDB URI
    #mongo_uri = "mongodb://localhost:27017/" # Replace with your MongoDB URI
    db_name = "fraud_detection"
    node_collection = "users"
    link_collection = "links"

    # Initialize Graph Fraud Detector
    graph_detector = GraphFraudDetector(mongo_uri, db_name, node_collection, link_collection)

    # Sample Fraudulent User IDs (replace with actual IDs from your database)
    fraud_user_ids = ["user123", "user456"]

    # Sample User ID to Check
    user_id_to_check = "user789"

    # Check if the user is close to fraud
    is_close = graph_detector.is_close_to_fraud(user_id_to_check, fraud_user_ids)
    print(f"User {user_id_to_check} is close to fraud: {is_close}")

    # Calculate proximity score
    proximity_score = graph_detector.calculate_proximity_score(user_id_to_check, fraud_user_ids)
    print(f"Proximity score for user {user_id_to_check}: {proximity_score}")