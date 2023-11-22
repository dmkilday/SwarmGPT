# Specify the function for the assistant to run
decompose_and_assign = {
    "name": "decompose_objective_and_assign_tasks",
    "description": "Decomposes an objective into a list of subtasks. Then, create a list of agents to assign the subtasks to and make the assignments.",
    "parameters": {
        "type": "object",
        "properties": {
            "objective": {"type": "string"},
            "subtasks": {
                "type": "array",
                "description": "An array of subtasks, each with a unique numerical identifier, title, and description. If this subtask is dependent on another to start, populate the dependency.",
                "items": {
                    "type": "object",
                    "properties": {
                        "subtask_id": {"type": "integer"},
                        "subtask_title": {"type": "string"},
                        "subtask_description": {"type": "string",},
                        "assigned_agent_id": {"type": "integer"}, 
                        "dependent_upon": {"type": "integer"},                            
                    },
                    "required": ["subtask_id", "subtask_title", "subtask_description", "assigned_agent_id"],
                },
            },
            "agents": {
                "type": "array",
                "description": "An array of agents, each with a unique numerical ID, name, and instructions",
                "items": {
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "integer"},
                        "agent_name": {"type": "string"},
                        "agent_instructions": {"type": "string",},
                    },
                    "required": ["agent_id", "agent_name", "agent_instructions"],
                },
            },
            "assignments": {
                "type": "array",
                "description": "An array of agent-subtask assignments.",
                "items": {
                    "type": "object",
                    "properties": {
                        "subtask_id": {"type": "integer"},
                        "agent_id": {"type": "integer"},
                    },
                    "required": ["subtask_id", "agent_id"],
                },
            },                
        },
        "required": ["objective", "subtasks", "agents", "assignments"],
    },
}

research = {
    "name": "research",
    "description": "Create a search term based on the user request so they can download research from the internet.",
    "parameters": {
        "type": "object",
        "properties": {
            "original_search_request": {"type": "string"},
            "search_term": {"type": "string"},
        },
        "required": ["original_search_request", "search_term"],
    },
}