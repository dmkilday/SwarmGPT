import utils
import functions
import json
import enums

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

    # Creates the tools node for the assistant
    def build_tools(self):
        # Create list of tools for the assistant
        assistant_tools = []
        for tool in self.tools:
            assistant_tools.append({"type": tool.value})

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
        
        # Get the task based on task_id
        work_task = None
        for task in self.task_list:
            if task.id == task_id:
                work_task = task   
                break        
        
        # Call decompose_or_do(task)
        self.decompose_or_do(work_task)
        
        return work_task.outcome

    # Decompose and assign tasks
    def decompose_or_do(self, task):
        
        # Determine if tasks is decomposable and set it in the task
        self.set_decomposability(task)

        # Check if task is decomposable
        if task.is_decomposable:
            task_specs, agent_specs = self.get_subtask_agent_specs(task)
           
            #   Loop through task_specs and invoke delegation
            for task_spec in task_specs:

                # Get agent_spec assigned to task
                agent_spec = self.get_agent_spec(agent_specs, task_spec)
                self.delegate(agent_spec, task_spec)

        else: # task is atomic

            # Do the task
            self.do(task) 

    # Get the agent specification assigned to a task specification
    def get_agent_spec(self, agent_specs, task_spec):

        assigned_agent_spec = None

        # Loop through agent specifications
        for agent_spec in agent_specs:
            if agent_spec["agent_id"] == task_spec["assigned_agent_id"]:
                assigned_agent_spec = agent_spec
                break

        return assigned_agent_spec

    # Check if a task is decomposable
    def set_decomposability(self, task):

        # Call OpenAI API function to determine if task is decomposable
        # Create the decomposability task and associate with parent task
        title = "Get Decomposability"
        description = f"Determine if the task '{task.description}' is decomposable into subtasks. If the task is decomposable, then also call the decompose_and_assign function. If the task is not decomposable, just call the decomposable function. In either case, make sure you call the decomposable function."
        decomposability_task = Task(self.client, self.log_file_path, 0, title, description, self.id, self.research.search_url)
        task.decomposability_task = decomposability_task

        # Run the decompose task
        thread, run = decomposability_task.run(self.agent_list, self.log_file_path, self.data_file_path)

        # Get the tool calls from the decompose task run    
        tool_calls = functions.get_tool_calls(run)

        # Set a reference to tool_calls in the task for future use
        decomposability_task.tool_calls = tool_calls
        
        # Get the decomposability tool call
        decomposability_tool_call = None
        for tool_call in tool_calls:
            if tool_call.function.name == functions.decomposability["name"]:
                decomposability_tool_call = tool_call
                break

        # Confirm reciept of is_decomposable tool call
        decomposability_task.finish(run, thread, decomposability_tool_call, "Completed." )  

        # Set the decomposability (True or False) on the task
        decomposable_result = json.loads(decomposability_tool_call.function.arguments)
        task.is_decomposable = decomposable_result["is_decomposable"]

    # Identify delegate and assign task 
    def delegate(self, agent_spec, task_spec):
        
        # Create agent
        agent_id = agent_spec["agent_id"]
        agent_name = agent_spec["agent_name"]
        agent_instructions = agent_spec["agent_instructions"]
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
    
        # Assign task specification to agent
        task_id = agent.receive_task_spec(task_spec)

        # Initiate agent work on task
        agent.work(task_id)

    # Do the assigned task
    def do(self, task):

        # Run the decompose task
        thread, run = task.run(self.agent_list, self.log_file_path, self.data_file_path)

        # # Get the tool call and function response from the decomposer task run    
        # tool_calls = functions.get_tool_calls(run)
        # decompose_tool_call = tool_calls[0] # tool_calls[0] assumes we're closing the first tool call.
        # function_response = json.loads(decompose_tool_call.function.arguments)

    # Get the subtask and agent specifications
    def get_subtask_agent_specs(self, task):

        # Get the decomposability tool call
        decompose_tool_call = None
        decomposability_task = task.decomposability_task
        for tool_call in decomposability_task.tool_calls:
            if tool_call.function.name == functions.decompose_and_assign["name"]:
                decompose_tool_call = tool_call
                break 

        # Get the function response from the decompose tool call
        function_response = json.loads(decompose_tool_call.function.arguments)

        # Return subtasks and agent specifications
        return function_response["subtasks"], function_response["agents"]

    def __str__(self):
        return f"Agent ID: {self.id}, Name: {self.name}, Description: {self.description}"