import os
import sys
import json
import functions
import enums

from openai import OpenAI
from task import Task
from agent import Agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
ASSISTANT_MODEL = os.getenv('OPENAI_MODEL_LARGE')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH')

# Set the API key
client = OpenAI(api_key=OPENAI_API_KEY)

# Gets the function response from the run
def get_function_response(tool_call):
    name = tool_call.function.name
    function_response = json.loads(tool_call.function.arguments)
    return function_response

# Get the response from the function
def get_work_response(run):
    # Get the function response from the run
    tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
    function_response = get_function_response(tool_call)
    return tool_call, function_response

# Creates a list of tasks to keep track of agent activity
def create_task_list(tasks, subtasks):
    print()
    print("Creating list of task objects to keep track of agent activity...")
    for subtask in subtasks:
        id = subtask["subtask_id"]
        title = subtask["subtask_title"]
        description = subtask["subtask_description"]
        assigned_agent_id = subtask["assigned_agent_id"]
        dependent_upon = subtask.get("dependent_upon")
        if not dependent_upon:
            dependent_upon = "0"
        task = Task(client, id, title, description, assigned_agent_id, tasks, dependent_upon=dependent_upon)
        print(f'Created task "{task.title}"')
        tasks.append(task)
    return tasks 

# Decompose the objective into subtasks and agent assignments
def decompose_and_assign(tasks, agents, objective, decomposer):
    print()
    print("Creating subtasks and agents to meet requested objective...")
    title = "Decompose Objective"
    description = f"Decompose following objective into a list of subtasks, agents to complete the work, and assignments. The objective is '{objective}'.\n\nDon't prompt me if I want to proceed, just assume I do."
    decomposer_task = Task(client, 0, title, description, decomposer.id, tasks)
    print(f'Created task "{decomposer_task.title}"')
    tasks.append(decomposer_task)
    thread, run = decomposer_task.run(agents, LOG_FILE_PATH)

    # Get the function response from the decomposer task run    
    tool_call, function_response = get_work_response(run)

    # Thank the assistant for the decomposition and finish the task
    print("Finishing decomposition task...")    
    decomposer_task.finish(run, thread, tool_call, "Thank you. Looks good.")
    
    # Return subtasks and agent specifications
    return function_response["subtasks"], function_response["agents"]

# Get files to load into knowledge base
def get_knowledge_base(file_path, extension_filter=None):
    
    # Get list of files from specified directory
    #file_paths = utils.get_file_paths(file_path, extension_filter)
    file_paths = []
    
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

    # Create containers for tasks and agents
    tasks = []
    agents = []

    # Get objective from command line
    if len(sys.argv) > 1:
        objective = sys.argv[1]
        print(f"Objective: {objective}")
    else:
        print("You must enter an objective to proceed. Please try again.")
        exit
   
    # Specify decomposer agent parameters
    print()
    print("Creating decomposer agent...")
    agent_id = 0
    agent_name = "Objective Decomposer"
    agent_instructions = "You are an expert decomposer. You decompose objectives into subtasks, create agents, and assign the subtasks to the agents."
    agent_tools = [enums.Tool.RETRIEVAL]
    function_list = [functions.decompose_and_assign]
    file_ids = get_knowledge_base('./','.py')

    # Create agent and append to the list of agents
    decomposer = Agent(agents, client, ASSISTANT_MODEL, agent_id, agent_name, agent_instructions, agent_tools, function_list, file_ids)

    # Create task specifications and agent specifications (with assignments)
    subtasks, agent_specs = decompose_and_assign(tasks, agents, objective, decomposer)

    # Create tasks and add to task list
    tasks = create_task_list(tasks, subtasks)

    # Create agents and add to agent list
    print()
    print("Creating list of agents to execute tasks...")
    for agent_spec in agent_specs:
        # Get the agent info from the specification
        agent_id = agent_spec["agent_id"]
        agent_name = agent_spec["agent_name"]
        agent_instructions = agent_spec["agent_instructions"]
        agent_tools = [enums.Tool.RETRIEVAL, enums.Tool.CODE_INTERPRETER]
        function_list = [functions.research]

        # Create agent object and append to the list of agents
        Agent(agents, client, ASSISTANT_MODEL, agent_id, agent_name, agent_instructions, agent_tools, function_list, file_ids)

    # Loop through the tasks to complete them.
    print()
    print("Executing tasks...")
    for task in tasks:
        if not task.is_complete:
            thread, run = task.run(agents, LOG_FILE_PATH)

if __name__ == "__main__":
    main()