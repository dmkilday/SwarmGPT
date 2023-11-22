import time
import json
import utils

class Task:
    def __init__(self, client, id, title, description, agent_id, parent, dependent_upon=None, outcome=None):
        self.client = client
        self.parent = parent
        self.id = id
        self.title = title
        self.description = description
        self.assigned_agent = agent_id 
        self.dependent_upon = dependent_upon
        self.outcome = outcome
        self.is_complete = False

    # Add message to the assistant thread and create a run
    def submit_message(self, assistant_id, thread, user_message):
        # Added messages to the thread
        self.client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=user_message
        )

        # Run the thread and return the run object
        return self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id,
        )
    
    # Create assistant thread and run it
    def create_thread_and_run(self, user_input, assistant_id):
        # Create the thread
        thread = self.client.beta.threads.create()

        # Submit the message to the assistant on the thread
        run =  self.submit_message(assistant_id, thread, user_input)
        return thread, run

    # Waiting in a loop
    def wait_on_run(self, run, thread, wait_duration):
        # Keep looping until the thread has completed its run
        while run.status == "queued" or run.status == "in_progress":
            # Get run status of thread
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            )
            print(f'Run Status: {run.status}')

            # Wait for 1/2 second
            time.sleep(wait_duration)
        return run

    # Gets an assistant from a list of assistants by agent ID
    def get_assistant(self, agents, agent_id):

        # Get the assistant from the agent
        for agent in agents:
            if agent.id == agent_id:
                assistant = agent.assistant
                return assistant

    # Aggregates all work done from the task list
    def aggregate_work(self, tasks, agents):
        work = ""
        for task in tasks:
            # Only grab completed tasks after the first one
            # Note: the first task is the decomposition task, so 
            #       it's not relevant to the work done so far.
            if task.is_complete & task.id > 0:
                work = f'{work}\n\n{task.print(agents)}'
        
        return work

    # Get the list of messages from the thread
    def get_messages(self, thread):
        return self.client.beta.threads.messages.list(thread_id=thread.id, order="asc")

    # Get the latest message in the message thread
    def get_latest_message(self, thread):
        # Get messages from the thread
        messages = self.get_messages(thread)

        # Get the last message
        latest_message = messages.data[len(messages.data)-1]

        return latest_message

    # Gets the function response from the run
    def get_function_response(tool_call):
        name = tool_call.function.name
        function_response = json.loads(tool_call.function.arguments)
        return function_response

    # Get the response from the function
    def get_work_response(self, run):
        # Get the function response from the run
        tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
        function_response = self.get_function_response(tool_call)
        return tool_call, function_response

    # Completes a task
    def finish(self, run, thread, tool_call, output_text):
        run = self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread.id,
            run_id=run.id,
            tool_outputs=[
                {
                    # Specify the tool to call and the final user response
                    # (this can be a second call back to the assistant for more info)
                    "tool_call_id": tool_call.id,
                    "output": output_text,
                }
            ],
        )

    def print(self, agent_list):
        # Get the name of the agent
        agent_name = ""
        for agent in agent_list:
            if agent.id == self.assigned_agent:
                agent_name = agent.name
                break

        return f"\n\nTask ID: {self.id}, Title: {self.title}, Description: {self.description}, Assigned Agent: {agent_name}, Dependent Upon: {self.dependent_upon}\n\nTask Outcome:\n{self.outcome}"

    def run(self, agents, log_file_path):
        agent_id = self.assigned_agent
        assistant = self.get_assistant(agents, agent_id)
        prompt = ""

        # Aggregate previously completed work
        previous_work = self.aggregate_work(self.parent, agents)

        # List out the tasks and show where we are
        prompt = ""
        if self.id > 0:
            prompt = f"Here is the overall plan for the entire team:"
            for task in self.parent:
                # Ignore the first task (decomposition)
                if task.id > 0:
                    task_text = f"\n{task.id}. {task.title}"
                    if task.id == self.id:
                        task_text = task_text + " <-- YOU ARE HERE"
                    prompt = prompt + task_text

        # Create prompt for task
        if previous_work != "":
            prompt = prompt + f"\n\nPrevious work completed: {previous_work}. Taking into account the previous work completed, complete the following task in a single request.\n\nTask Title: {self.title}\n\nTask Description: {self.description}\n\nIf there is code to be written, output the actual python code requested.\n\nAssuming I want you to proceed, do not prompt me for any further information."
        else:
            prompt = prompt + f"\n\nComplete the following task in a single request.\n\nTask Title: {self.title}\n\nTask Description: {self.description}\n\nIf there is code to be written, output the actual python code requested.\n\nAssuming I want you to proceed, do not prompt me for any further information."
        
        # Run the thread to execute the task
        print()
        print(f'{assistant.name} executing task #{self.id}: {self.title}...')
        thread, run = self.create_thread_and_run(prompt, assistant.id)

        # Wait for run & print tasks outcome
        run = self.wait_on_run(run, thread, 5)

        # Check if there was a function called
        # Get the function response from the decomposer task run    
        #tool_call, function_response = get_work_response(run)

        task_outcome_message = self.get_latest_message(thread)
        self.outcome = task_outcome_message.content[0].text.value
        self.is_complete = True # Set the task to complete
        file_name = (f'{thread.id}_{self.id}.{self.title}.txt').replace(' ', '_')
        utils.write_to_file(f'{log_file_path}/{file_name}', self.outcome)
        print()
        print(f'{self.print(agents)}')

        return thread, run