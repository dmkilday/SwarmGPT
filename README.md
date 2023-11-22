
# README for Swarm Project

## Introduction
Welcome to the Swarm Project! This is a Python-based program designed to handle complex tasks by dividing them into smaller subtasks and assigning them to different agents. The entry point for this program is `swarm.py`.

## Files Included
1. **`agent.py`**: Defines the `Agent` class, responsible for managing individual agents in the swarm, including their identification, description, and assigned tasks.
2. **`enums.py`**: Contains the `Tool` enumeration, defining various tools that can be used within the project.
3. **`functions.py`**: Includes the `decompose_and_assign` function, which decomposes objectives into subtasks and assigns them to agents.
4. **`research.py`**: Handles research-related functionalities, including API interactions for data retrieval (e.g., querying the arXiv API for research papers).
5. **`task.py`**: Defines the `Task` class, used for managing tasks, including their creation, assignment, and tracking.
6. **`utils.py`**: Provides utility functions such as `write_to_file`, useful for file operations.
7. **`swarm.py`**: The main script of the project, responsible for initializing and orchestrating the interaction between different components like tasks, agents, and research functions.
8. **`requirements.txt`**: Lists all the Python package dependencies for the project.
9. **`template.env`**: A template for setting up environment variables, including the OpenAI API key. Make a copy of this to .env and add your OpenAI API key.

## Installation Instructions
- Run python pip install -r requirements.txt
- Copy template.env to .env and add your OpenAI API key

## Usage Instructions
- Run python swarm.py and add a command line argument (in quotes) for the objective.