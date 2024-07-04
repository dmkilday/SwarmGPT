import os
import time
import utils
import threading

class Task:
    def __init__(self, client, log_file_path, id, title, description, agent_id, research_url, parent_task=None, dependent_upon=None, outcome=None):
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
        self.parent_task = parent_task

        print(f'Created task "{self.title}"')

        self.lock = threading.Lock()

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
        with self.lock:
            agent = self.get_agent(agents, self.assigned_agent)
            prompt = f"""
            Complete the following task:
            Task Title: {self.title}
            Task Description: {self.description}
            
            If the task requires writing code, please provide the complete, runnable code.
            For non-coding tasks, provide a detailed description or plan to accomplish the task.
            
            Begin your response now:
            """

            print(f'\n{agent.assistant.name} executing task #{self.id}: {self.title}...')
            thread, run = self.create_thread_and_run(prompt, agent.assistant.id)

            run = self.wait_on_run(run, thread, 5)

            task_outcome_message = self.get_latest_message(thread)
            self.outcome = task_outcome_message.content[0].text.value
            self.is_complete = True
            
            # Determine the appropriate file extension
            file_extension = self.determine_file_extension(self.outcome)
            
            # Create a sanitized filename
            sanitized_title = ''.join(c for c in self.title if c.isalnum() or c in (' ', '_')).rstrip()
            file_name = f'{thread.id}_{self.id}.{sanitized_title}{file_extension}'
            
            # Ensure the log directory exists
            os.makedirs(self.log_file_path, exist_ok=True)
            
            # Write the outcome to the file
            file_path = os.path.join(self.log_file_path, file_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.outcome)
            
            print(f'\nTask completed. Output written to {file_path}')
            print(f'\n{self.print(agents)}')
            
            return thread, run

    def determine_file_extension(self, content):
        # Check if the content looks like code
        code_indicators = ['import ', 'def ', 'class ', 'function', 'var ', 'let ', 'const ']
        if any(indicator in content[:500] for indicator in code_indicators):
            # Attempt to determine the language
            if 'import' in content[:500] and ('def' in content or 'class' in content):
                return '.py'
            elif 'function' in content[:500] or 'var' in content[:500] or 'let' in content[:500] or 'const' in content[:500]:
                return '.js'
            # Add more language checks as needed
            else:
                return '.txt'  # Default to .txt if language can't be determined
        else:
            return '.txt'