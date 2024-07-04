# Specify the function for the assistant to run
decompose_and_assign = {
    "name": "decompose_and_assign",
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

decomposability = {
    "name": "decomposability",
    "description": "Identify if a task is decomposable into a list of subtasks or not.",
    "parameters": {
        "type": "object",
        "properties": {
            "is_decomposable": {"type": "boolean"},
        },
        "required": ["is_decomposable"],
    },
}

# Get the response from the function
def get_tool_calls(run):
    if run.status == "failed":
        print(f"Warning: Run failed with error: {run.last_error}")
        return None

    if run.required_action is None:
        print("Warning: No required action in the run")
        return None

    return run.required_action.submit_tool_outputs.tool_calls