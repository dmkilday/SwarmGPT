import os
import sys
import enums
import utils
import functions

from openai import OpenAI
from agent import Agent
from research import Research
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
ASSISTANT_MODEL = os.getenv('OPENAI_MODEL_LARGE')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH')
DATA_FILE_PATH = os.getenv('DATA_FILE_PATH')
RESEARCH_URL = os.getenv('RESEARCH_URL')

# Set the API key
client = OpenAI(api_key=OPENAI_API_KEY)

# Creates an agent to decompose an objective into subtasks
def create_top_agent(agents, client, ASSISTANT_MODEL, file_ids, research):
    agent_id = 0
    agent_name = "Objective Decomposer"
    agent_instructions = "You are an expert decomposer. You decompose objectives into subtasks, create agents, and assign the subtasks to the agents."
    agent_tools = [enums.Tool.RETRIEVAL]
    function_list = [functions.decompose_and_assign]
    decomposer = Agent(LOG_FILE_PATH, 
                       DATA_FILE_PATH,
                       ASSISTANT_MODEL,
                       RESEARCH_URL,
                       agents, 
                       client, 
                       agent_id, 
                       agent_name, 
                       agent_instructions, 
                       research, 
                       agent_tools, 
                       function_list, 
                       file_ids)
    
    return decomposer

# Main entry point of the program
def main():

    # Get objective from command line
    if len(sys.argv) > 2:
        objective_title = sys.argv[1]
        objective_description = sys.argv[2]
        print(f"Objective: {objective_title}")
    else:
        print("You must enter an objective to proceed. Please try again.")
        exit

    # Get knowledge base files & create empty containers
    print("\nGathering knowledge base files...")
    research = Research(DATA_FILE_PATH, RESEARCH_URL)
    file_ids = utils.get_knowledge_base(client, DATA_FILE_PATH, ".pdf")
    agents = []

    # Create decomposer agent
    print("\nCreating top agent...")    
    top_agent = create_top_agent(agents, client, ASSISTANT_MODEL, file_ids, research)

    # Assign objective to agent
    print("\nAssigning task to top agent...")       
    task_id = top_agent.assign(objective_title, objective_description)

    # Have agent start work on the task assigned
    print("\nInitiate work on the assigned task...") 
    top_agent.work(task_id)

if __name__ == "__main__":
    main()