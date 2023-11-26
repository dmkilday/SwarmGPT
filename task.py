import time
import utils

class Task:
    def __init__(self, client, log_file_path, id, title, description, agent_id, research_url, dependent_upon=None, outcome=None):
        self.log_file_path = log_file_path
        self.client = client
        self.id = id
        self.title = title
        self.description = description
        self.assigned_agent = agent_id 
        self.dependent_upon = dependent_upon
        self.research_url = research_url
        self.outcome = outcome
        self.decomposability_task = None
        self.tool_calls = None
        self.is_decomposable = None
        self.is_complete = False

        print(f'Created task "{self.title}"')

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

    # Gets an agent from the list of agents by agent ID
    def get_agent(self, agents, agent_id):

        # Get the assistant from the agent
        for agent in agents:
            if agent.id == agent_id:
                return agent

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

    # Completes a task
    def finish(self, run, thread, tool_call, tool_response):
        # Build tool outputs
        tool_outputs = []
        for tc in self.tool_calls:
            if (tc.id == tool_call.id):
                tool_outputs.append({"tool_call_id": tc.id, "output": tool_response,})
            else:
                # Set other tool calls to pending
                tool_outputs.append({"tool_call_id": tc.id, "output": "Pending...",})

        # Submit the tool outputs to the assistant
        run = self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread.id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )

    def print(self, agent_list):
        # Get the name of the agent
        agent_name = ""
        for agent in agent_list:
            if agent.id == self.assigned_agent:
                agent_name = agent.name
                break

        return f"\n\nTask ID: {self.id}, Title: {self.title}, Description: {self.description}, Assigned Agent: {agent_name}, Dependent Upon: {self.dependent_upon}\n\nTask Outcome:\n{self.outcome}"

    def run(self, agents, log_file_path, knowledge_file_path):
        # Get the assigned agent for this task 
        agent = self.get_agent(agents, self.assigned_agent)
        prompt = ""

        # Aggregate previously completed work
        #previous_work = self.aggregate_work(self.parent, agents)

        # List out the tasks and show where we are
        prompt = ""
        if self.id > 0:
            prompt = "Here is the overall plan for the entire team:"
            for task in self.parent:
                # Ignore the first task (decomposition)
                if task.id > 0:
                    task_text = f"\n{task.id}. {task.title}"
                    if task.id == self.id:
                        task_text = task_text + " <-- YOU ARE HERE"
                    prompt = prompt + task_text

        # Create prompt for task
        prompt = f"\n\nComplete the following task in a single request.\n\nTask Title: {self.title}\n\nTask Description: {self.description}\n\nIf there is code to be written, output the actual python code requested.\n\nAssuming I want you to proceed, do not prompt me for any further information."
        # if previous_work != "":
        #     prompt = prompt + f"\n\nPrevious work completed: {previous_work}. Taking into account the previous work completed, complete the following task in a single request.\n\nTask Title: {self.title}\n\nTask Description: {self.description}\n\nIf there is code to be written, output the actual python code requested.\n\nAssuming I want you to proceed, do not prompt me for any further information."
        # else:
        #     prompt = prompt + f"\n\nComplete the following task in a single request.\n\nTask Title: {self.title}\n\nTask Description: {self.description}\n\nIf there is code to be written, output the actual python code requested.\n\nAssuming I want you to proceed, do not prompt me for any further information."
        
        # Run the thread to execute the task
        print()
        print(f'{agent.assistant.name} executing task #{self.id}: {self.title}...')
        thread, run = self.create_thread_and_run(prompt, agent.assistant.id)

        # Wait for run & print tasks outcome
        run = self.wait_on_run(run, thread, 5)

        # # Check if there was a function called
        # tool_calls = functions.get_tool_calls(run)
        # if tool_calls:
        #     responses = []
        #     for tool_call in tool_calls:
        #         function_response = json.loads(tool_call.function.arguments)
        #         # If research was called, then perform the research task
        #         if tool_call.function.name == 'research':
        #             # 1. search/download research.
        #             search_term = function_response["search_term"]
        #             search_tree = agent.research.search(search_term, 5)
        #             agent.research.download(search_tree)

        #             # 2. load research into assistant knowledge

        #             # 3. complete task from (original_search_request)
        #             # Submit the message to the assistant on the thread
                    
        #             response = f"Parse the attached files, and {self.description} - using search term '{search_term}'. If there are no files available, or there is no relavant information in the files provided, do your best to respond with information from your own memory."
        #             responses.append(response)
        #         else: # If not research, then assume this was the decompose task
        #             responses.append("Looks good. Thank you.")
            
        #     # Finish the run
        #     self.finish(run, thread, tool_calls, responses)
        #     run = self.wait_on_run(run, thread, 5)

        # Get task outcome and write to file
        task_outcome_message = self.get_latest_message(thread)
        self.outcome = task_outcome_message.content[0].text.value
        self.is_complete = True # Set the task to complete
        file_name = (f'{thread.id}_{self.id}.{self.title}.txt').replace(' ', '_')
        utils.write_to_file(f'{self.log_file_path}/{file_name}', self.outcome)
        print()
        print(f'{self.print(agents)}')

        return thread, run