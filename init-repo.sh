#!/bin/bash
# Initialize the repository structure
mkdir -p {src/{rag,agents,guardrails,utils},notebooks,tests,localstack/sample-data,workshop-materials/{slides,handouts}}
touch src/__init__.py src/{rag,agents,guardrails,utils}/__init__.py tests/__init__.py

# Create initial Python files
touch src/rag/{pipeline,chunking,embeddings,retrieval}.py
touch src/agents/{sql_agent,reranking}.py
touch src/guardrails/safety.py
touch src/utils/{aws_client,cost_calculator}.py

# Create test files
touch tests/{test_rag,test_agents}.py

# Create notebook files
for i in {1..5}; do
    case $i in
        1) name="01_rag_basics.org" ;;
        2) name="02_advanced_rag.org" ;;
        3) name="03_text_to_sql.org" ;;
        4) name="04_fine_tuning.org" ;;
        5) name="05_cost_analysis.org" ;;
    esac
    touch notebooks/$name
done

echo "Repository structure created successfully!"
