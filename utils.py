import os

def get_file_paths(directory_path, extension_filter=None):
    # Check if the provided path is indeed a directory
    if not os.path.isdir(directory_path):
        print(f"The provided path '{directory_path}' is not a directory.")
        return

    # Loop through each file in the directory
    file_paths = []
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        # Check if it's a file and not a directory
        if os.path.isfile(file_path):
            # If there's an extension filter, use it.
            if extension_filter:
                file_extension = os.path.splitext(filename)[1]
                if file_extension == extension_filter:
                    # Add the file to the list
                    print(f"Found file: {filename}")
                    file_paths.append(file_path)         
            else: # Otherwise, just add the file to the list
                print(f"Found file: {filename}")
                file_paths.append(file_path)                 
    
    return file_paths

# Get files to load into knowledge base
def get_knowledge_base(client, file_path, extension_filter=None):
    
    # Get list of files from specified directory
    file_paths = get_file_paths(file_path, extension_filter)
    
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