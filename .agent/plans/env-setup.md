Environment Setup Plan
Goal Description
Set up the foundational infrastructure for hugging-tree using Docker for orchestration and Python for the application logic. This includes configuring Neo4j as the Graph DB and preparing the Python environment.

User Review Required
IMPORTANT

Please review the NEO4J_AUTH settings in docker-compose.yml and ensure they match your local security preferences. Default is neo4j/password.

Proposed Changes
Infrastructure
[NEW] 
docker-compose.yml
Define neo4j service (image: neo4j:5-community).
Define app service (build context: .).
Configure networks and volumes for persistence.
[NEW] 
Dockerfile
Base image: python:3.11-slim.
Install system dependencies (git).
Install python dependencies from requirements.txt.
Configuration
[NEW] 
requirements.txt
neo4j (driver)
chromadb
tree-sitter
tree-s