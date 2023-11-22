class Agent:

    def __init__(self, agent_list, client, model, id, name, description, tools_list=[], function_list=[], file_ids=[]):
        self.parent = agent_list
        self.client = client
        self.model = model
        self.id = id
        self.name = name
        self.description = description
        self.tools = tools_list
        self.functions = function_list
        self.file_ids = file_ids

        # Create list of tools/functions for the assistant
        assistant_tools = self.build_tools()

        # Create the agent's assistant
        self.assistant = self.create_assistant(
            name=self.name,
            instructions=self.description,
            tools=assistant_tools,
            file_ids=self.file_ids,
        )
        
        # Add self to parent
        self.parent.append(self)

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

    def __str__(self):
        return f"Agent ID: {self.id}, Name: {self.name}, Description: {self.description}"