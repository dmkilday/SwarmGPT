import os

def write_to_file(file_path, content):
    """
    Writes the given content to a file at the specified file_path.
    
    :param file_path: str, the path to the file where the content will be written.
    :param content: str, the content to write to the file.
    """
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        print(f"Content successfully written to {file_path}")
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")

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