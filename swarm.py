import os
import sys
import json
import enums
import utils
import functions

from openai import OpenAI
from task import Task
from agent import Agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
ASSISTANT_MODEL = os.getenv('OPENAI_MODEL_LARGE')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH')
DATA_FILE_PATH = os.getenv('DATA_FILE_PATH')

# Set the API key
client = OpenAI(api_key=OPENAI_API_KEY)

# Creates an agent to decompose an objective into subtasks
def create_decomposer_agent(agents, client, ASSISTANT_MODEL, file_ids):
    agent_id = 0
    agent_name = "Objective Decomposer"
    agent_instructions = "You are an expert decomposer. You decompose objectives into subtasks, create agents, and assign the subtasks to the agents."
    agent_tools = [enums.Tool.RETRIEVAL]
    function_list = [functions.decompose_and_assign]
    decomposer = Agent(agents, client, ASSISTANT_MODEL, agent_id, agent_name, agent_instructions, agent_tools, function_list, file_ids)
    return decomposer

# Creates a list of tasks to keep track of agent activity
def create_task_list(tasks, subtasks):
    for subtask in subtasks:
        id = subtask["subtask_id"]
        title = subtask["subtask_title"]
        description = subtask["subtask_description"]
        assigned_agent_id = subtask["assigned_agent_id"]
        dependent_upon = subtask.get("dependent_upon")
        if not dependent_upon:
            dependent_upon = "0"
        Task(tasks, client, id, title, description, assigned_agent_id, dependent_upon=dependent_upon)
    return tasks

# Creates a list of agents to execute the tasks
def create_agent_list(agents, agent_specs, file_ids):
    for agent_spec in agent_specs:
        # Get the agent info from the specification
        agent_id = agent_spec["agent_id"]
        agent_name = agent_spec["agent_name"]
        agent_instructions = agent_spec["agent_instructions"]
        agent_tools = [enums.Tool.RETRIEVAL, enums.Tool.CODE_INTERPRETER]
        function_list = [functions.research]

        # Create agent object and append to the list of agents
        Agent(agents, client, ASSISTANT_MODEL, agent_id, agent_name, agent_instructions, agent_tools, function_list, file_ids)
    return agents

# Decompose the objective into subtasks and agent assignments
def decompose_and_assign(tasks, agents, objective, decomposer):
    # Create the decompose task 
    title = "Decompose Objective"
    description = f"Decompose following objective into a list of subtasks, agents to complete the work, and assignments. The objective is '{objective}'.\n\nDon't prompt me if I want to proceed, just assume I do."
    decompose_task = Task(tasks, client, 0, title, description, decomposer.id)

    # Run the decompose task
    thread, run = decompose_task.run(agents, LOG_FILE_PATH)

    # Get the tool call and function response from the decomposer task run    
    tool_calls = functions.get_tool_calls(run)
    decompose_tool_call = tool_calls[0] # tool_calls[0] assumes we're closing the first tool call.
    function_response = json.loads(decompose_tool_call.function.arguments)
    
    # Return subtasks and agent specifications
    return function_response["subtasks"], function_response["agents"]

# Get files to load into knowledge base
def get_knowledge_base(file_path, extension_filter=None):
    
    # Get list of files from specified directory
    #file_paths = [] # temporarily excluding load files
    file_paths = utils.get_file_paths(file_path, extension_filter)
    
    # Create Assistant API client files and add to list
    file_ids = []
    for file_path in file_paths:
        file = client.files.create(
        file=open(
            file_path,
            "rb",
        ),
        purpose="assistants",)
        file_ids.append(file.id)

    return file_ids

# Main entry point of the program
def main():

    # Get objective from command line
    if len(sys.argv) > 1:
        objective = sys.argv[1]
        print(f"Objective: {objective}")
    else:
        print("You must enter an objective to proceed. Please try again.")
        exit

    # Get knowledge base files & create empty containers
    print("\nGathering knowledge base files...") 
    file_ids = get_knowledge_base(DATA_FILE_PATH, None)
    tasks = []
    agents = []

    # Create decomposer agent
    print("\nCreating decomposer agent...")    
    decomposer = create_decomposer_agent(agents, client, ASSISTANT_MODEL, file_ids)

    # Decompose objective into task specifications and agent specifications (with assignments)
    print("\nDecomposing objective into task and agent specifications...") 
    task_specs, agent_specs = decompose_and_assign(tasks, agents, objective, decomposer)

    # Create tasks
    print("\nCreating tasks from list of task specifications...") 
    tasks = create_task_list(tasks, task_specs)

    # Create agents
    print("\nCreating agents from list of agent specifications...") 
    agents = create_agent_list(agents, agent_specs, file_ids)

    # Loop through tasks to have assigned agents execute
    print("\nExecuting tasks...")
    for task in tasks:
        if not task.is_complete:
            thread, run = task.run(agents, LOG_FILE_PATH)

if __name__ == "__main__":
    main()