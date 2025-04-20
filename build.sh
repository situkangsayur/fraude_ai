cd common
poetry install
poetry build
cd ..

cd rules_policy_engine
poetry install
poetry build
cd ..

cd neural_net_service
poetry install
poetry build
cd ..

cd llm_interface
poetry install
poetry build
cd ..

cd graph_service
poetry install
poetry build
cd ..

cd orchestrator
poetry install
poetry build
cd ..

cd dashboard
poetry install
poetry build
cd ..

