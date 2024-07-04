import utils
import functions
import json
import enums
import threading

from concurrent.futures import ThreadPoolExecutor, as_completed
from task import Task

class Agent:
    def __init__(self, log_file_path, data_file_path, model, research_url, agent_list, client, id, name, description, research, tools_list=[], function_list=[], file_ids=[]):
        self.log_file_path = log_file_path
        self.data_file_path = data_file_path
        self.model = model
        self.research_url = research_url
        self.agent_list = agent_list
        self.client = client
        self.id = id
        self.name = name
        self.description = description
        self.research = research
        self.tools = tools_list
        self.functions = function_list
        self.file_ids = file_ids
        self.task_list = []

        # Create list of tools/functions for the assistant
        assistant_tools = self.build_tools()

        # Create the agent's assistant
        self.assistant = self.create_assistant(
            name=self.name,
            instructions=self.description,
            tools=assistant_tools,
            file_ids=self.file_ids,
        )
        
        # Add self to agent_list
        self.agent_list.append(self)

        # Show agent creation success
        print(f'Created agent "{self.name}"')

        self.lock = threading.Lock()

    def build_tools(self):
        # Create list of tools for the assistant
        assistant_tools = []
        for tool in self.tools:
            assistant_tools.append({"type": tool})

        # Add functions to list of assistant tools 
        if self.functions:
            for function in self.functions:
                assistant_tools.append({"type": "function", "function": function})

        return assistant_tools

    # Creates an assistant based on provided info
    def create_assistant(self, name, instructions, tools, file_ids):
        assistant = self.client.beta.assistants.create(
            name=name,
            instructions=instructions,
            tools=tools,
            model=self.model,
            file_ids=file_ids
        )

        return assistant

    # Refreshes the assistant's files
    def refresh_knowledge(self):

        # Get updated file list
        # Need to identify current list of file_ids, then only add to existing list of files.
        utils.get_knowledge_base(self.client, self.research.knowledge_path, None) # this currently gets all files

        # Update assistant
        self.client.beta.assistants[0].update(
            name=self.name,
            instructions=self.description,
            tools=self.build_tools(),
            model=self.model,
            file_ids=self.file_ids,            
        )

    # Receive a task with just task title and task description (for top level task)
    def receive_task_desc(self, task_title, task_description):
        
        # Create a new task and assign to agent
        new_task = Task(self.client, self.log_file_path, 0, task_title, task_description, self.id, self.research.search_url)
        self.task_list.append(new_task)

        return new_task.id
    
    # Receive a task specification to create task and assign to agent
    def receive_task_spec(self, task_spec):

        # Create a new task and add to agent's task list
        id = task_spec["subtask_id"]
        title = task_spec["subtask_title"]
        description = task_spec["subtask_description"]
        assigned_agent_id = task_spec["assigned_agent_id"]
        dependent_upon = task_spec.get("dependent_upon")
        if not dependent_upon:
            dependent_upon = "0"
        new_task = Task(self.client,
                    self.log_file_path,
                    id, 
                    title, 
                    description, 
                    assigned_agent_id, 
                    self.research_url, 
                    dependent_upon)

        self.task_list.append(new_task)

        return new_task.id
   
    # Have the agent start working on it's tasks
    def work(self, task_id):
        work_task = None
        with self.lock:
            for task in self.task_list:
                if task.id == task_id:
                    work_task = task
                    break

        if work_task is None:
            print(f"Error: No task found with id {task_id}")
            return None

        self.decompose_or_do(work_task)
        return work_task.outcome

    def decompose_or_do(self, task):
        self.set_decomposability(task)

        if task.is_decomposable:
            task_specs, agent_specs = self.get_subtask_agent_specs(task)
            print("Debug - task_specs:", task_specs)
            print("Debug - agent_specs:", agent_specs)

            if task_specs and agent_specs:
                with ThreadPoolExecutor(max_workers=len(task_specs)) as executor:
                    future_to_task = {executor.submit(self.execute_subtask, task_spec, agent_specs): task_spec for task_spec in task_specs}
                    for future in as_completed(future_to_task):
                        task_spec = future_to_task[future]
                        try:
                            future.result()
                        except Exception as exc:
                            print(f'{task_spec["subtask_id"]} generated an exception: {exc}')
            else:
                print("Warning: No subtasks or agents specified. Treating task as non-decomposable.")
                self.do(task)
        else:
            self.do(task)

        self.summarize_results(task)

    def execute_subtask(self, task_spec, agent_specs):
        agent_spec = self.get_agent_spec(agent_specs, task_spec)
        if agent_spec:
            subtask = self.create_subtask(task_spec)
            self.delegate(agent_spec, subtask)
        else:
            print(f"Warning: No agent found for task {task_spec.get('subtask_id', 'Unknown')}")

    def summarize_results(self, task):
        summary_prompt = f"""
        Summarize the results of the following task and its subtasks:
        Task: {task.title}
        Description: {task.description}
        
        If any subtasks produced code, compile the code into a complete, runnable program.
        If no code was produced, provide a detailed summary of the task outcomes.
        
        Begin your summary:
        """
        
        summary_task = Task(self.client, self.log_file_path, task.id + 1000, f"Summarize {task.title}", summary_prompt, self.id, self.research_url)
        self.do(summary_task)

    def create_subtask(self, task_spec, parent_task):
        return Task(self.client,
                    self.log_file_path,
                    task_spec['subtask_id'],
                    task_spec['subtask_title'],
                    task_spec['subtask_description'],
                    task_spec['assigned_agent_id'],
                    self.research_url,
                    parent_task=parent_task,
                    dependent_upon=task_spec.get('dependent_upon'))

    # Get the agent specification assigned to a task specification
    def get_agent_spec(self, agent_specs, task_spec):
        print("Debug - agent_specs:", agent_specs)
        print("Debug - task_spec:", task_spec)
        
        assigned_agent_spec = None
        for agent_spec in agent_specs:
            if agent_spec.get("agent_id") == task_spec.get("assigned_agent_id"):
                assigned_agent_spec = agent_spec
                break
        
        if assigned_agent_spec is None:
            print("Warning: No matching agent found for task.")
        
        return assigned_agent_spec

    # Check if a task is decomposable
    def set_decomposability(self, task):
        title = "Get Decomposability"
        description = f"Determine if the task '{task.description}' is decomposable into subtasks. If the task is decomposable, then also call the decompose_and_assign function. If the task is not decomposable, just call the decomposable function. In either case, make sure you call the decomposable function."
        decomposability_task = Task(self.client, self.log_file_path, 0, title, description, self.id, self.research.search_url)
        task.decomposability_task = decomposability_task

        thread, run = decomposability_task.run(self.agent_list, self.log_file_path, self.data_file_path)

        tool_calls = functions.get_tool_calls(run)

        if tool_calls is None:
            print(f"Warning: Run failed or no tool calls returned for task '{task.title}'")
            task.is_decomposable = False
            return

        decomposability_task.tool_calls = tool_calls
        
        decomposability_tool_call = None
        for tool_call in tool_calls:
            if tool_call.function.name == functions.decomposability["name"]:
                decomposability_tool_call = tool_call
                break

        if decomposability_tool_call is None:
            print(f"Warning: No decomposability function call found for task '{task.title}'")
            task.is_decomposable = False
            return

        decomposability_task.finish(run, thread, decomposability_tool_call, "Completed." )  

        try:
            decomposable_result = json.loads(decomposability_tool_call.function.arguments)
            task.is_decomposable = decomposable_result.get("is_decomposable", False)
        except json.JSONDecodeError:
            print(f"Error: Failed to parse decomposability result for task '{task.title}'")
            task.is_decomposable = False

    # Identify delegate and assign task 
    def delegate(self, agent_spec, task_spec):
        agent_id = agent_spec.get("agent_id")
        agent_name = agent_spec.get("agent_name")
        agent_instructions = agent_spec.get("agent_instructions", f"Perform the task: {task_spec.get('subtask_description', 'No description provided')}")

        agent_tools = [enums.Tool.RETRIEVAL, enums.Tool.CODE_INTERPRETER]
        function_list = [functions.research, functions.decomposability, functions.decompose_and_assign]
        
        agent = Agent(self.log_file_path, 
                    self.data_file_path, 
                    self.model, 
                    self.research_url, 
                    self.agent_list, 
                    self.client, 
                    agent_id, 
                    agent_name, 
                    agent_instructions, 
                    self.research, 
                    agent_tools, 
                    function_list, 
                    self.file_ids)

        task_id = agent.receive_task_spec(task_spec)
        agent.work(task_id)

    # Do the assigned task
    def do(self, task):
        prompt = f"""
        Complete the following task:
        Task Title: {task.title}
        Task Description: {task.description}

        If this task requires writing code:
        1. Provide the complete, runnable code.
        2. Include all necessary imports.
        3. Ensure the code is self-contained and can be executed as-is.
        4. Use appropriate libraries or frameworks if needed (e.g., tkinter for GUIs in Python).

        If this task doesn't require code:
        Provide a detailed plan or description to accomplish the task.

        Begin your response now:
        """

        task.description = prompt
        thread, run = task.run(self.agent_list, self.log_file_path, self.data_file_path)

    # Get the subtask and agent specifications
    def get_subtask_agent_specs(self, task):
        decompose_tool_call = None
        decomposability_task = task.decomposability_task
        for tool_call in decomposability_task.tool_calls:
            if tool_call.function.name == functions.decompose_and_assign["name"]:
                decompose_tool_call = tool_call
                break 

        if decompose_tool_call is None:
            print("Warning: No decompose_and_assign function call found.")
            return [], []

        try:
            function_response = json.loads(decompose_tool_call.function.arguments)
            subtasks = function_response.get("subtasks", [])
            agents = function_response.get("agents", [])
            
            # Ensure each agent has instructions
            for agent in agents:
                if "agent_instructions" not in agent:
                    agent["agent_instructions"] = f"Perform tasks as assigned for {agent.get('agent_name', 'Unknown Agent')}"
            
            return subtasks, agents
        except json.JSONDecodeError:
            print("Error: Failed to parse function arguments as JSON.")
            return [], []

    def __str__(self):
        return f"Agent ID: {self.id}, Name: {self.name}, Description: {self.description}"