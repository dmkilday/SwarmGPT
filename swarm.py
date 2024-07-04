import os
import sys
import argparse
from openai import OpenAI
from agent import Agent
from research import Research
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed


# Load environment variables
load_dotenv()
ASSISTANT_MODEL = os.getenv('OPENAI_MODEL_LARGE')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', './logs')  # Default to './logs' if not set in .env
DATA_FILE_PATH = os.getenv('DATA_FILE_PATH')
RESEARCH_URL = os.getenv('RESEARCH_URL')

# Set the API key
client = OpenAI(api_key=OPENAI_API_KEY)

def create_top_agent(agents, client, ASSISTANT_MODEL, file_ids, research):
    agent_id = 0
    agent_name = "Helpful Agent"
    agent_instructions = "You are a helpful agent assisting me in completing the assigned task."
    agent_tools = ["retrieval"]  # Changed from enum to string
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
                       [],  # Empty list for function_list
                       file_ids)
    
    return decomposer

def get_args():
    if len(sys.argv) > 2:
        objective_title = sys.argv[1]
        objective_description = sys.argv[2]
        print(f"Objective: {objective_title}")
    else:
        print("You must enter an objective to proceed. Please try again.")
        sys.exit(1)

    return objective_title, objective_description 

def main():
    print("\nGathering knowledge base files...")
    research = Research(DATA_FILE_PATH, RESEARCH_URL)
    file_ids = []  # Implement get_knowledge_base() if needed
    agents = []

    print("\nCreating top agent...")    
    top_agent = create_top_agent(agents, client, ASSISTANT_MODEL, file_ids, research)

    print("\nAssigning task to top agent...")
    objective_title, objective_description = get_args()
    task_id = top_agent.receive_task_desc(objective_title, objective_description)

    print("\nInitiate work on the assigned task...") 
    with ThreadPoolExecutor(max_workers=5) as executor:  # Adjust max_workers as needed
        future = executor.submit(top_agent.work, task_id)
        try:
            future.result()  # This will re-raise any exception that occurred during execution
        except Exception as exc:
            print(f"Task execution generated an exception: {exc}")

    # Print contents of generated files
    print("\nGenerated outputs:")
    for filename in os.listdir(LOG_FILE_PATH):
        file_path = os.path.join(LOG_FILE_PATH, filename)
        if os.path.isfile(file_path):
            print(f"\nContents of {filename}:")
            with open(file_path, 'r', encoding='utf-8') as f:
                print(f.read())

if __name__ == "__main__":
    main()